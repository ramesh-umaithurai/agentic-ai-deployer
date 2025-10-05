"""
Memory System for Learning from Past Deployments
Enables continuous improvement and pattern recognition
"""

import json
from typing import Dict, List
from pathlib import Path
import hashlib
from datetime import datetime


class DeploymentMemory:
    def __init__(self, memory_file: str = "deployment_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory = self.load_memory()
    
    def load_memory(self) -> Dict:
        """Load deployment memory from file"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "deployments": [],
            "patterns": {},
            "failures": [],
            "optimizations": {}
        }
    
    def save_memory(self):
        """Save deployment memory to file"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    async def record_deployment(self, intent: Dict, plan: Dict, result: Dict):
        """Record a successful deployment"""
        deployment_id = result.get('deployment_id', self.generate_deployment_id(intent))
        
        deployment_record = {
            "id": deployment_id,
            "intent": intent,
            "plan": plan,
            "result": result,
            "timestamp": self.get_timestamp(),
            "tech_stack_fingerprint": self.generate_tech_fingerprint(plan)
        }
        
        self.memory["deployments"].append(deployment_record)
        self.save_memory()
    
    async def record_failure(self, intent: Dict, error_result: Dict):
        """Record a deployment failure"""
        failure_record = {
            "intent": intent,
            "error": error_result.get('error'),
            "recovery_attempt": error_result.get('recovery_attempt'),
            "timestamp": self.get_timestamp()
        }
        
        self.memory["failures"].append(failure_record)
        self.save_memory()
    
    def generate_tech_fingerprint(self, plan: Dict) -> str:
        """Generate fingerprint for tech stack matching"""
        tech_data = json.dumps({
            "services": len(plan.get('services', [])),
            "database": plan.get('database', {}).get('type'),
            "compute": plan.get('infrastructure', {}).get('compute_service')
        }, sort_keys=True)
        
        return hashlib.md5(tech_data.encode()).hexdigest()
    
    async def find_similar_deployments(self, tech_stack: Dict) -> List[Dict]:
        """Find similar past deployments"""
        current_fingerprint = self.generate_tech_fingerprint({"services": tech_stack})
        
        similar = []
        for deployment in self.memory["deployments"]:
            if deployment["tech_stack_fingerprint"] == current_fingerprint:
                similar.append(deployment)
        
        return similar[:5]
    
    async def get_relevant_experiences(self, tech_stack: Dict) -> List[Dict]:
        """Get relevant past experiences for decision making"""
        similar = await self.find_similar_deployments(tech_stack)
        
        experiences = []
        for deployment in similar:
            experiences.append({
                "success": deployment["result"]["success"],
                "cost": deployment["result"].get("cost_estimate", 0),
                "challenges": deployment["result"].get("challenges", []),
                "optimizations": deployment["result"].get("optimizations_applied", [])
            })
        
        return experiences
    
    def generate_deployment_id(self, intent: Dict) -> str:
        """Generate deployment ID from intent"""
        repo_hash = hashlib.md5(
            intent.get('repository_url', '').encode()
        ).hexdigest()[:6]
        return f"auto-{repo_hash}"
    
    def get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()