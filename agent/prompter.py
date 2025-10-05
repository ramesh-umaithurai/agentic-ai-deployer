"""Intelligent prompting system for deployment information"""

import re
import sys
from typing import Optional


class DeploymentPrompter:
    def __init__(self):
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'reset': '\033[0m'
        }
    
    def colorize(self, text, color):
        """Add color to text if terminal supports it"""
        if sys.stdout.isatty():
            return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
        return text
    
    def prompt_repository_url(self) -> str:
        """Prompt for .NET repository URL with validation"""
        print(self.colorize("\n🔗 Repository URL", 'blue'))
        print("   Please provide the Git URL of your .NET solution")
        print("   Supported: GitHub, GitLab, Bitbucket, Azure DevOps")
        
        while True:
            url = input("\n   Enter repository URL: ").strip()
            
            if not url:
                print(self.colorize("   ❌ URL cannot be empty", 'red'))
                continue
            
            # Basic URL validation
            if any(domain in url for domain in ['github.com', 'gitlab.com', 'bitbucket.org', 'dev.azure.com']):
                return url
            else:
                print(self.colorize("   ❌ Please enter a valid Git repository URL", 'red'))
                print("   💡 Example: https://github.com/username/your-dotnet-solution")
    
    def prompt_project_name(self) -> str:
        """Prompt for GCP project name with validation"""
        print(self.colorize("\n🏷️  Project Name", 'blue'))
        print("   This will be used for naming GCP resources")
        print("   Use lowercase letters, numbers, and hyphens only")
        
        while True:
            name = input("\n   Enter project name: ").strip().lower()
            
            if not name:
                print(self.colorize("   ❌ Project name cannot be empty", 'red'))
                continue
            
            # GCP naming validation
            if not re.match(r'^[a-z][a-z0-9-]{2,30}$', name):
                print(self.colorize("   ❌ Invalid project name", 'red'))
                print("   💡 Must start with letter, 3-31 chars, lowercase alphanumeric and hyphens")
                continue
            
            if name.endswith('-') or '--' in name:
                print(self.colorize("   ❌ Cannot end with hyphen or have consecutive hyphens", 'red'))
                continue
                
            return name
    
    def prompt_confirmation(self, message: str) -> bool:
        """Get user confirmation for deployment"""
        print(self.colorize(f"\n❓ {message}", 'yellow'))
        
        while True:
            response = input("   Confirm? (y/N): ").strip().lower()
            
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print(self.colorize("   ❌ Please enter 'y' for yes or 'n' for no", 'red'))
    
    def prompt_cloud_provider(self) -> str:
        """Prompt for cloud provider (currently only GCP supported)"""
        print(self.colorize("\n☁️  Cloud Provider", 'blue'))
        print("   Currently supported: Google Cloud Platform (GCP)")
        return 'gcp'
    
    def prompt_database_type(self) -> str:
        """Prompt for database type (default PostgreSQL)"""
        print(self.colorize("\n🗄️  Database", 'blue'))
        print("   Default: PostgreSQL (Cloud SQL)")
        return 'postgresql'
    
    def display_deployment_summary(self, config: dict, plan: dict):
        """Display a summary of the deployment configuration"""
        print(self.colorize("\n📊 DEPLOYMENT SUMMARY", 'green'))
        print("=" * 40)
        
        print(f"   Repository:    {config['repo_url']}")
        print(f"   Project:       {config['project_name']}")
        print(f"   Cloud:         {config['deployment_type'].upper()}")
        print(f"   Region:        {config['region']}")
        print(f"   Database:      PostgreSQL ({config['database_tier']})")
        print(f"   Services:      {len(plan['services'])} API projects")
        
        print(self.colorize("\n   Services to be created:", 'yellow'))
        for service in plan['services']:
            print(f"     • {service['name']}")