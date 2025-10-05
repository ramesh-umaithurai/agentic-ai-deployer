#!/usr/bin/env python3
"""
Test the autonomous agent with the specific Furniqo.API repository
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from autonomous_agent import AutonomousDeploymentAgent
from agent.detector import TechStackDetector


async def test_furniqo_repository():
    """Test with the specific Furniqo.API repository"""
    print("🧪 Testing with Furniqo.API repository...")
    
    # Test the detector directly first
    detector = TechStackDetector()
    
    try:
        repo_url = "https://github.com/k-ashokkumar/Furniqo.API"
        print(f"🔗 Testing repository: {repo_url}")
        
        repo_path = await detector.clone_repository(repo_url)
        print(f"✅ Repository cloned successfully to: {repo_path}")
        
        tech_stack = detector.detect_tech_stack(repo_path)
        print(f"✅ Tech stack detected:")
        print(f"   .NET projects: {len(tech_stack['dotnet']['projects'])}")
        print(f"   API projects: {len(tech_stack['dotnet']['api_projects'])}")
        print(f"   Dockerfiles: {len(tech_stack['docker']['dockerfiles'])}")
        print(f"   Database: {tech_stack['database']['type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Repository test failed: {e}")
        return False


async def test_autonomous_with_furniqo():
    """Test autonomous deployment with Furniqo"""
    print("\n🧪 Testing autonomous deployment with Furniqo...")
    
    agent = AutonomousDeploymentAgent()
    
    test_input = "deploy .net api from https://github.com/k-ashokkumar/Furniqo.API"
    
    print(f"💬 Test input: {test_input}")
    result = await agent.deploy_from_natural_language(test_input)
    
    print(f"📊 Result: {result}")
    
    if result.get('success'):
        print("✅ Test passed!")
    else:
        print(f"❌ Test failed: {result.get('error', 'Unknown error')}")
        if 'suggestion' in result:
            print(f"💡 Suggestion: {result['suggestion']}")


if __name__ == "__main__":
    print("🚀 Testing Furniqo.API Repository...")
    
    # First test just the repository cloning and detection
    success = asyncio.run(test_furniqo_repository())
    
    if success:
        # Then test the full autonomous deployment
        asyncio.run(test_autonomous_with_furniqo())
    else:
        print("💥 Repository test failed, skipping autonomous deployment test")