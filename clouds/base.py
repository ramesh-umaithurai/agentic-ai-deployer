"""Base classes for cloud providers"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any  # Add missing imports


class CloudProvider(ABC):
    """Abstract base class for cloud providers"""
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with cloud provider"""
        pass
    
    @abstractmethod
    async def provision_infrastructure(self, config: Dict) -> Dict:
        """Provision cloud infrastructure"""
        pass
    
    @abstractmethod
    async def deploy_services(self, services: List[Dict]) -> Dict:  # Fixed: List imported now
        """Deploy application services"""
        pass
    
    @abstractmethod
    async def setup_monitoring(self, config: Dict) -> Dict:
        """Setup monitoring and alerting"""
        pass


class DatabaseProvider(ABC):
    """Abstract base class for database providers"""
    
    @abstractmethod
    async def create_instance(self, config: Dict) -> Dict:
        """Create database instance"""
        pass
    
    @abstractmethod
    async def create_database(self, config: Dict) -> Dict:
        """Create database"""
        pass
    
    @abstractmethod
    async def create_user(self, config: Dict) -> Dict:
        """Create database user"""
        pass