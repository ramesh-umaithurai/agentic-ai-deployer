"""
Ollama Integration for Autonomous Decision Making
Uses local LLM for natural language processing and reasoning
"""

import aiohttp
import json
import asyncio
import re
from typing import Dict, List, Optional
from pathlib import Path


class OllamaManager:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama2"
        self.session = None
    
    async def ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def chat_completion(self, messages: List[Dict], model: str = None) -> Dict:
        """Send chat completion request to Ollama"""
        await self.ensure_session()
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "top_k": 40
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    raise Exception(f"Ollama API error: {response.status}")
        except Exception as e:
            print(f"⚠️  Ollama connection failed: {e}")
            return {
                "message": {
                    "content": '{"analysis": "Ollama not available, using fallback logic"}'
                }
            }
    
    async def analyze_deployment_intent(self, user_input: str) -> Dict:
        """Analyze user's deployment intent using Ollama"""
        # First try to extract URL with improved pattern matching that handles dots
        repo_url = self.extract_repository_url(user_input)
        
        if repo_url:
            return {
                "repository_url": repo_url,
                "cloud_provider": "gcp",
                "database_type": "postgresql", 
                "budget_limit": 100
            }
        
        # If no URL found and Ollama is available, use it
        system_prompt = """You are an AI deployment expert. Analyze the user's request and extract:
        1. Repository URL (GitHub, GitLab, etc.)
        2. Desired cloud provider (GCP, AWS, Azure)
        3. Database requirements
        4. Budget constraints
        5. Performance requirements
        6. Any specific configuration requests

        Return JSON format with extracted information."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = await self.chat_completion(messages)
        content = response["message"]["content"]
        
        # Extract JSON from response
        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: simple pattern matching
        return self.fallback_intent_analysis(user_input)
    
    def extract_repository_url(self, text: str) -> Optional[str]:
        """Extract repository URL from text using pattern matching - FIXED TO HANDLE DOTS"""
        # Improved patterns that handle dots in repository names
        patterns = [
            r'https?://(?:www\.)?github\.com/[\w\-\.,]+/[\w\-\.,]+',  # Added dots to character class
            r'https?://(?:www\.)?gitlab\.com/[\w\-\.,]+/[\w\-\.,]+',  # Added dots to character class
            r'https?://(?:www\.)?bitbucket\.org/[\w\-\.,]+/[\w\-\.,]+',  # Added dots to character class
            r'github\.com/[\w\-\.,]+/[\w\-\.,]+',  # Added dots to character class
            r'gitlab\.com/[\w\-\.,]+/[\w\-\.,]+',  # Added dots to character class
            r'bitbucket\.org/[\w\-\.,]+/[\w\-\.,]+'  # Added dots to character class
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                url = match.group()
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
        
        return None
    
    def fallback_intent_analysis(self, user_input: str) -> Dict:
        """Fallback intent analysis without Ollama"""
        intent = {
            "repository_url": None,
            "cloud_provider": "gcp",
            "database_type": "postgresql",
            "budget_limit": 100,
            "requirements": []
        }
        
        # Simple pattern matching with improved URL extraction
        url = self.extract_repository_url(user_input)
        if url:
            intent["repository_url"] = url
        
        # Cloud provider detection
        if 'aws' in user_input.lower():
            intent["cloud_provider"] = "aws"
        elif 'azure' in user_input.lower():
            intent["cloud_provider"] = "azure"
        
        # Budget detection
        budget_pattern = r'\$(\d+)'
        budget_match = re.search(budget_pattern, user_input)
        if budget_match:
            intent["budget_limit"] = int(budget_match.group(1))
        
        return intent
    
    async def analyze_code_structure(self, repo_path: Path) -> Dict:
        """Analyze code structure using Ollama"""
        # For now, return basic analysis without Ollama
        return {
            "analysis": "Basic code structure analysis",
            "recommendations": ["Use Cloud Run for .NET APIs", "Configure PostgreSQL database"]
        }
    
    async def determine_deployment_strategy(self, context: Dict) -> Dict:
        """Determine optimal deployment strategy using Ollama"""
        # Fallback strategy without Ollama
        return {
            "cloud_service": "cloud_run",
            "database_tier": "db-f1-micro", 
            "scaling": "auto",
            "optimization": "cost_effective"
        }
    
    async def suggest_cost_optimizations(self, deployment_plan: Dict, budget: float) -> Dict:
        """Suggest cost optimizations using Ollama"""
        return {
            "suggestions": "Consider using smaller instance types and enabling auto-scaling",
            "can_optimize": True
        }
    
    async def suggest_error_recovery(self, error: str, context: Dict = None) -> Dict:
        """Suggest error recovery strategies using Ollama"""
        if "repository not found" in error.lower() or "404" in error.lower():
            return {
                "strategy": "Check the repository URL and ensure it exists and is accessible",
                "can_recover": False,
                "suggestion": "Please verify the repository URL and try again"
            }
        
        return {
            "strategy": "Check cloud provider quotas and authentication",
            "can_recover": True
        }
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()