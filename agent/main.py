#!/usr/bin/env python3
"""
Agentic AI Deployment System - Cloud Run Edition
Deploys .NET APIs to Google Cloud Run with PostgreSQL
"""

import os
import sys
import asyncio
import click
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.prompter import DeploymentPrompter
from agent.detector import TechStackDetector
from agent.deployer import DeploymentOrchestrator


class CloudRunDeploymentAgent:
    def __init__(self, auto_deploy=False):
        self.auto_deploy = auto_deploy
        self.prompter = DeploymentPrompter()
        self.detector = TechStackDetector()
        self.deployer = DeploymentOrchestrator()
        
        # Cloud Run optimized configuration
        self.config = {
            'repo_url': None,
            'project_name': None,
            'region': 'us-central1',
            'database_tier': 'db-f1-micro',
            'max_instances': 10,
            'cpu': 1,
            'memory': '2Gi',
            'deployment_type': 'cloudrun'
        }
    
    async def run(self):
        """Cloud Run deployment flow"""
        try:
            self.show_welcome_banner()
            
            # Step 1: Gather repository information
            await self.gather_repository_info()
            
            # Step 2: Analyze .NET solution
            tech_stack = await self.analyze_solution()
            
            # Step 3: Generate Cloud Run deployment plan
            deployment_plan = await self.generate_cloudrun_plan(tech_stack)
            
            # Step 4: Confirm and deploy
            if await self.confirm_deployment(deployment_plan):
                await self.execute_cloudrun_deployment(deployment_plan)
            else:
                print("❌ Deployment cancelled.")
                
        except Exception as e:
            print(f"❌ Deployment failed: {str(e)}")
            sys.exit(1)
    
    def show_welcome_banner(self):
        """Display welcome banner"""
        print("🚀 Agentic AI - Cloud Run Deployer")
        print("=" * 50)
        print("📝 Default: Google Cloud Run + PostgreSQL")
        print("💡 Perfect for .NET APIs with Dockerfiles")
        print("💰 Cost-effective serverless deployment")
        print("=" * 50)
    
    async def gather_repository_info(self):
        """Get repository details"""
        print("\n📋 Repository Information")
        print("-" * 30)
        
        self.config['repo_url'] = self.prompter.prompt_repository_url()
        self.config['project_name'] = self.prompter.prompt_project_name()
        
        # Optional: Let user choose region
        region_choice = input(f"🌍 Choose region [{self.config['region']}]: ").strip()
        if region_choice:
            self.config['region'] = region_choice
        
        print(f"✅ Target: Cloud Run ({self.config['region']})")
    
    async def analyze_solution(self):
        """Analyze .NET solution for Cloud Run compatibility"""
        print(f"\n🔍 Analyzing {self.config['repo_url']}")
        
        repo_path = await self.detector.clone_repository(self.config['repo_url'])
        tech_stack = self.detector.detect_dotnet_stack(repo_path)
        
        # Cloud Run specific validation
        if not tech_stack.get('dockerfiles'):
            print("❌ No Dockerfiles found. Cloud Run requires containerized applications.")
            print("💡 Please add Dockerfiles to your .NET projects")
            sys.exit(1)
        
        print("✅ Cloud Run Compatibility:")
        print(f"   .NET Version: {tech_stack.get('dotnet_version', 'Unknown')}")
        print(f"   API Projects: {len(tech_stack.get('api_projects', []))}")
        print(f"   Dockerfiles: {len(tech_stack.get('dockerfiles', []))}")
        print(f"   Database: {tech_stack.get('database_type', 'PostgreSQL (auto-provisioned)')}")
        
        return tech_stack
    
    async def generate_cloudrun_plan(self, tech_stack):
        """Generate Cloud Run specific deployment plan"""
        print("\n📋 Generating Cloud Run Deployment Plan")
        print("-" * 40)
        
        plan = {
            'services': [],
            'infrastructure': {
                'cloud_sql': {
                    'instance': f"{self.config['project_name']}-postgres",
                    'tier': self.config['database_tier'],
                    'database': 'appdb'
                },
                'artifact_registry': {
                    'repository': f"{self.config['project_name']}-repo",
                    'format': 'DOCKER'
                }
            },
            'ci_cd': {
                'trigger': 'Cloud Build',
                'auto_deploy': True
            }
        }
        
        # Create service for each API project
        for api_project in tech_stack.get('api_projects', []):
            service_name = api_project['name'].replace('.', '-').replace('_', '-').lower()
            plan['services'].append({
                'name': service_name,
                'project': api_project,
                'config': {
                    'cpu': self.config['cpu'],
                    'memory': self.config['memory'],
                    'max_instances': self.config['max_instances'],
                    'port': 8080  # .NET default
                }
            })
        
        return plan
    
    async def confirm_deployment(self, deployment_plan):
        """Show deployment summary and get confirmation"""
        print("\n" + "="*60)
        print("🚀 CLOUD RUN DEPLOYMENT PLAN")
        print("="*60)
        
        print(f"📦 Project: {self.config['project_name']}")
        print(f"🌍 Region: {self.config['region']}")
        print(f"🛠️  Services to deploy: {len(deployment_plan['services'])}")
        
        for service in deployment_plan['services']:
            print(f"   • {service['name']}: {service['config']['cpu']} CPU, {service['config']['memory']}")
        
        print(f"🗄️  Database: Cloud SQL PostgreSQL ({deployment_plan['infrastructure']['cloud_sql']['tier']})")
        print(f"🔧 CI/CD: Automatic container builds on git push")
        
        # Cost estimation
        estimated_cost = self.estimate_cloudrun_cost(deployment_plan)
        print(f"💰 Estimated monthly cost: ${estimated_cost:.2f}")
        
        print("\n⚠️  This will:")
        print("   • Create Cloud Run services")
        print("   • Provision Cloud SQL PostgreSQL instance")
        print("   • Set up Artifact Registry for container images")
        print("   • Configure CI/CD pipelines")
        
        return self.prompter.prompt_confirmation("Proceed with Cloud Run deployment?")
    
    def estimate_cloudrun_cost(self, plan):
        """Estimate Cloud Run costs"""
        base_cost = 8.0  # Cloud SQL micro instance
        service_cost = len(plan['services']) * 5.0  # Approximate per service
        return base_cost + service_cost
    
    async def execute_cloudrun_deployment(self, deployment_plan):
        """Execute Cloud Run deployment"""
        print("\n🛠️ Starting Cloud Run Deployment...")
        
        # Execute deployment through orchestrator
        result = await self.deployer.deploy_to_cloudrun(
            self.config, 
            deployment_plan
        )
        
        if result['success']:
            print("\n✅ Deployment Complete!")
            await self.display_deployment_summary(result)
        else:
            print(f"❌ Deployment failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    async def display_deployment_summary(self, result):
        """Display Cloud Run deployment summary"""
        print("\n🎉 Your .NET APIs are now running on Cloud Run!")
        print("\n🔗 Access your services:")
        
        for service in result.get('services', []):
            print(f"   {service['name']}: {service['url']}")
        
        print(f"\n🗄️  Database connection: {result.get('database_connection')}")
        
        print("\n📊 Next steps:")
        print("   make monitor    # Open Cloud Run dashboard")
        print("   make logs       # View application logs")
        print("   make destroy    # Clean up resources")
        print("\n💡 Your database connection string is automatically configured")
        print("   via Cloud Run environment variables")


@click.command()
@click.option('--auto', is_flag=True, help='Auto-deploy without confirmation')
@click.option('--project', help='GCP project ID')
@click.option('--region', default='us-central1', help='GCP region')
def main(auto, project, region):
    """Deploy .NET APIs to Google Cloud Run"""
    
    # Check for basic requirements
    try:
        import google.auth
    except ImportError:
        print("❌ Google Cloud libraries not installed. Run: make install")
        sys.exit(1)
    
    agent = CloudRunDeploymentAgent(auto_deploy=auto)
    if project:
        agent.config['project_name'] = project
    if region:
        agent.config['region'] = region
        
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()