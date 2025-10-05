"""Deployment orchestrator for Cloud Run deployments"""

import os
import asyncio
import subprocess
import json
import shutil
import re
import random
import string
from pathlib import Path
from typing import Dict, List, Optional

from clouds.gcp.cloudrun import CloudRunDeployer


class DeploymentOrchestrator:
    def __init__(self):
        self.cloudrun_deployer = CloudRunDeployer()
        self.outputs_dir = Path("outputs")
        self.outputs_dir.mkdir(exist_ok=True)
    
    async def deploy_to_cloudrun(self, config: Dict, deployment_plan: Dict) -> Dict:
        """Orchestrate Cloud Run deployment"""
        try:
            # Validate authentication first
            auth_result = await self.validate_gcp_authentication()
            if not auth_result['success']:
                return {'success': False, 'error': f"Authentication failed: {auth_result['error']}"}
            
            # Step 1: Enable required APIs first
            print("🔧 Enabling required GCP services...")
            await self._enable_required_apis()
            
            # Step 2: Completely replace with corrected Terraform configuration
            print("🔄 Applying comprehensive Terraform configuration...")
            await self._create_comprehensive_terraform_config(config, deployment_plan)
            
            # Step 3: Provision infrastructure
            print("🚀 Provisioning cloud resources...")
            infra_result = await self.provision_infrastructure_real(deployment_plan, config)
            
            if not infra_result['success']:
                return infra_result
            
            # Step 4: Build and deploy services
            print("🐳 Building and deploying containers...")
            services_result = await self.deploy_applications_real(deployment_plan, config)
            
            return {
                'success': True,
                'services': services_result.get('services', []),
                'database_connection': infra_result.get('database_connection'),
                'urls': services_result.get('urls', {}),
                'service_urls': infra_result.get('service_urls', {})
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _enable_required_apis(self):
        """Enable required GCP APIs before Terraform runs"""
        project_id = self._get_gcp_project()
        required_apis = [
            "compute.googleapis.com",
            "sqladmin.googleapis.com",
            "run.googleapis.com", 
            "cloudbuild.googleapis.com",
            "artifactregistry.googleapis.com",
            "servicenetworking.googleapis.com",
            "vpcaccess.googleapis.com",
            "iam.googleapis.com"
        ]
        
        print("   🔧 Enabling GCP APIs...")
        for api in required_apis:
            try:
                result = subprocess.run([
                    "gcloud", "services", "enable", api,
                    f"--project={project_id}",
                    "--quiet"
                ], capture_output=True, text=True, check=True)
                print(f"   ✅ Enabled {api}")
            except subprocess.CalledProcessError as e:
                # If API is already enabled, that's fine
                if "already enabled" in e.stderr:
                    print(f"   ✅ {api} already enabled")
                else:
                    print(f"   ⚠️  Could not enable {api}: {e.stderr}")
    
    def _generate_random_suffix(self, length=6):
        """Generate a random suffix for resource names to avoid conflicts"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    async def _create_comprehensive_terraform_config(self, config: Dict, deployment_plan: Dict):
        """Create a completely corrected Terraform configuration"""
        terraform_dir = self.cloudrun_deployer.terraform_dir
        main_tf_path = terraform_dir / "main.tf"
        versions_tf_path = terraform_dir / "versions.tf"
        
        project_id = self._get_gcp_project()
        region = config.get('region', 'us-central1')
        project_name = config.get('project_name', 'my-project')
        database_tier = config.get('database_tier', 'db-f1-micro')
        
        # Generate random suffix to avoid resource conflicts
        random_suffix = self._generate_random_suffix()
        
        # Get service names from deployment plan
        service_names = [service['name'] for service in deployment_plan.get('services', [])]
        if not service_names:
            service_names = ["api", "web", "worker"]
        
        # Create service configurations for main.tf
        service_configs = []
        for service_name in service_names:
            tf_service_name = service_name.replace('-', '_')
            service_config = f'''
resource "google_cloud_run_service" "{tf_service_name}" {{
  name     = "{service_name}-{random_suffix}"
  location = "{region}"

  template {{
    spec {{
      containers {{
        image = "gcr.io/cloudrun/hello:latest"
        
        env {{
          name  = "DATABASE_URL"
          value = "Host=${{google_sql_database_instance.postgres.private_ip_address}};Database=${{google_sql_database.database.name}};Username=${{google_sql_user.users.name}};Password=${{random_password.db_password.result}};SSL Mode=Require;Trust Server Certificate=true"
        }}
        
        ports {{
          container_port = 8080
        }}
        
        resources {{
          limits = {{
            memory = "512Mi"
            cpu    = "1000m"
          }}
        }}
      }}
      
      container_concurrency = 80
      timeout_seconds       = 300
    }}
  }}

  traffic {{
    percent         = 100
    latest_revision = true
  }}

  depends_on = [
    google_sql_database_instance.postgres,
    google_sql_database.database,
    google_sql_user.users
  ]
}}

resource "google_cloud_run_service_iam_member" "{tf_service_name}_public" {{
  service  = google_cloud_run_service.{tf_service_name}.name
  location = google_cloud_run_service.{tf_service_name}.location
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [google_cloud_run_service.{tf_service_name}]
}}'''
            service_configs.append(service_config)
        
        services_block = '\n'.join(service_configs)
        
        # Create outputs for services
        service_outputs = []
        for service_name in service_names:
            tf_service_name = service_name.replace('-', '_')
            service_outputs.append(f'    {tf_service_name} = google_cloud_run_service.{tf_service_name}.status[0].url')
        
        outputs_block = ',\n'.join(service_outputs)
        
        # Generate main.tf (resources only)
        main_tf_content = f'''# Main Terraform configuration for Cloud Run
# Terraform and providers configuration is in versions.tf

# Data source for default network
data "google_compute_network" "default" {{
  name = "default"
  project = var.project_id
}}

# Enable required services
resource "google_project_service" "services" {{
  for_each = toset([
    "servicenetworking.googleapis.com",
    "sqladmin.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com"
  ])

  service = each.key
  disable_on_destroy = false
}}

# Private VPC connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {{
  name          = "{project_name}-private-ip-{random_suffix}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = data.google_compute_network.default.id

  depends_on = [google_project_service.services]
}}

resource "google_service_networking_connection" "private_vpc_connection" {{
  network                 = data.google_compute_network.default.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]

  depends_on = [
    google_project_service.services,
    google_compute_global_address.private_ip_address
  ]
}}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {{
  name             = "{project_name}-postgres-{random_suffix}"
  database_version = "POSTGRES_14"
  region           = "{region}"

  settings {{
    tier = "{database_tier}"
    availability_type = "ZONAL"
    
    ip_configuration {{
      ipv4_enabled    = false
      private_network = data.google_compute_network.default.id
      require_ssl     = true
    }}

    backup_configuration {{
      enabled = true
    }}

    disk_size = 20
    disk_type = "PD_SSD"
  }}

  deletion_protection = false

  depends_on = [
    google_project_service.services,
    google_service_networking_connection.private_vpc_connection
  ]
}}

resource "google_sql_database" "database" {{
  name     = "{project_name}_db_{random_suffix}"
  instance = google_sql_database_instance.postgres.name
}}

resource "google_sql_user" "users" {{
  name     = "{project_name}_user_{random_suffix}"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}}

resource "random_password" "db_password" {{
  length  = 16
  special = false
}}

resource "google_artifact_registry_repository" "repo" {{
  location      = "{region}"
  repository_id = "{project_name}-repo-{random_suffix}"
  description   = "Docker repository for {project_name}"
  format        = "DOCKER"

  depends_on = [google_project_service.services]
}}

# Cloud Run Services
{services_block}

output "database_connection" {{
  value = google_sql_database_instance.postgres.connection_name
}}

output "database_private_ip" {{
  value = google_sql_database_instance.postgres.private_ip_address
}}

output "service_urls" {{
  value = {{
{outputs_block}
  }}
}}

output "artifact_registry_url" {{
  value = google_artifact_registry_repository.repo.repository_id
}}

output "random_suffix" {{
  value = "{random_suffix}"
}}
'''
        
        # Generate versions.tf (terraform block and providers only)
        versions_tf_content = '''terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random" 
      version = "~> 3.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "random" {}
'''
        
        # Generate variables.tf
        variables_tf_content = f'''
variable "project_id" {{
  description = "The GCP project ID"
  type        = string
  default     = "{project_id}"
}}

variable "project_name" {{
  description = "The name prefix for resources"
  type        = string
  default     = "{project_name}"
}}

variable "region" {{
  description = "The GCP region"
  type        = string
  default     = "{region}"
}}

variable "database_tier" {{
  description = "The Cloud SQL instance tier"
  type        = string
  default     = "{database_tier}"
}}
'''
        
        # Ensure the directory exists
        terraform_dir.mkdir(parents=True, exist_ok=True)
        
        # Write all files
        with open(main_tf_path, 'w') as f:
            f.write(main_tf_content)
        
        with open(versions_tf_path, 'w') as f:
            f.write(versions_tf_content)
            
        with open(terraform_dir / "variables.tf", 'w') as f:
            f.write(variables_tf_content)
        
        print("   ✅ Created comprehensive Terraform configuration")
        print(f"   📍 Project: {project_id}")
        print(f"   📍 Region: {region}") 
        print(f"   📍 Services: {', '.join(service_names)}")
        print(f"   📍 Random suffix: {random_suffix} (to avoid conflicts)")
    
    async def _check_cloud_quotas(self, project_id: str) -> Dict:
        """Check if we have sufficient quotas for deployment"""
        print("   📊 Checking cloud quotas...")
        
        try:
            # Check if necessary APIs are enabled
            required_services = [
                "compute.googleapis.com",
                "sqladmin.googleapis.com", 
                "run.googleapis.com",
                "cloudbuild.googleapis.com",
                "artifactregistry.googleapis.com",
                "servicenetworking.googleapis.com"
            ]
            
            enabled_services = []
            for service in required_services:
                try:
                    result = subprocess.run([
                        "gcloud", "services", "list", 
                        f"--project={project_id}",
                        f"--filter=name:{service}",
                        "--format=value(name)"
                    ], capture_output=True, text=True, check=True)
                    if result.stdout.strip():
                        enabled_services.append(service)
                except:
                    pass
            
            print(f"   ✅ Enabled services: {len(enabled_services)}/{len(required_services)}")
            
            return {
                'success': True,
                'enabled_services': enabled_services,
                'required_services': required_services
            }
            
        except Exception as e:
            print(f"   ⚠️  Quota check warning: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Autonomous deployment methods
    async def generate_infrastructure_autonomous(self, deployment_plan: Dict, config: Dict = None):
        """Generate infrastructure code for autonomous deployment"""
        print("📁 Generating infrastructure autonomously...")
        if config is None:
            config = {
                'project_name': 'autonomous-project',
                'region': 'us-central1'
            }
        await self._create_comprehensive_terraform_config(config, deployment_plan)
    
    async def provision_autonomous(self, deployment_plan: Dict, config: Dict = None) -> Dict:
        """Provision infrastructure autonomously (simulation)"""
        print("🚀 Provisioning infrastructure autonomously...")
        try:
            return await self.cloudrun_deployer.provision_infrastructure()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def deploy_applications_autonomous(self, deployment_plan: Dict, config: Dict = None) -> Dict:
        """Deploy applications autonomously (simulation)"""
        print("🐳 Deploying applications autonomously...")
        if config is None:
            config = {
                'project_name': 'autonomous-project', 
                'region': 'us-central1'
            }
        return await self.cloudrun_deployer.build_and_deploy_services(config, deployment_plan)
    
    async def setup_monitoring_autonomous(self, deployment_plan: Dict, config: Dict = None) -> Dict:
        """Setup monitoring autonomously (simulation)"""
        print("📊 Setting up monitoring autonomously...")
        if config is None:
            config = {}
        return await self.cloudrun_deployer.setup_monitoring(config)
    
    # REAL DEPLOYMENT METHODS
    async def provision_infrastructure_real(self, deployment_plan: Dict, config: Dict) -> Dict:
        """Provision real infrastructure using Terraform"""
        print("🚀 Provisioning REAL infrastructure with Terraform...")
        
        # Clean up any existing Terraform state to avoid conflicts
        await self.clean_terraform_state()
        
        # Set environment variable for service account authentication
        service_account_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        env = os.environ.copy()
        
        if service_account_key and os.path.exists(service_account_key):
            print(f"🔑 Using service account: {service_account_key}")
            env['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key
            env['GOOGLE_PROJECT'] = self._get_gcp_project()
        else:
            print("⚠️  No service account key found, using default authentication")
        
        project_id = self._get_gcp_project()
        
        # Check cloud quotas and prerequisites
        await self._check_cloud_quotas(project_id)
        
        try:
            # Step 1: Initialize Terraform
            print("   🔧 Initializing Terraform...")
            init_result = subprocess.run([
                "terraform", "init", "-upgrade", "-reconfigure"
            ], cwd=self.cloudrun_deployer.terraform_dir, capture_output=True, text=True, env=env)
            
            if init_result.returncode != 0:
                print(f"   ❌ Terraform init failed: {init_result.stderr}")
                
                # Try with more aggressive cleanup
                await self.force_clean_terraform()
                init_result = subprocess.run([
                    "terraform", "init", "-upgrade", "-reconfigure"
                ], cwd=self.cloudrun_deployer.terraform_dir, capture_output=True, text=True, env=env)
                
                if init_result.returncode != 0:
                    return {'success': False, 'error': f"Terraform init failed: {init_result.stderr}"}
            
            print("   ✅ Terraform initialized")
            
            # Step 2: Validate Terraform configuration
            print("   🔍 Validating Terraform configuration...")
            validate_result = subprocess.run([
                "terraform", "validate"
            ], cwd=self.cloudrun_deployer.terraform_dir, capture_output=True, text=True, env=env)
            
            if validate_result.returncode != 0:
                print(f"   ⚠️  Terraform validation warnings: {validate_result.stderr}")
            
            # Step 3: Test Terraform plan with authentication
            print("   🔐 Testing Terraform authentication with plan...")
            plan_result = subprocess.run([
                "terraform", "plan",
                "-input=false",
                "-lock=false",
                "-detailed-exitcode"
            ], cwd=self.cloudrun_deployer.terraform_dir, capture_output=True, text=True, env=env)
            
            # Exit code 0 = success, no changes
            # Exit code 1 = error
            # Exit code 2 = success, changes present
            if plan_result.returncode not in [0, 2]:
                error_output = plan_result.stderr
                print(f"   ❌ Terraform plan failed: {error_output}")
                return {'success': False, 'error': f"Terraform plan failed: {plan_result.stderr}"}
            
            print("   ✅ Terraform authentication and plan successful")
            
            # Step 4: Apply Terraform configuration
            print("   🚀 Applying Terraform configuration...")
            apply_result = subprocess.run([
                "terraform", "apply", "-auto-approve",
                "-input=false",
                "-lock=false"
            ], cwd=self.cloudrun_deployer.terraform_dir, capture_output=True, text=True, env=env)
            
            if apply_result.returncode != 0:
                print(f"   ❌ Terraform apply failed: {apply_result.stderr}")
                return {'success': False, 'error': f"Terraform apply failed: {apply_result.stderr}"}
            
            print("   ✅ Terraform apply completed")
            
            # Step 5: Get outputs
            output_result = subprocess.run([
                "terraform", "output", "-json"
            ], cwd=self.cloudrun_deployer.terraform_dir, capture_output=True, text=True, env=env)
            
            if output_result.returncode == 0:
                try:
                    outputs = json.loads(output_result.stdout)
                    database_connection = outputs.get('database_connection', {}).get('value', 'unknown')
                    service_urls = outputs.get('service_urls', {}).get('value', {})
                    database_private_ip = outputs.get('database_private_ip', {}).get('value', 'unknown')
                    random_suffix = outputs.get('random_suffix', {}).get('value', 'unknown')
                except json.JSONDecodeError:
                    database_connection = 'unknown'
                    service_urls = {}
                    database_private_ip = 'unknown'
                    random_suffix = 'unknown'
            else:
                database_connection = 'unknown'
                service_urls = {}
                database_private_ip = 'unknown'
                random_suffix = 'unknown'
            
            print("✅ Real infrastructure provisioned")
            return {
                'success': True,
                'database_connection': database_connection,
                'database_private_ip': database_private_ip,
                'service_urls': service_urls,
                'random_suffix': random_suffix
            }
            
        except Exception as e:
            error_msg = f"Terraform provisioning failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    async def deploy_applications_real(self, deployment_plan: Dict, config: Dict) -> Dict:
        """Deploy applications to real Cloud Run"""
        print("🐳 Deploying to REAL Cloud Run...")
        
        # Authenticate with service account for gcloud commands
        service_account_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if service_account_key and os.path.exists(service_account_key):
            print(f"🔑 Authenticating gcloud with service account...")
            try:
                auth_result = subprocess.run([
                    "gcloud", "auth", "activate-service-account",
                    f"--key-file={service_account_key}",
                    f"--project={self._get_gcp_project()}"
                ], check=True, capture_output=True, text=True)
                print("✅ Service account activated for gcloud")
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                return {'success': False, 'error': f"Service account authentication failed: {error_msg}"}
        
        results = {
            'services': [],
            'urls': {}
        }
        
        project_id = self._get_gcp_project()
        region = config['region']
        
        # Get the random suffix from Terraform outputs
        random_suffix = "unknown"
        try:
            output_result = subprocess.run([
                "terraform", "output", "-raw", "random_suffix"
            ], cwd=self.cloudrun_deployer.terraform_dir, capture_output=True, text=True)
            if output_result.returncode == 0:
                random_suffix = output_result.stdout.strip()
        except:
            pass
        
        repository_id = f"{config['project_name']}-repo-{random_suffix}"
        
        # Enable required services first (in case they're not already enabled)
        print("   🔧 Ensuring required GCP services are enabled...")
        required_services = [
            "run.googleapis.com",
            "cloudbuild.googleapis.com", 
            "artifactregistry.googleapis.com",
            "sqladmin.googleapis.com"
        ]
        
        for service in required_services:
            try:
                subprocess.run([
                    "gcloud", "services", "enable", service,
                    f"--project={project_id}",
                    "--quiet"
                ], check=True, capture_output=True)
                print(f"   ✅ Enabled {service}")
            except subprocess.CalledProcessError:
                print(f"   ⚠️  Could not enable {service} (may already be enabled)")
        
        for service in deployment_plan['services']:
            service_name = service['name']
            project_path = service.get('project', {}).get('path', '.')
            
            print(f"   🚀 Deploying {service_name}...")
            
            try:
                # Build and push container image
                image_url = f"{region}-docker.pkg.dev/{project_id}/{repository_id}/{service_name}:latest"
                
                print(f"   🏗️  Building container for {service_name}...")
                build_result = subprocess.run([
                    "gcloud", "builds", "submit",
                    f"--tag={image_url}",
                    f"--project={project_id}",
                    project_path
                ], check=True, capture_output=True, text=True)
                
                print(f"   ✅ Container built: {image_url}")
                
                # Deploy to Cloud Run
                print(f"   🚀 Deploying to Cloud Run...")
                deploy_result = subprocess.run([
                    "gcloud", "run", "deploy", f"{service_name}-{random_suffix}",
                    f"--image={image_url}",
                    f"--region={region}",
                    f"--project={project_id}",
                    "--allow-unauthenticated",
                    "--platform=managed",
                    "--memory=2Gi",
                    "--cpu=1",
                    "--max-instances=10",
                    "--min-instances=0"
                ], check=True, capture_output=True, text=True)
                
                # Get the service URL
                describe_result = subprocess.run([
                    "gcloud", "run", "services", "describe", f"{service_name}-{random_suffix}",
                    f"--region={region}",
                    f"--project={project_id}",
                    "--platform=managed",
                    "--format=value(status.url)"
                ], capture_output=True, text=True, check=True)
                
                service_url = describe_result.stdout.strip()
                
                results['services'].append({
                    'name': service_name,
                    'url': service_url,
                    'status': 'deployed',
                    'image': image_url
                })
                results['urls'][service_name] = service_url
                
                print(f"   ✅ {service_name} deployed: {service_url}")
                
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                print(f"   ❌ Failed to deploy {service_name}: {error_msg}")
                results['services'].append({
                    'name': service_name,
                    'status': 'failed',
                    'error': error_msg
                })
            except Exception as e:
                print(f"   ❌ Unexpected error deploying {service_name}: {e}")
                results['services'].append({
                    'name': service_name,
                    'status': 'failed',
                    'error': str(e)
                })
    
        return results
    
    async def setup_monitoring_real(self, deployment_plan: Dict, config: Dict) -> Dict:
        """Setup real monitoring in GCP"""
        print("📊 Setting up REAL monitoring...")
        
        project_id = self._get_gcp_project()
        
        try:
            # Enable monitoring APIs
            subprocess.run([
                "gcloud", "services", "enable", "monitoring.googleapis.com",
                f"--project={project_id}",
                "--quiet"
            ], check=True, capture_output=True)
            
            print("   ✅ Monitoring services enabled")
            
            return {
                'monitoring': {
                    'enabled': True,
                    'alerts': True,
                    'logging': True,
                    'services_monitored': len(deployment_plan['services'])
                }
            }
            
        except Exception as e:
            print(f"⚠️  Monitoring setup had issues: {e}")
            return {
                'monitoring': {
                    'enabled': False,
                    'error': str(e)
                }
            }
    
    async def estimate_costs(self, deployment_plan: Dict) -> float:
        """Estimate deployment costs"""
        # Simple cost estimation logic
        base_cost = 8.0  # Cloud SQL micro instance
        service_count = len(deployment_plan.get('services', []))
        service_cost = service_count * 5.0
        return base_cost + service_cost
    
    async def validate_configuration(self, config: Dict) -> List[str]:
        """Validate deployment configuration"""
        errors = []
        
        if not config.get('repo_url'):
            errors.append("Repository URL is required")
        
        if not config.get('project_name'):
            errors.append("Project name is required")
        
        return errors
    
    def _get_gcp_project(self) -> str:
        """Get current GCP project"""
        # First try environment variable
        project_id = os.getenv('GCP_PROJECT_ID')
        if project_id:
            return project_id
        
        # Then try gcloud config
        try:
            result = subprocess.run([
                "gcloud", "config", "get-value", "project"
            ], capture_output=True, text=True, check=True)
            project_id = result.stdout.strip()
            if project_id and project_id != "(unset)":
                return project_id
        except:
            pass
        
        # Finally try the service account file
        service_account_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if service_account_key and os.path.exists(service_account_key):
            try:
                with open(service_account_key, 'r') as f:
                    sa_data = json.load(f)
                    return sa_data.get('project_id', 'unknown-project')
            except:
                pass
        
        return 'unknown-project'
    
    def _check_gcp_authentication(self) -> bool:
        """Check if GCP authentication is set up"""
        # Check if service account key exists
        service_account_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if service_account_key and os.path.exists(service_account_key):
            return True
        
        # Check if gcloud is authenticated
        try:
            result = subprocess.run([
                "gcloud", "auth", "list", "--format=value(account)"
            ], capture_output=True, text=True, check=True)
            return bool(result.stdout.strip())
        except:
            return False

    async def validate_gcp_authentication(self) -> Dict:
        """Validate GCP authentication before deployment"""
        print("🔐 Validating GCP authentication...")
        
        # Check service account file
        service_account_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not service_account_key or not os.path.exists(service_account_key):
            return {'success': False, 'error': 'GOOGLE_APPLICATION_CREDENTIALS not set or file not found'}
        
        # Validate service account file is JSON
        try:
            with open(service_account_key, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Service account key is not valid JSON'}
        
        # Test gcloud authentication
        try:
            project_id = self._get_gcp_project()
            auth_check = subprocess.run([
                "gcloud", "auth", "list", "--filter=status:ACTIVE", 
                "--format=value(account)", f"--project={project_id}"
            ], capture_output=True, text=True, check=True)
            
            if not auth_check.stdout.strip():
                return {'success': False, 'error': 'No active GCP authentication found'}
                
            print(f"   ✅ Authenticated as: {auth_check.stdout.strip()}")
            return {'success': True, 'account': auth_check.stdout.strip()}
            
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': f'GCP authentication check failed: {e.stderr}'}
    
    async def clean_terraform_state(self):
        """Clean up Terraform state to avoid conflicts"""
        terraform_dir = self.cloudrun_deployer.terraform_dir
        if terraform_dir.exists():
            print("   🧹 Cleaning up previous Terraform state...")
            # Remove Terraform state files but keep configuration
            state_files = [
                terraform_dir / ".terraform",
                terraform_dir / "terraform.tfstate",
                terraform_dir / "terraform.tfstate.backup",
                terraform_dir / ".terraform.tfstate.lock.info"
            ]
            
            for state_file in state_files:
                if state_file.exists():
                    if state_file.is_dir():
                        shutil.rmtree(state_file, ignore_errors=True)
                    else:
                        try:
                            state_file.unlink()
                        except:
                            pass
                    print(f"   ✅ Removed {state_file.name}")

    async def force_clean_terraform(self):
        """Force clean Terraform state and lock files"""
        terraform_dir = self.cloudrun_deployer.terraform_dir
        if terraform_dir.exists():
            print("   🧹 Force cleaning Terraform state...")
            
            # Remove all Terraform state and cache files
            state_files = [
                terraform_dir / ".terraform",
                terraform_dir / ".terraform.lock.hcl",
                terraform_dir / "terraform.tfstate",
                terraform_dir / "terraform.tfstate.backup",
                terraform_dir / ".terraform.tfstate.lock.info"
            ]
            
            for state_file in state_files:
                if state_file.exists():
                    if state_file.is_dir():
                        shutil.rmtree(state_file, ignore_errors=True)
                    else:
                        try:
                            state_file.unlink()
                        except:
                            pass
                    print(f"   ✅ Removed {state_file.name}")
    
    async def cleanup(self):
        """Clean up temporary files and resources"""
        temp_files = [
            self.outputs_dir / "terraform",
            self.outputs_dir / "kubernetes", 
            self.outputs_dir / "build"
        ]
        
        for temp_file in temp_files:
            if temp_file.exists():
                shutil.rmtree(temp_file)