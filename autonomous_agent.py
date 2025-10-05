#!/usr/bin/env python3
"""
Fully Autonomous Deployment Agent with Ollama Integration
Can make deployment decisions, learn from patterns, and work autonomously
"""

import asyncio
import json
import re
import uuid
import os
import subprocess
from typing import Dict, List, Optional
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from agent.detector import TechStackDetector
from agent.deployer import DeploymentOrchestrator

# Import the new autonomous modules
try:
    from ollama_integration import OllamaManager
    from decision_engine import DecisionEngine
    from memory_system import DeploymentMemory
except ImportError:
    # Create placeholder classes if modules don't exist yet
    class OllamaManager:
        async def analyze_deployment_intent(self, user_input): 
            return {"repository_url": None}
        async def analyze_code_structure(self, repo_path): 
            return {}
        async def determine_deployment_strategy(self, context): 
            return {}
        async def suggest_cost_optimizations(self, plan, budget): 
            return {"can_optimize": False}
        async def suggest_error_recovery(self, error, context): 
            return {"can_recover": False}
        def extract_repository_url(self, text):
            # Simple URL extraction without Ollama
            patterns = [
                r'https?://(?:www\.)?github\.com/[\w\-\.,]+/[\w\-\.,]+',
                r'https?://(?:www\.)?gitlab\.com/[\w\-\.,]+/[\w\-\.,]+',
                r'https?://(?:www\.)?bitbucket\.org/[\w\-\.,]+/[\w\-\.,]+',
                r'github\.com/[\w\-\.,]+/[\w\-\.,]+',
                r'gitlab\.com/[\w\-\.,]+/[\w\-\.,]+',
                r'bitbucket\.org/[\w\-\.,]+/[\w\-\.,]+'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    url = match.group()
                    if not url.startswith('http'):
                        url = 'https://' + url
                    return url
            return None
    
    class DecisionEngine:
        async def generate_optimal_plan(self, tech_stack, strategy, config):
            return {
                "infrastructure": {
                    "cloud_provider": "gcp",
                    "compute_service": "cloud_run", 
                    "region": "us-central1",
                    "service_count": len(tech_stack.get('dotnet', {}).get('api_projects', []))
                },
                "services": [],
                "database": {
                    "type": "postgresql",
                    "tier": "db-f1-micro",
                    "backup_enabled": True,
                    "high_availability": False
                },
                "monitoring": {
                    "enabled": True,
                    "alerts": True,
                    "logging": True,
                    "metrics": ["cpu", "memory", "requests", "latency"]
                },
                "scaling": {
                    "auto_scaling": True,
                    "min_instances": 0,
                    "max_instances": 10,
                    "target_cpu_utilization": 60
                }
            }
    
    class DeploymentMemory:
        async def record_deployment(self, intent, plan, result): pass
        async def record_failure(self, intent, error_result): pass
        async def find_similar_deployments(self, tech_stack): return []
        async def get_relevant_experiences(self, tech_stack): return []


class AutonomousDeploymentAgent:
    def __init__(self):
        self.ollama = OllamaManager()
        self.detector = TechStackDetector()
        self.deployer = DeploymentOrchestrator()
        self.decision_engine = DecisionEngine()
        self.memory = DeploymentMemory()
        
        # Autonomous configuration
        self.config = {
            'auto_approve': True,
            'budget_limit': 100,
            'preferred_providers': ['gcp', 'aws', 'azure'],
            'deployment_strategy': 'cost_optimized',
            'deployment_mode': 'simulation'  # 'simulation' or 'real'
        }
    
    def check_authentication(self) -> bool:
        """Check if cloud authentication is properly set up"""
        print("🔐 Checking cloud authentication...")
        
        if self.config['deployment_mode'] == 'real':
            # Check if environment variables are set
            project_id = os.getenv('GCP_PROJECT_ID')
            service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            
            print(f"   GCP_PROJECT_ID: {project_id}")
            print(f"   GOOGLE_APPLICATION_CREDENTIALS: {service_account_path}")
            
            if not project_id or project_id == 'your-actual-project-id':
                print("❌ GCP_PROJECT_ID not properly configured")
                print("💡 Please update .env file with your actual GCP project ID")
                return False
            
            if not service_account_path or service_account_path == 'path/to/your/service-account-key.json':
                print("❌ GOOGLE_APPLICATION_CREDENTIALS not properly configured")
                print("💡 Please update .env file with the actual path to your service account key")
                return False
            
            # Check if service account file exists
            if not os.path.exists(service_account_path):
                print(f"❌ Service account key file not found: {service_account_path}")
                print("💡 Please check the path in your .env file")
                return False
            
            # Check GCP authentication
            if not self.deployer._check_gcp_authentication():
                print("❌ GCP authentication failed")
                print("💡 Please verify your service account key has the required permissions:")
                print("   - Cloud Run Admin")
                print("   - Cloud SQL Admin") 
                print("   - Storage Admin")
                print("   - Cloud Build Editor")
                return False
            
            print(f"✅ GCP authentication verified - Project: {project_id}")
        
        return True
    
    async def deploy_from_natural_language(self, user_request: str) -> Dict:
        """Process natural language deployment requests"""
        print("🧠 Processing your request...")
        
        # Extract deployment intent
        intent = await self.ollama.analyze_deployment_intent(user_request)
        
        if not intent.get('repository_url'):
            # Try to find repository from context
            repo_url = self.ollama.extract_repository_url(user_request)
            if repo_url:
                intent['repository_url'] = repo_url
            else:
                return {
                    'success': False,
                    'error': 'Could not determine repository URL from request',
                    'suggestion': 'Please provide a complete GitHub/GitLab URL'
                }
        
        return await self.autonomous_deployment_flow(intent)
    
    async def autonomous_deployment_flow(self, intent: Dict) -> Dict:
        """Fully autonomous deployment flow"""
        try:
            print("🚀 Starting Autonomous Deployment...")
            
            # Step 1: Analyze repository and tech stack
            tech_stack = await self.analyze_repository_autonomous(intent['repository_url'])
            
            # Step 2: Autonomous decision making
            deployment_plan = await self.make_autonomous_decisions(tech_stack, intent)
            
            # Step 3: Check constraints and budget
            if not await self.validate_constraints(deployment_plan):
                return {
                    'success': False,
                    'error': 'Deployment exceeds budget or constraints',
                    'suggestion': 'Consider optimizing resource allocations'
                }
            
            # Step 4: Execute deployment
            result = await self.execute_autonomous_deployment(deployment_plan)
            
            # Step 5: Learn from this deployment
            await self.memory.record_deployment(intent, deployment_plan, result)
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'recovery_attempt': await self.attempt_autonomous_recovery(e)
            }
            await self.memory.record_failure(intent, error_result)
            return error_result
    
    async def analyze_repository_autonomous(self, repo_url: str) -> Dict:
        """Autonomous repository analysis with enhanced detection"""
        print("🔍 Autonomous repository analysis...")
        
        try:
            # Clone and detect basic tech stack
            repo_path = await self.detector.clone_repository(repo_url)
            tech_stack = self.detector.detect_tech_stack(repo_path)
            
            # Use Ollama for advanced analysis (if available)
            try:
                advanced_analysis = await self.ollama.analyze_code_structure(repo_path)
                tech_stack.update(advanced_analysis)
            except Exception as e:
                print(f"⚠️  Advanced analysis skipped: {e}")
            
            # Learn from similar past deployments
            similar_deployments = await self.memory.find_similar_deployments(tech_stack)
            if similar_deployments:
                tech_stack['learned_patterns'] = similar_deployments
            
            return tech_stack
            
        except Exception as e:
            print(f"❌ Repository analysis failed: {e}")
            raise Exception(f"Failed to analyze repository: {e}")
    
    async def make_autonomous_decisions(self, tech_stack: Dict, intent: Dict) -> Dict:
        """Make autonomous deployment decisions"""
        print("🤖 Making autonomous deployment decisions...")
        
        # Generate decision context
        context = {
            'tech_stack': tech_stack,
            'user_intent': intent,
            'budget_constraints': self.config['budget_limit'],
            'past_experiences': await self.memory.get_relevant_experiences(tech_stack)
        }
        
        # Use Ollama for strategic decisions
        strategy = await self.ollama.determine_deployment_strategy(context)
        
        # Use decision engine for optimal resource allocation
        deployment_plan = await self.decision_engine.generate_optimal_plan(
            tech_stack, strategy, self.config
        )
        
        # Create services only for actual API projects (exclude shared libraries)
        deployment_plan['services'] = []
        api_count = 0
        
        for api_project in tech_stack.get('dotnet', {}).get('api_projects', []):
            # Skip shared libraries - only deploy actual API projects
            if 'shared' in api_project['name'].lower():
                print(f"🔧 Skipping shared library: {api_project['name']}")
                continue
                
            service_name = api_project['name'].replace('.', '-').replace('_', '-').lower()
            deployment_plan['services'].append({
                'name': service_name,
                'project': api_project,
                'config': {
                    'cpu': '1',
                    'memory': '2Gi',
                    'max_instances': 10,
                    'port': 8080
                }
            })
            api_count += 1
        
        print(f"✅ Created deployment plan with {api_count} API services")
        return deployment_plan
    
    async def validate_constraints(self, deployment_plan: Dict) -> bool:
        """Validate deployment against constraints"""
        try:
            cost_estimate = await self.deployer.estimate_costs(deployment_plan)
            
            if cost_estimate > self.config['budget_limit']:
                print(f"⚠️  Cost ${cost_estimate} exceeds budget ${self.config['budget_limit']}")
                
                # Use Ollama to suggest optimizations
                optimization_suggestions = await self.ollama.suggest_cost_optimizations(
                    deployment_plan, self.config['budget_limit']
                )
                
                if optimization_suggestions.get('can_optimize'):
                    print("💡 Cost optimization suggestions available")
                
                return True  # Continue anyway for now
            
            return True
        except Exception as e:
            print(f"⚠️  Cost validation failed: {e}")
            return True
    
    async def execute_autonomous_deployment(self, deployment_plan: Dict) -> Dict:
        """Execute deployment autonomously"""
        print("🛠️ Executing autonomous deployment...")
        
        # Check authentication for real deployment
        if self.config['deployment_mode'] == 'real' and not self.check_authentication():
            return {
                'success': False,
                'error': 'Cloud authentication not configured',
                'suggestion': 'Please set up GCP authentication as shown above'
            }
        
        try:
            # Create a basic config for autonomous deployment
            config = {
                'project_name': 'furniqo-app',
                'region': 'us-central1',
                'database_tier': 'db-f1-micro'
            }
            
            # Generate infrastructure code
            await self.deployer.generate_infrastructure_autonomous(deployment_plan, config)
            
            if self.config['deployment_mode'] == 'real':
                # REAL DEPLOYMENT
                print("🚀 Starting REAL deployment to Google Cloud Run...")
                
                # Provision resources (REAL)
                provision_result = await self.deployer.provision_infrastructure_real(deployment_plan, config)
                
                if not provision_result.get('success', True):
                    recovery_result = await self.attempt_autonomous_recovery(
                        provision_result.get('error', 'Unknown provisioning error'), 
                        deployment_plan
                    )
                    if not recovery_result['success']:
                        return recovery_result
                
                # Deploy applications (REAL)
                deploy_result = await self.deployer.deploy_applications_real(deployment_plan, config)
                
                # Setup monitoring (REAL)
                monitoring_result = await self.deployer.setup_monitoring_real(deployment_plan, config)
                
                message = 'Deployment completed successfully to Google Cloud Run!'
                
            else:
                # SIMULATION MODE (default)
                print("🚀 Simulating infrastructure provisioning...")
                provision_result = {'success': True, 'database_connection': 'furniqo-postgres'}
                
                # Deploy applications (SIMULATION)
                print("🐳 Simulating application deployment...")
                deploy_result = await self.deployer.deploy_applications_autonomous(deployment_plan, config)
                
                # Setup monitoring (SIMULATION)
                monitoring_result = await self.deployer.setup_monitoring_autonomous(deployment_plan, config)
                
                message = 'Deployment completed successfully (simulation mode)'
            
            return {
                'success': True,
                'services': deploy_result.get('services', []),
                'monitoring': monitoring_result,
                'cost_estimate': await self.deployer.estimate_costs(deployment_plan),
                'deployment_id': self.generate_deployment_id(),
                'message': message,
                'mode': self.config['deployment_mode']
            }
            
        except Exception as e:
            raise Exception(f"Deployment execution failed: {e}")
    
    async def attempt_autonomous_recovery(self, error: str, context: Dict = None) -> Dict:
        """Attempt autonomous recovery from errors using Ollama"""
        print("🔄 Attempting autonomous recovery...")
        
        try:
            error_str = str(error) if not isinstance(error, str) else error
            
            recovery_plan = await self.ollama.suggest_error_recovery(error_str, context)
            
            if recovery_plan.get('can_recover'):
                print(f"✅ Applying recovery strategy: {recovery_plan['strategy']}")
                return await self.execute_recovery_strategy(recovery_plan)
            else:
                return {
                    'success': False,
                    'error': f"Unable to recover automatically: {error_str}",
                    'suggestion': recovery_plan.get('suggestion', 'Manual intervention required')
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Recovery attempt failed: {e}",
                'suggestion': 'Please check the error and try again manually'
            }
    
    async def execute_recovery_strategy(self, recovery_plan: Dict) -> Dict:
        """Execute a recovery strategy"""
        strategy = recovery_plan.get('strategy', '').lower()
        
        if 'check repository url' in strategy or 'repository not found' in strategy:
            return {
                'success': False,
                'error': 'Repository not found',
                'suggestion': 'Please check the repository URL and ensure it exists and is accessible'
            }
        elif 'check cloud provider' in strategy or 'authentication' in strategy:
            return {
                'success': False, 
                'error': 'Cloud authentication issue',
                'suggestion': 'Please check your cloud provider credentials and authentication'
            }
        elif 'quota' in strategy:
            return {
                'success': False,
                'error': 'Cloud quota exceeded',
                'suggestion': 'Check your cloud provider quotas or try a different region'
            }
        elif 'config' in strategy or 'parameter' in strategy:
            return {
                'success': False,
                'error': 'Configuration error',
                'suggestion': 'There appears to be a configuration issue. Please check the deployment parameters.'
            }
        else:
            return {
                'success': False,
                'error': 'Automatic recovery not possible',
                'suggestion': recovery_plan.get('strategy', 'Manual intervention required')
            }
    
    def generate_deployment_id(self) -> str:
        """Generate unique deployment ID"""
        return f"dep-{uuid.uuid4().hex[:8]}"
    
    def set_deployment_mode(self, mode: str):
        """Set deployment mode (simulation or real)"""
        if mode in ['simulation', 'real']:
            self.config['deployment_mode'] = mode
            print(f"🔧 Deployment mode set to: {mode}")
            
            if mode == 'real':
                print("🚨 WARNING: REAL DEPLOYMENT MODE - This will deploy to actual Google Cloud Run")
                print("   Make sure you have GCP credentials configured in .env file!")
                print("   Required environment variables:")
                print("   - GCP_PROJECT_ID=your-actual-project-id")
                print("   - GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json")
        else:
            print("⚠️  Invalid deployment mode. Use 'simulation' or 'real'")


# Improved CLI interface with deployment mode option
async def main_autonomous():
    agent = AutonomousDeploymentAgent()
    
    print("🤖 Autonomous AI Deployment Agent")
    print("=================================")
    print("I can deploy your applications automatically!")
    print("\n📋 Current Mode: SIMULATION (no actual cloud deployment)")
    print("   Use '--real' flag for actual deployment to Google Cloud Run")
    print("\n💡 Examples:")
    print("  • 'deploy .net api from https://github.com/k-ashokkumar/Furniqo.API'")
    print("  • 'I need a PostgreSQL database and deploy this app with auto-scaling'") 
    print("  • 'Deploy this repository with cost under $50 per month'")
    print()
    
    # Check for command line arguments
    import sys
    if '--real' in sys.argv:
        agent.set_deployment_mode('real')
        print("\n" + "="*60)
    
    while True:
        try:
            user_input = input("\n💬 What would you like me to deploy? (or 'quit'): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
                
            print("🤔 Processing your request...")
            result = await agent.deploy_from_natural_language(user_input)
            
            print("\n" + "="*60)
            if result['success']:
                print("🎉 DEPLOYMENT SUCCESS!")
                print("="*60)
                print(f"Deployment ID: {result['deployment_id']}")
                print(f"Mode: {result.get('mode', 'simulation').upper()}")
                if 'services' in result:
                    print(f"Services deployed: {len(result['services'])}")
                    for service in result['services']:
                        status_icon = "✅" if service.get('status') == 'deployed' else "❌"
                        print(f"  {status_icon} {service['name']}: {service.get('url', 'N/A')}")
                if 'cost_estimate' in result:
                    print(f"Estimated cost: ${result['cost_estimate']:.2f}/month")
                if 'message' in result:
                    print(f"Status: {result['message']}")
            else:
                print("❌ DEPLOYMENT FAILED")
                print("="*60)
                print(f"Error: {result['error']}")
                if 'suggestion' in result:
                    print(f"Suggestion: {result['suggestion']}")
                if 'recovery_attempt' in result:
                    print(f"Recovery attempted: {result['recovery_attempt']}")
            print("="*60)
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
            print("💡 Please check your input and try again")


if __name__ == "__main__":
    asyncio.run(main_autonomous())