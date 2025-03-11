#!/usr/bin/env python3
"""
Universal deployment script for Pipecat applications.

This script simplifies deploying Pipecat applications to various environments.
"""
import argparse
import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import shutil

# Ensure pipecat is in the path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.pipecat.deployment.config import (
    DeploymentConfig,
    DeploymentEnvironment,
    ResourceRequirements,
    ResourceSize
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Deploy Pipecat applications")
    
    parser.add_argument(
        "environment",
        choices=[e.value for e in DeploymentEnvironment],
        help="Deployment environment"
    )
    
    parser.add_argument(
        "--config",
        "-c",
        help="Path to deployment configuration file"
    )
    
    parser.add_argument(
        "--name",
        "-n",
        help="Name of the deployment"
    )
    
    parser.add_argument(
        "--version",
        "-v",
        default="latest",
        help="Version tag for the deployment"
    )
    
    parser.add_argument(
        "--size",
        choices=[s.value for s in ResourceSize],
        default="medium",
        help="Resource size for the deployment"
    )
    
    parser.add_argument(
        "--replicas",
        type=int,
        default=1,
        help="Number of replicas to deploy"
    )
    
    parser.add_argument(
        "--env-file",
        "-e",
        help="Path to environment file"
    )
    
    parser.add_argument(
        "--domain",
        "-d",
        help="Domain name for the deployment"
    )
    
    parser.add_argument(
        "--no-ssl",
        action="store_true",
        help="Disable SSL"
    )
    
    parser.add_argument(
        "--enable-autoscaling",
        action="store_true",
        help="Enable autoscaling"
    )
    
    parser.add_argument(
        "--output-dir",
        "-o",
        default="deployment",
        help="Directory for generated deployment files"
    )
    
    parser.add_argument(
        "--apply",
        "-a",
        action="store_true",
        help="Apply the deployment immediately"
    )
    
    return parser.parse_args()


def load_env_file(file_path: str) -> Dict[str, str]:
    """Load environment variables from a file."""
    env_vars = {}
    if not file_path or not os.path.exists(file_path):
        return env_vars
        
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars


def create_config(args) -> DeploymentConfig:
    """Create deployment configuration."""
    if args.config:
        return DeploymentConfig.load(args.config)
    
    name = args.name or f"pipecat-{int(time.time())}"
    environment = DeploymentEnvironment(args.environment)
    resources = ResourceRequirements.from_size(args.size)
    
    # Load environment variables
    env_vars = {}
    if args.env_file:
        env_vars = load_env_file(args.env_file)
    
    return DeploymentConfig(
        name=name,
        environment=environment,
        version=args.version,
        resources=resources,
        replicas=args.replicas,
        environment_variables=env_vars,
        domain=args.domain,
        ssl_enabled=not args.no_ssl,
        enable_autoscaling=args.enable_autoscaling
    )


def generate_docker_compose(config: DeploymentConfig, output_dir: Path) -> Path:
    """Generate Docker Compose configuration."""
    os.makedirs(output_dir, exist_ok=True)
    
    compose_file = output_dir / "docker-compose.yml"
    
    # Create Docker Compose configuration
    compose_config = {
        "version": "3",
        "services": {
            "pipecat": {
                "build": {
                    "context": ".",
                    "dockerfile": "docker/Dockerfile"
                },
                "image": f"pipecat:{config.version}",
                "restart": "always",
                "ports": [f"{port}:{port}" for port in config.ports.values()],
                "volumes": [
                    "./data:/app/data",
                    "./cache:/app/cache"
                ],
                "environment": config.environment_variables
            }
        },
        "volumes": {
            "pipecat_data": {},
            "pipecat_cache": {}
        }
    }
    
    # Add healthcheck if specified
    if config.health_check_path:
        compose_config["services"]["pipecat"]["healthcheck"] = {
            "test": f"curl --fail http://localhost:{config.ports.get('api', 8000)}{config.health_check_path} || exit 1",
            "interval": "30s",
            "timeout": "10s",
            "retries": 3
        }
    
    # Write Docker Compose file
    with open(compose_file, "w") as f:
        yaml.dump(compose_config, f, default_flow_style=False)
    
    print(f"Generated Docker Compose file: {compose_file}")
    return compose_file


def generate_kubernetes(config: DeploymentConfig, output_dir: Path) -> Path:
    """Generate Kubernetes manifests."""
    k8s_dir = output_dir / "kubernetes"
    os.makedirs(k8s_dir, exist_ok=True)
    
    # Create deployment manifest
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": config.name
        },
        "spec": {
            "replicas": config.replicas,
            "selector": {
                "matchLabels": {
                    "app": config.name
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": config.name
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "pipecat",
                            "image": f"pipecat:{config.version}",
                            "ports": [
                                {"containerPort": port} for port in config.ports.values()
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": config.resources.cpu,
                                    "memory": config.resources.memory
                                },
                                "limits": {
                                    "cpu": str(float(config.resources.cpu) * 2),
                                    "memory": config.resources.memory
                                }
                            },
                            "env": [
                                {"name": k, "value": v} 
                                for k, v in config.environment_variables.items()
                            ],
                            "volumeMounts": [
                                {
                                    "name": "cache-volume",
                                    "mountPath": "/app/cache"
                                }
                            ]
                        }
                    ],
                    "volumes": [
                        {
                            "name": "cache-volume",
                            "persistentVolumeClaim": {
                                "claimName": f"{config.name}-cache-pvc"
                            }
                        }
                    ]
                }
            }
        }
    }
    
    # Add readiness and liveness probes
    if config.health_check_path:
        deployment["spec"]["template"]["spec"]["containers"][0]["livenessProbe"] = {
            "httpGet": {
                "path": config.health_check_path,
                "port": config.ports.get("api", 8000)
            },
            "initialDelaySeconds": 30,
            "periodSeconds": 10
        }
    
    if config.readiness_check_path:
        deployment["spec"]["template"]["spec"]["containers"][0]["readinessProbe"] = {
            "httpGet": {
                "path": config.readiness_check_path,
                "port": config.ports.get("api", 8000)
            },
            "initialDelaySeconds": 10,
            "periodSeconds": 5
        }
    
    # Create service manifest
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": config.name
        },
        "spec": {
            "selector": {
                "app": config.name
            },
            "ports": [
                {
                    "name": name,
                    "port": port,
                    "targetPort": port
                } for name, port in config.ports.items()
            ],
            "type": "ClusterIP"
        }
    }
    
    # Create PVC for cache
    pvc = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": f"{config.name}-cache-pvc"
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": config.resources.disk
                }
            }
        }
    }
    
    # Create ingress if domain is specified
    ingress = None
    if config.domain:
        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": config.name,
                "annotations": {
                    "kubernetes.io/ingress.class": "nginx"
                }
            },
            "spec": {
                "rules": [
                    {
                        "host": config.domain,
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": config.name,
                                            "port": {
                                                "number": config.ports.get("api", 8000)
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        # Add TLS if SSL is enabled
        if config.ssl_enabled:
            ingress["metadata"]["annotations"]["cert-manager.io/cluster-issuer"] = "letsencrypt"
            ingress["spec"]["tls"] = [
                {
                    "hosts": [config.domain],
                    "secretName": f"{config.name}-tls"
                }
            ]
    
    # Create autoscaling configuration if enabled
    hpa = None
    if config.enable_autoscaling:
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": config.name
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": config.name
                },
                "minReplicas": config.min_replicas,
                "maxReplicas": config.max_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": config.target_cpu_utilization
                            }
                        }
                    }
                ]
            }
        }
    
    # Write manifests to files
    with open(k8s_dir / "deployment.yaml", "w") as f:
        yaml.dump(deployment, f, default_flow_style=False)
    
    with open(k8s_dir / "service.yaml", "w") as f:
        yaml.dump(service, f, default_flow_style=False)
    
    with open(k8s_dir / "pvc.yaml", "w") as f:
        yaml.dump(pvc, f, default_flow_style=False)
    
    if ingress:
        with open(k8s_dir / "ingress.yaml", "w") as f:
            yaml.dump(ingress, f, default_flow_style=False)
    
    if hpa:
        with open(k8s_dir / "hpa.yaml", "w") as f:
            yaml.dump(hpa, f, default_flow_style=False)
    
    # Create a kustomization file
    kustomization = {
        "apiVersion": "kustomize.config.k8s.io/v1beta1",
        "kind": "Kustomization",
        "resources": [
            "deployment.yaml",
            "service.yaml",
            "pvc.yaml"
        ]
    }
    
    if ingress:
        kustomization["resources"].append("ingress.yaml")
    
    if hpa:
        kustomization["resources"].append("hpa.yaml")
    
    with open(k8s_dir / "kustomization.yaml", "w") as f:
        yaml.dump(kustomization, f, default_flow_style=False)
    
    print(f"Generated Kubernetes manifests in: {k8s_dir}")
    return k8s_dir


def generate_cloud_formation(config: DeploymentConfig, output_dir: Path) -> Path:
    """Generate AWS CloudFormation template."""
    aws_dir = output_dir / "aws"
    os.makedirs(aws_dir, exist_ok=True)
    
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": f"Pipecat deployment: {config.name}",
        "Parameters": {
            "ContainerImage": {
                "Type": "String",
                "Default": f"pipecat:{config.version}",
                "Description": "Docker image for the container"
            },
            "ContainerPort": {
                "Type": "Number",
                "Default": config.ports.get("api", 8000),
                "Description": "Port on which the application listens"
            }
        },
        "Resources": {
            "PipecatCluster": {
                "Type": "AWS::ECS::Cluster",
                "Properties": {
                    "ClusterName": f"{config.name}-cluster"
                }
            },
            "PipecatTaskDefinition": {
                "Type": "AWS::ECS::TaskDefinition",
                "Properties": {
                    "Family": config.name,
                    "RequiresCompatibilities": ["FARGATE"],
                    "NetworkMode": "awsvpc",
                    "ExecutionRoleArn": {"Fn::GetAtt": ["PipecatTaskExecutionRole", "Arn"]},
                    "Cpu": str(int(float(config.resources.cpu) * 1024)),  # Convert CPU units
                    "Memory": str(int(config.resources.memory.replace("Gi", "")) * 1024),  # Convert to MB
                    "ContainerDefinitions": [
                        {
                            "Name": config.name,
                            "Image": {"Ref": "ContainerImage"},
                            "Essential": True,
                            "PortMappings": [
                                {
                                    "ContainerPort": port,
                                    "HostPort": port,
                                    "Protocol": "tcp"
                                } for port in config.ports.values()
                            ],
                            "Environment": [
                                {
                                    "Name": k,
                                    "Value": v
                                } for k, v in config.environment_variables.items()
                            ],
                            "LogConfiguration": {
                                "LogDriver": "awslogs",
                                "Options": {
                                    "awslogs-group": {"Ref": "PipecatLogGroup"},
                                    "awslogs-region": {"Ref": "AWS::Region"},
                                    "awslogs-stream-prefix": "ecs"
                                }
                            }
                        }
                    ]
                }
            },
            "PipecatService": {
                "Type": "AWS::ECS::Service",
                "Properties": {
                    "Cluster": {"Ref": "PipecatCluster"},
                    "TaskDefinition": {"Ref": "PipecatTaskDefinition"},
                    "LaunchType": "FARGATE",
                    "DesiredCount": config.replicas,
                    "NetworkConfiguration": {
                        "AwsvpcConfiguration": {
                            "AssignPublicIp": "ENABLED",
                            "SecurityGroups": [{"Ref": "PipecatSecurityGroup"}],
                            "Subnets": {"Fn::Split": [",", {"Ref": "SubnetIds"}]}
                        }
                    },
                    "LoadBalancers": [
                        {
                            "ContainerName": config.name,
                            "ContainerPort": config.ports.get("api", 8000),
                            "TargetGroupArn": {"Ref": "PipecatTargetGroup"}
                        }
                    ]
                },
                "DependsOn": ["PipecatLoadBalancerListener"]
            },
            # Additional resources omitted for brevity
        }
    }
    
    # Write CloudFormation template
    cf_path = aws_dir / "cloudformation.json"
    with open(cf_path, "w") as f:
        json.dump(template, f, indent=2)
    
    print(f"Generated AWS CloudFormation template: {cf_path}")
    return cf_path


def apply_deployment(config: DeploymentConfig, output_dir: Path) -> bool:
    """Apply the generated deployment configuration."""
    if config.environment == DeploymentEnvironment.DOCKER:
        # Run Docker Compose deployment
        compose_file = output_dir / "docker-compose.yml"
        if not os.path.exists(compose_file):
            print(f"Error: Docker Compose file not found at {compose_file}")
            return False
        
        try:
            subprocess.run(
                ["docker-compose", "-f", str(compose_file), "up", "-d"],
                check=True
            )
            print(f"Successfully deployed {config.name} using Docker Compose")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error deploying with Docker Compose: {e}")
            return False
            
    elif config.environment == DeploymentEnvironment.KUBERNETES:
        # Apply Kubernetes manifests
        k8s_dir = output_dir / "kubernetes"
        if not os.path.exists(k8s_dir):
            print(f"Error: Kubernetes manifests not found in {k8s_dir}")
            return False
        
        try:
            subprocess.run(
                ["kubectl", "apply", "-k", str(k8s_dir)],
                check=True
            )
            print(f"Successfully applied Kubernetes manifests for {config.name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error applying Kubernetes manifests: {e}")
            return False
            
    elif config.environment == DeploymentEnvironment.AWS:
        # Deploy using AWS CloudFormation
        cf_path = output_dir / "aws" / "cloudformation.json"
        if not os.path.exists(cf_path):
            print(f"Error: CloudFormation template not found at {cf_path}")
            return False
        
        try:
            stack_name = f"pipecat-{config.name}"
            subprocess.run(
                [
                    "aws", "cloudformation", "deploy",
                    "--template-file", str(cf_path),
                    "--stack-name", stack_name,
                    "--capabilities", "CAPABILITY_IAM",
                    "--parameter-overrides",
                    f"ContainerImage=pipecat:{config.version}"
                ],
                check=True
            )
            print(f"Successfully deployed {config.name} to AWS")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error deploying to AWS: {e}")
            return False
    
    else:
        print(f"Deployment to {config.environment.value} is not implemented yet")
        return False


def main():
    """Main function."""
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is required for this script.")
        print("Install it with: pip install pyyaml")
        sys.exit(1)
        
    args = parse_args()
    output_dir = Path(args.output_dir)
    
    print(f"Deploying Pipecat to {args.environment}...")
    
    # Create deployment configuration
    config = create_config(args)
    
    # Save configuration
    os.makedirs(output_dir, exist_ok=True)
    config_path = output_dir / "config.json"
    config.save(config_path)
    print(f"Saved deployment configuration to: {config_path}")
    
    # Generate deployment files
    if config.environment == DeploymentEnvironment.DOCKER:
        generate_docker_compose(config, output_dir)
    elif config.environment == DeploymentEnvironment.KUBERNETES:
        generate_kubernetes(config, output_dir)
    elif config.environment == DeploymentEnvironment.AWS:
        generate_cloud_formation(config, output_dir)
    else:
        print(f"Generation for {config.environment.value} is not implemented yet")
    
    # Apply deployment if requested
    if args.apply:
        print("Applying deployment...")
        apply_deployment(config, output_dir)
    
    print(f"Deployment files generated in: {output_dir}")
    print("To apply the deployment manually, follow the instructions in the documentation.")


if __name__ == "__main__":
    main()
