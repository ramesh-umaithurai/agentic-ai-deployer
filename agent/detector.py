"""Technology stack detection for .NET solutions"""

import os
import re
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET


class TechStackDetector:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "agentic-ai-deployer"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def clone_repository(self, repo_url: str) -> Path:
        """Clone repository to temporary directory - FIXED URL HANDLING"""
        # Extract repository name properly, handling dots in the name
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        
        # Get the last part of the URL, preserving dots
        repo_name = repo_url.split('/')[-1]
        
        # Clean up any invalid characters for directory names
        repo_name = re.sub(r'[<>:"/\\|?*]', '-', repo_name)
        
        repo_path = self.temp_dir / repo_name
        
        print(f"🔗 Cloning repository: {repo_url}")
        print(f"📁 Local path: {repo_path}")
        
        if repo_path.exists():
            # Update existing clone
            print("📥 Updating existing repository...")
            subprocess.run(['git', 'pull'], cwd=repo_path, check=True)
        else:
            # Clone fresh
            print("📥 Cloning repository...")
            try:
                subprocess.run(['git', 'clone', repo_url, str(repo_path)], check=True)
                print(f"✅ Repository cloned successfully to {repo_path}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to clone repository: {e}")
                # Check if it's a 404 error
                if "Repository not found" in str(e):
                    raise Exception(f"Repository not found: {repo_url}. Please check the URL and repository accessibility.")
                else:
                    raise Exception(f"Git clone failed: {e}")
        
        return repo_path
    
    def detect_tech_stack(self, repo_path: Path) -> Dict:
        """Detect complete technology stack"""
        print("🔍 Detecting technology stack...")
        
        stack = {
            'dotnet': self.detect_dotnet_stack(repo_path),
            'docker': self.detect_docker_stack(repo_path),
            'database': self.detect_database_stack(repo_path),
            'ci_cd': self.detect_ci_cd_files(repo_path)
        }
        
        print("✅ Tech stack detection completed")
        return stack
    
    def detect_dotnet_stack(self, repo_path: Path) -> Dict:
        """Detect .NET specific stack information"""
        print("   🔍 Detecting .NET stack...")
        
        dotnet_info = {
            'framework': 'dotnet',
            'version': self.get_dotnet_version(repo_path),
            'api_projects': self.find_api_projects(repo_path),
            'projects': self.find_csproj_files(repo_path),
            'solution_files': self.find_solution_files(repo_path)
        }
        
        print(f"   ✅ Found {len(dotnet_info['api_projects'])} API projects")
        return dotnet_info
    
    def get_dotnet_version(self, repo_path: Path) -> str:
        """Extract .NET version from project files"""
        csproj_files = list(repo_path.rglob("*.csproj"))
        
        for csproj in csproj_files[:3]:  # Check first few projects
            try:
                tree = ET.parse(csproj)
                root = tree.getroot()
                
                # Look for TargetFramework
                for elem in root.iter():
                    if 'TargetFramework' in elem.tag:
                        version = elem.text
                        if version:
                            # Extract version number (e.g., "net8.0" -> "8.0")
                            version = version.replace('net', '').lower()
                            return version
            except Exception as e:
                print(f"      ⚠️ Could not parse {csproj}: {e}")
                continue
        
        return "8.0"  # Default to latest LTS
    
    def find_api_projects(self, repo_path: Path) -> List[Dict]:
        """Find API projects in the solution"""
        api_projects = []
        csproj_files = list(repo_path.rglob("*.csproj"))
        
        print(f"   📁 Scanning {len(csproj_files)} .csproj files...")
        
        for csproj in csproj_files:
            project_info = self.analyze_project_file(csproj)
            if project_info.get('is_web_project', False):
                api_projects.append(project_info)
                print(f"      ✅ Found API project: {project_info['name']}")
        
        return api_projects
    
    def analyze_project_file(self, csproj_path: Path) -> Dict:
        """Analyze a .csproj file for project type"""
        project_info = {
            'name': csproj_path.stem,
            'path': str(csproj_path.parent),
            'relative_path': str(csproj_path.relative_to(csproj_path.parent.parent.parent)) if csproj_path.parent.parent.parent.exists() else str(csproj_path),
            'is_web_project': False,
            'is_api_project': False,
            'dockerfile': self.find_dockerfile_for_project(csproj_path.parent)
        }
        
        try:
            content = csproj_path.read_text(encoding='utf-8', errors='ignore')
            
            # Check for web SDK or web references
            if any(web_ref in content for web_ref in [
                'Microsoft.NET.Sdk.Web',
                'Microsoft.AspNetCore',
                'WebApplication',
                'Program.cs'  # Also check for Program.cs in the same directory
            ]):
                project_info['is_web_project'] = True
                project_info['is_api_project'] = True
                
            # Check for Controllers (MVC/Web API)
            controllers_dir = csproj_path.parent / "Controllers"
            if controllers_dir.exists():
                project_info['is_api_project'] = True
                    
        except Exception as e:
            print(f"      ⚠️ Could not analyze {csproj_path}: {e}")
        
        return project_info
    
    def find_csproj_files(self, repo_path: Path) -> List[str]:
        """Find all .csproj files"""
        return [str(p.relative_to(repo_path)) for p in repo_path.rglob("*.csproj")]
    
    def find_solution_files(self, repo_path: Path) -> List[str]:
        """Find all .sln files"""
        return [str(p.relative_to(repo_path)) for p in repo_path.rglob("*.sln")]
    
    def detect_docker_stack(self, repo_path: Path) -> Dict:
        """Detect Docker configuration"""
        print("   🔍 Detecting Docker configuration...")
        
        dockerfiles = self.find_dockerfiles(repo_path)
        compose_files = self.find_docker_compose_files(repo_path)
        
        docker_info = {
            'dockerfiles': dockerfiles,
            'compose_files': compose_files,
            'multi_project': len(dockerfiles) > 1
        }
        
        print(f"   ✅ Found {len(dockerfiles)} Dockerfile(s)")
        return docker_info
    
    def find_dockerfiles(self, repo_path: Path) -> List[Dict]:
        """Find all Dockerfiles"""
        dockerfiles = []
        for dockerfile in repo_path.rglob("Dockerfile*"):
            dockerfiles.append({
                'path': str(dockerfile.relative_to(repo_path)),
                'project': self.find_project_for_dockerfile(dockerfile)
            })
        return dockerfiles
    
    def find_dockerfile_for_project(self, project_path: Path) -> Optional[str]:
        """Find Dockerfile for a specific project"""
        dockerfiles = list(project_path.glob("Dockerfile*"))
        if dockerfiles:
            return str(dockerfiles[0].relative_to(project_path.parent.parent)) if project_path.parent.parent.exists() else str(dockerfiles[0])
        return None
    
    def find_project_for_dockerfile(self, dockerfile_path: Path) -> Optional[str]:
        """Find project for a Dockerfile"""
        # Look for .csproj files in the same directory
        csproj_files = list(dockerfile_path.parent.glob("*.csproj"))
        if csproj_files:
            return csproj_files[0].stem
        return None
    
    def find_docker_compose_files(self, repo_path: Path) -> List[str]:
        """Find docker-compose files"""
        return [str(p.relative_to(repo_path)) for p in repo_path.rglob("docker-compose*.yml")]
    
    def detect_database_stack(self, repo_path: Path) -> Dict:
        """Detect database dependencies"""
        print("   🔍 Detecting database dependencies...")
        
        db_type = self.detect_database_type(repo_path)
        db_info = {
            'type': db_type,
            'connection_strings': self.find_connection_strings(repo_path),
            'migrations': self.find_migration_files(repo_path)
        }
        
        print(f"   ✅ Database type: {db_type}")
        return db_info
    
    def detect_database_type(self, repo_path: Path) -> str:
        """Detect database type from project files"""
        # Check for common database packages
        potential_files = list(repo_path.rglob("*.csproj")) + list(repo_path.rglob("appsettings*.json"))
        
        for file_path in potential_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore').lower()
                
                if 'npgsql' in content or 'postgresql' in content or 'npgsql' in content:
                    return 'postgresql'
                elif 'microsoft.entityframeworkcore.sqlserver' in content:
                    return 'sqlserver'
                elif 'mysql' in content or 'mariadb' in content:
                    return 'mysql'
                elif 'sqlite' in content:
                    return 'sqlite'
            except:
                continue
        
        return 'postgresql'  # Default to PostgreSQL
    
    def find_connection_strings(self, repo_path: Path) -> List[str]:
        """Find database connection strings"""
        connection_strings = []
        config_files = repo_path.rglob("appsettings*.json")
        
        for config_file in config_files:
            try:
                content = config_file.read_text(encoding='utf-8', errors='ignore')
                # Simple regex to find connection strings
                matches = re.findall(r'connectionstring["\']?\s*:\s*["\']([^"\']+)', content, re.IGNORECASE)
                connection_strings.extend(matches)
            except:
                continue
        
        return connection_strings
    
    def find_migration_files(self, repo_path: Path) -> List[str]:
        """Find Entity Framework migration files"""
        migrations = []
        for migration_dir in repo_path.rglob("Migrations"):
            if any(migration_dir.glob("*.cs")):
                migrations.append(str(migration_dir.relative_to(repo_path)))
        return migrations
    
    def detect_ci_cd_files(self, repo_path: Path) -> Dict:
        """Detect CI/CD configuration files"""
        ci_files = {}
        
        # GitHub Actions
        github_actions = list((repo_path / ".github" / "workflows").rglob("*.yml")) if (repo_path / ".github" / "workflows").exists() else []
        ci_files['github_actions'] = [str(f.relative_to(repo_path)) for f in github_actions]
        
        # Azure Pipelines
        azure_pipelines = list(repo_path.glob("azure-pipelines.yml"))
        ci_files['azure_pipelines'] = [str(f.relative_to(repo_path)) for f in azure_pipelines]
        
        # GitLab CI
        gitlab_ci = list(repo_path.glob(".gitlab-ci.yml"))
        ci_files['gitlab_ci'] = [str(f.relative_to(repo_path)) for f in gitlab_ci]
        
        return ci_files