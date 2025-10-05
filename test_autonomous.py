#!/usr/bin/env python3
"""
Quick test script to verify the autonomous agent works
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from autonomous_agent import AutonomousDeploymentAgent
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all required files are created")
    sys.exit(1)


async def test_basic_functionality():
    """Test basic autonomous agent functionality"""
    print("🧪 Testing Autonomous Agent...")
    
    try:
        agent = AutonomousDeploymentAgent()
        print("✅ Agent initialized successfully")
        
        # Test with a simple repository URL
        test_input = "Deploy https://github.com/example/dotnet-api to GCP"
        
        print(f"💬 Test input: {test_input}")
        result = await agent.deploy_from_natural_language(test_input)
        
        print(f"📊 Result: {result}")
        
        if result.get('success'):
            print("✅ Test passed!")
        else:
            print(f"❌ Test failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 Error during test: {e}")
        import traceback
        traceback.print_exc()


async def test_autonomous_flow():
    """Test the full autonomous flow"""
    print("\n🧪 Testing Full Autonomous Flow...")
    
    agent = AutonomousDeploymentAgent()
    
    # Test the individual methods
    try:
        # Test repository analysis
        print("1. Testing repository analysis...")
        tech_stack = await agent.analyze_repository_autonomous("https://github.com/example/dotnet-api")
        print(f"   ✅ Tech stack detected: {list(tech_stack.keys())}")
        
        # Test decision making
        print("2. Testing decision making...")
        deployment_plan = await agent.make_autonomous_decisions(tech_stack, {"repository_url": "test"})
        print(f"   ✅ Deployment plan created with {len(deployment_plan.get('services', []))} services")
        
        # Test constraint validation
        print("3. Testing constraint validation...")
        is_valid = await agent.validate_constraints(deployment_plan)
        print(f"   ✅ Constraints valid: {is_valid}")
        
        print("🎉 All autonomous components working!")
        
    except Exception as e:
        print(f"❌ Autonomous flow test failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Autonomous Agent Tests...")
    asyncio.run(test_basic_functionality())
    # asyncio.run(test_autonomous_flow())  # Uncomment for more detailed testing