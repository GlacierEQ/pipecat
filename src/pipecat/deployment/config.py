"""
Deployment configuration for Pipecat applications.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union
import os
import json
from pathlib import Path


class DeploymentEnvironment(str, Enum):
    """Supported deployment environments."""
    
    LOCAL = "local"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    FLY_IO = "fly_io"
    HEROKU = "heroku"
    DIGITAL_OCEAN = "digital_ocean"
    CUSTOM = "custom"


class ResourceSize(str, Enum):
    """Resource size options for deployments."""
    
    SMALL = "small"      # 1 CPU, 1GB RAM
    MEDIUM = "medium"    # 2 CPU, 2GB RAM
    LARGE = "large"      # 4 CPU, 8GB RAM
    XLARGE = "xlarge"    # 8 CPU, 16GB RAM
    CUSTOM = "custom"    # Custom resource configuration


@dataclass
class ResourceRequirements:
    """Resource requirements for a deployment."""
    
    cpu: str = "1"
    memory: str = "1Gi"
    disk: str = "10Gi"
    gpu: Optional[str] = None
    
    @classmethod
    def from_size(cls, size: Union[ResourceSize, str]) -> "ResourceRequirements":
        """Create resource requirements based on predefined size."""
        if isinstance(size, str):
            size = ResourceSize(size)
            
        if size == ResourceSize.SMALL:
            return cls(cpu="1", memory="1Gi")
        elif size == ResourceSize.MEDIUM:
            return cls(cpu="2", memory="2Gi")
        elif size == ResourceSize.LARGE:
            return cls(cpu="4", memory="8Gi")
        elif size == ResourceSize.XLARGE:
            return cls(cpu="8", memory="16Gi")
        else:  # CUSTOM
            return cls()


@dataclass
class DeploymentConfig:
    """Configuration for deploying Pipecat applications."""
    
    name: str
    environment: DeploymentEnvironment
    version: str = "latest"
    resources: ResourceRequirements = field(default_factory=ResourceRequirements)
    replicas: int = 1
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    ports: Dict[str, int] = field(default_factory=lambda: {"api": 8000, "dashboard": 8080})
    health_check_path: str = "/health"
    readiness_check_path: str = "/readiness"
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    domain: Optional[str] = None
    ssl_enabled: bool = True
    enable_monitoring: bool = True
    enable_autoscaling: bool = False
    min_replicas: int = 1
    max_replicas: int = 5
    target_cpu_utilization: int = 80
    custom_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        return {
            "name": self.name,
            "environment": self.environment.value,
            "version": self.version,
            "resources": {
                "cpu": self.resources.cpu,
                "memory": self.resources.memory,
                "disk": self.resources.disk,
                "gpu": self.resources.gpu
            },
            "replicas": self.replicas,
            "environment_variables": self.environment_variables,
            "secrets": self.secrets,
            "ports": self.ports,
            "health_check_path": self.health_check_path,
            "readiness_check_path": self.readiness_check_path,
            "command": self.command,
            "args": self.args,
            "domain": self.domain,
            "ssl_enabled": self.ssl_enabled,
            "enable_monitoring": self.enable_monitoring,
            "enable_autoscaling": self.enable_autoscaling,
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
            "target_cpu_utilization": self.target_cpu_utilization,
            "custom_config": self.custom_config
        }
    
    def save(self, file_path: Union[str, Path]) -> None:
        """Save configuration to a file."""
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "DeploymentConfig":
        """Load configuration from a file."""
        with open(file_path, "r") as f:
            data = json.load(f)
        
        # Convert environment from string to enum
        data["environment"] = DeploymentEnvironment(data["environment"])
        
        # Extract resource requirements
        resources = data.pop("resources", {})
        data["resources"] = ResourceRequirements(**resources)
        
        return cls(**data)
