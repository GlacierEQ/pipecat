"""
Container deployment utilities for Pipecat applications.
"""
from dataclasses import dataclass, field
import os
import subprocess
from typing import List, Dict, Optional


@dataclass
class DockerConfig:
    """Configuration for Docker container builds."""
    
    base_image: str = "python:3.11-slim"
    working_dir: str = "/app"
    install_dev_deps: bool = False
    extra_packages: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    
    def to_dockerfile(self) -> str:
        """Generate a Dockerfile from this configuration."""
        lines = [
            f"FROM {self.base_image}",
            "",
            f"WORKDIR {self.working_dir}",
            "",
            "# Set environment variables",
            "ENV PYTHONDONTWRITEBYTECODE=1 \\",
            "    PYTHONUNBUFFERED=1 \\",
            f"    PYTHONPATH={self.working_dir}"
        ]
        
        # Add environment variables
        for key, value in self.environment.items():
            lines.append(f"ENV {key}={value}")
        
        # System dependencies
        if self.extra_packages:
            lines.extend([
                "",
                "# Install system dependencies",
                "RUN apt-get update && apt-get install -y --no-install-recommends \\",
                "    " + " \\\n    ".join(self.extra_packages) + " \\",
                "    && apt-get clean \\",
                "    && rm -rf /var/lib/apt/lists/*"
            ])
        
        # Project files
        lines.extend([
            "",
            "# Copy project files",
            f"COPY . {self.working_dir}/",
            ""
        ])
        
        # Dependencies
        deps_target = "[all]" if self.install_dev_deps else ""
        lines.extend([
            "# Install dependencies",
            f'RUN pip install --no-cache-dir -e ".{deps_target}"',
            "",
            "# Default command",
            'CMD ["python", "-m", "pipecat.cli"]'
        ])
        
        return "\n".join(lines)


class DockerBuilder:
    """Utility for building Docker containers from Pipecat applications."""
    
    def __init__(self, config: DockerConfig = None):
        self.config = config or DockerConfig()
    
    def generate_dockerfile(self, output_path: str) -> None:
        """Generate a Dockerfile at the specified path."""
        dockerfile_content = self.config.to_dockerfile()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(dockerfile_content)
    
    def build_image(self, 
                    tag: str, 
                    context_path: str = ".", 
                    dockerfile_path: Optional[str] = None) -> bool:
        """Build a Docker image."""
        cmd = ["docker", "build", "-t", tag]
        
        if dockerfile_path:
            cmd.extend(["-f", dockerfile_path])
        
        cmd.append(context_path)
        
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error building Docker image: {e}")
            return False
