"""
Autonomous Decision Engine for Deployment Planning
Makes optimal deployment decisions based on constraints and patterns
"""

from typing import Dict, List
import json


class DecisionEngine:
    def __init__(self):
        self.decision_rules = self.load_decision_rules()
    
    def load_decision_rules(self) -> Dict:
        """Load decision rules for autonomous deployment"""
        return {
            "cost_optimized": {
                "cloud_provider": "gcp",  # GCP often has better free tiers
                "database_tier": "db-f1-micro",
                "compute_tier": "lowest",
                "scaling": "conservative"
            },
            "performance": {
                "cloud_provider": "aws",  # AWS often has better performance
                "database_tier": "db-n1-standard-1",
                "compute_tier": "balanced",
                "scaling": "aggressive"
            },
            "balanced": {
                "cloud_provider": "gcp",
                "database_tier": "db-g1-small",
                "compute_tier": "standard",
                "scaling": "moderate"
            }
        }
    
    async def generate_optimal_plan(self, tech_stack: Dict, strategy: Dict, config: Dict) -> Dict:
        """Generate optimal deployment plan based on strategy"""
        strategy_type = config.get('deployment_strategy', 'cost_optimized')
        rules = self.decision_rules.get(strategy_type, self.decision_rules['cost_optimized'])
        
        plan = {
            "infrastructure": self.determine_infrastructure(tech_stack, rules),
            "services": self.determine_services(tech_stack, rules),
            "database": self.determine_database(tech_stack, rules),
            "monitoring": self.determine_monitoring(tech_stack, rules),
            "scaling": self.determine_scaling(tech_stack, rules)
        }
        
        # Apply strategy-specific optimizations
        plan = self.apply_strategy_optimizations(plan, strategy)
        
        return plan
    
    def determine_infrastructure(self, tech_stack: Dict, rules: Dict) -> Dict:
        """Determine infrastructure requirements"""
        api_count = len(tech_stack.get('dotnet', {}).get('api_projects', []))
        
        return {
            "cloud_provider": rules["cloud_provider"],
            "compute_service": "cloud_run",  # Default to serverless
            "region": "us-central1",
            "service_count": api_count
        }
    
    def determine_services(self, tech_stack: Dict, rules: Dict) -> List[Dict]:
        """Determine service configurations"""
        services = []
        api_projects = tech_stack.get('dotnet', {}).get('api_projects', [])
        
        for project in api_projects:
            service = {
                "name": project['name'].replace('.', '-').lower(),
                "cpu": self.determine_cpu_allocation(rules),
                "memory": self.determine_memory_allocation(rules),
                "max_instances": self.determine_max_instances(rules),
                "min_instances": 0 if rules['scaling'] == 'conservative' else 1
            }
            services.append(service)
        
        return services
    
    def determine_cpu_allocation(self, rules: Dict) -> str:
        """Determine CPU allocation based on strategy"""
        cpu_map = {
            "lowest": "1",
            "standard": "2", 
            "balanced": "2",
            "high": "4"
        }
        return cpu_map.get(rules["compute_tier"], "1")
    
    def determine_memory_allocation(self, rules: Dict) -> str:
        """Determine memory allocation based on strategy"""
        memory_map = {
            "lowest": "1Gi",
            "standard": "2Gi",
            "balanced": "4Gi", 
            "high": "8Gi"
        }
        return memory_map.get(rules["compute_tier"], "2Gi")
    
    def determine_max_instances(self, rules: Dict) -> int:
        """Determine maximum instances based on scaling strategy"""
        scaling_map = {
            "conservative": 5,
            "moderate": 10,
            "aggressive": 20
        }
        return scaling_map.get(rules["scaling"], 10)
    
    def determine_database(self, tech_stack: Dict, rules: Dict) -> Dict:
        """Determine database configuration"""
        return {
            "type": "postgresql",
            "tier": rules["database_tier"],
            "backup_enabled": True,
            "high_availability": rules["scaling"] == "aggressive"
        }
    
    def determine_monitoring(self, tech_stack: Dict, rules: Dict) -> Dict:
        """Determine monitoring configuration"""
        return {
            "enabled": True,
            "alerts": True,
            "logging": True,
            "metrics": ["cpu", "memory", "requests", "latency"]
        }
    
    def determine_scaling(self, tech_stack: Dict, rules: Dict) -> Dict:
        """Determine scaling configuration"""
        return {
            "auto_scaling": True,
            "min_instances": 0 if rules["scaling"] == "conservative" else 1,
            "max_instances": self.determine_max_instances(rules),
            "target_cpu_utilization": 60
        }
    
    def apply_strategy_optimizations(self, plan: Dict, strategy: Dict) -> Dict:
        """Apply strategy-specific optimizations"""
        # Apply any custom optimizations from Ollama's strategy
        if "optimizations" in strategy:
            for key, value in strategy["optimizations"].items():
                if key in plan:
                    plan[key].update(value)
        
        return plan