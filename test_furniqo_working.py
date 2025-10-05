#!/usr/bin/env python3
"""
Test the autonomous agent with the Furniqo.API repository - WORKING VERSION
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.detector import TechStackDetector
from agent.deployer import DeploymentOrchestrator


async def test_furniqo_detection():
    """Test Furniqo repository detection"""
    print("🧪 Testing Furniqo.API repository detection...")
    
    detector = TechStackDetector()
    
    try:
        repo_url = "https://github.com/k-ashokkumar/Furniqo.API"
        print(f"🔗 Testing repository: {repo_url}")
        
        repo_path = await detector.clone_repository(repo_url)
        print(f"✅ Repository cloned successfully to: {repo_path}")
        
        tech_stack = detector.detect_tech_stack(repo_path)
        print(f"✅ Tech stack detected:")
        print(f"   .NET Version: {tech_stack['dotnet']['version']}")
        print(f"   .NET Projects: {len(tech_stack['dotnet']['projects'])}")
        print(f"   API Projects: {len(tech_stack['dotnet']['api_projects'])}")
        for project in tech_stack['dotnet']['api_projects']:
            print(f"     - {project['name']}")
        print(f"   Dockerfiles: {len(tech_stack['docker']['dockerfiles'])}")
        print(f"   Database: {tech_stack['database']['type']}")
        
        return tech_stack
        
    except Exception as e:
        print(f"❌ Repository test failed: {e}")
        return None


async def test_deployment_plan_generation(tech_stack):
    """Test deployment plan generation"""
    print("\n🧪 Testing deployment plan generation...")
    
    deployer = DeploymentOrchestrator()
    
    try:
        # Create a deployment plan based on the tech stack
        deployment_plan = {
            'services': [],
            'infrastructure': {
                'cloud_sql': {
                    'instance': 'furniqo-postgres',
                    'tier': 'db-f1-micro',
                    'database': 'furniqodb'
                },
                'artifact_registry': {
                    'repository': 'furniqo-repo',
                    'format': 'DOCKER'
                }
            }
        }
        
        # Create services for each API project
        for api_project in tech_stack['dotnet']['api_projects']:
            service_name = api_project['name'].replace('.', '-').lower()
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
        
        print(f"✅ Deployment plan created with {len(deployment_plan['services'])} services")
        
        # Test cost estimation
        cost = await deployer.estimate_costs(deployment_plan)
        print(f"💰 Estimated monthly cost: ${cost:.2f}")
        
        return deployment_plan
        
    except Exception as e:
        print(f"❌ Deployment plan generation failed: {e}")
        return None


async def test_infrastructure_generation(deployment_plan):
    """Test infrastructure generation"""
    print("\n🧪 Testing infrastructure generation...")
    
    deployer = DeploymentOrchestrator()
    
    try:
        config = {
            'project_name': 'furniqo-test',
            'region': 'us-central1',
            'database_tier': 'db-f1-micro'
        }
        
        # Generate Terraform files
        await deployer.generate_infrastructure_autonomous(deployment_plan, config)
        print("✅ Terraform files generated successfully")
        
        # Check if files were created
        outputs_dir = Path("outputs/terraform")
        if outputs_dir.exists():
            files = list(outputs_dir.glob("*.tf"))
            print(f"📁 Generated {len(files)} Terraform files:")
            for file in files:
                print(f"   - {file.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Infrastructure generation failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Testing Furniqo.API Deployment Pipeline...")
    
    # Step 1: Test repository detection
    tech_stack = await test_furniqo_detection()
    if not tech_stack:
        return
    
    # Step 2: Test deployment plan generation
    deployment_plan = await test_deployment_plan_generation(tech_stack)
    if not deployment_plan:
        return
    
    # Step 3: Test infrastructure generation
    success = await test_infrastructure_generation(deployment_plan)
    
    if success:
        print("\n🎉 All tests passed! The Furniqo.API deployment pipeline is working.")
        print("\n📝 Next steps:")
        print("   1. Configure GCP credentials in .env file")
        print("   2. Run: python autonomous_agent.py")
        print("   3. Enter: 'deploy https://github.com/k-ashokkumar/Furniqo.API to GCP'")
    else:
        print("\n💥 Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())