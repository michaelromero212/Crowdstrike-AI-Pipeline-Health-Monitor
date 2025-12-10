"""
Multi-cloud metrics ingestor for CrowdStrike AI Pipeline Health Monitor.
Simulates pulling metrics from AWS, GCP, and OCI for demo purposes.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np


class CloudMetricsIngestor:
    """
    Simulates ingestion of cloud infrastructure metrics from multiple providers.
    In production, this would integrate with cloud provider APIs.
    """
    
    # Instance type configurations for simulation
    INSTANCE_TYPES = {
        "aws": {
            "t3.micro": {"vcpu": 2, "memory_gb": 1, "cost_per_hour": 0.0104},
            "t3.medium": {"vcpu": 2, "memory_gb": 4, "cost_per_hour": 0.0416},
            "m5.large": {"vcpu": 2, "memory_gb": 8, "cost_per_hour": 0.096},
            "m5.xlarge": {"vcpu": 4, "memory_gb": 16, "cost_per_hour": 0.192},
            "c5.2xlarge": {"vcpu": 8, "memory_gb": 16, "cost_per_hour": 0.34},
            "p3.2xlarge": {"vcpu": 8, "memory_gb": 61, "cost_per_hour": 3.06},
        },
        "gcp": {
            "e2-micro": {"vcpu": 2, "memory_gb": 1, "cost_per_hour": 0.0084},
            "e2-medium": {"vcpu": 2, "memory_gb": 4, "cost_per_hour": 0.0335},
            "n1-standard-2": {"vcpu": 2, "memory_gb": 7.5, "cost_per_hour": 0.095},
            "n1-standard-4": {"vcpu": 4, "memory_gb": 15, "cost_per_hour": 0.19},
            "c2-standard-8": {"vcpu": 8, "memory_gb": 32, "cost_per_hour": 0.382},
            "a2-highgpu-1g": {"vcpu": 12, "memory_gb": 85, "cost_per_hour": 3.67},
        },
        "oci": {
            "VM.Standard.E2.1": {"vcpu": 1, "memory_gb": 8, "cost_per_hour": 0.03},
            "VM.Standard.E2.2": {"vcpu": 2, "memory_gb": 16, "cost_per_hour": 0.06},
            "VM.Standard.E3.Flex": {"vcpu": 4, "memory_gb": 32, "cost_per_hour": 0.085},
            "VM.GPU2.1": {"vcpu": 12, "memory_gb": 72, "cost_per_hour": 2.95},
        }
    }
    
    REGIONS = {
        "aws": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        "gcp": ["us-central1", "us-east1", "europe-west1", "asia-east1"],
        "oci": ["us-ashburn-1", "us-phoenix-1", "eu-frankfurt-1", "ap-tokyo-1"]
    }
    
    def __init__(self):
        self.instances: Dict[str, Dict] = {}
        self.metrics_history: List[Dict] = []
        self._generate_demo_instances()
    
    def _generate_demo_instances(self):
        """Generate a set of demo instances across providers."""
        instance_num = 0
        
        for provider in ["aws", "gcp", "oci"]:
            regions = self.REGIONS[provider]
            instance_types = list(self.INSTANCE_TYPES[provider].keys())
            
            # Generate 5-10 instances per provider
            num_instances = random.randint(5, 10)
            
            for i in range(num_instances):
                instance_id = f"{provider}-{instance_num:04d}"
                instance_type = random.choice(instance_types)
                
                # Determine resource type
                if "gpu" in instance_type.lower() or "p3" in instance_type or "a2" in instance_type:
                    resource_type = "ml-inference"
                elif instance_num % 5 == 0:
                    resource_type = "k8s-node"
                else:
                    resource_type = "vm"
                
                self.instances[instance_id] = {
                    "instance_id": instance_id,
                    "provider": provider,
                    "instance_type": instance_type,
                    "region": random.choice(regions),
                    "resource_type": resource_type,
                    "specs": self.INSTANCE_TYPES[provider][instance_type],
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                    # Utilization profile: some instances are idle, some are efficient
                    "utilization_profile": random.choice(["idle", "low", "medium", "high", "efficient"])
                }
                
                instance_num += 1
    
    def get_instances(self, provider: str = None) -> List[Dict]:
        """Get list of instances, optionally filtered by provider."""
        if provider:
            return [i for i in self.instances.values() if i["provider"] == provider]
        return list(self.instances.values())
    
    def collect_metrics(self, instance_id: str = None) -> List[Dict]:
        """
        Collect current metrics for instance(s).
        
        Args:
            instance_id: Optional specific instance, or all if None
            
        Returns:
            List of metric dictionaries
        """
        instances = [self.instances[instance_id]] if instance_id else self.instances.values()
        metrics = []
        
        for instance in instances:
            profile = instance["utilization_profile"]
            
            # Generate metrics based on utilization profile
            if profile == "idle":
                cpu_base, mem_base = 2, 5
            elif profile == "low":
                cpu_base, mem_base = 10, 20
            elif profile == "medium":
                cpu_base, mem_base = 40, 50
            elif profile == "high":
                cpu_base, mem_base = 85, 80
            else:  # efficient
                cpu_base, mem_base = 65, 70
            
            # Add some variance
            cpu_util = max(0, min(100, cpu_base + random.gauss(0, 5)))
            mem_util = max(0, min(100, mem_base + random.gauss(0, 3)))
            
            metric = {
                "instance_id": instance["instance_id"],
                "provider": instance["provider"],
                "resource_type": instance["resource_type"],
                "instance_type": instance["instance_type"],
                "region": instance["region"],
                "cpu_util": round(cpu_util, 2),
                "memory_util": round(mem_util, 2),
                "disk_iops": round(random.uniform(50, 500), 2),
                "network_in_bytes": round(random.uniform(1e6, 1e9), 0),
                "network_out_bytes": round(random.uniform(5e5, 5e8), 0),
                "ts": datetime.utcnow()
            }
            
            metrics.append(metric)
            self.metrics_history.append(metric)
        
        # Keep history bounded
        if len(self.metrics_history) > 10000:
            self.metrics_history = self.metrics_history[-10000:]
        
        return metrics
    
    def get_idle_instances(self, threshold_cpu: float = 10) -> List[Dict]:
        """Get instances with CPU utilization below threshold."""
        # Collect fresh metrics
        metrics = self.collect_metrics()
        
        idle = []
        for m in metrics:
            if m["cpu_util"] < threshold_cpu:
                instance = self.instances.get(m["instance_id"], {})
                idle.append({
                    **m,
                    "specs": instance.get("specs", {}),
                    "days_running": (datetime.utcnow() - instance.get("created_at", datetime.utcnow())).days
                })
        
        return sorted(idle, key=lambda x: x["cpu_util"])
    
    def get_rightsizing_opportunities(self) -> List[Dict]:
        """Identify instances that could be rightsized for cost savings."""
        metrics = self.collect_metrics()
        opportunities = []
        
        for m in metrics:
            instance = self.instances.get(m["instance_id"], {})
            provider = instance.get("provider")
            current_type = instance.get("instance_type")
            
            if not provider or not current_type:
                continue
            
            current_specs = self.INSTANCE_TYPES.get(provider, {}).get(current_type, {})
            current_cost = current_specs.get("cost_per_hour", 0)
            
            # If utilization is low, suggest smaller instance
            if m["cpu_util"] < 20 and m["memory_util"] < 30:
                # Find a smaller instance type
                for alt_type, alt_specs in self.INSTANCE_TYPES.get(provider, {}).items():
                    if alt_specs["cost_per_hour"] < current_cost * 0.7:
                        # Check if smaller instance has enough resources
                        if alt_specs["vcpu"] >= 1 and alt_specs["memory_gb"] >= 1:
                            monthly_savings = (current_cost - alt_specs["cost_per_hour"]) * 24 * 30
                            
                            opportunities.append({
                                "instance_id": m["instance_id"],
                                "provider": provider,
                                "current_type": current_type,
                                "recommended_type": alt_type,
                                "current_cpu_util": m["cpu_util"],
                                "current_memory_util": m["memory_util"],
                                "current_cost_per_hour": current_cost,
                                "recommended_cost_per_hour": alt_specs["cost_per_hour"],
                                "estimated_monthly_savings": round(monthly_savings, 2),
                                "confidence": "high" if m["cpu_util"] < 10 else "medium"
                            })
                            break
        
        return sorted(opportunities, key=lambda x: -x["estimated_monthly_savings"])
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics across all instances."""
        metrics = self.collect_metrics()
        
        if not metrics:
            return {}
        
        by_provider = {}
        for provider in ["aws", "gcp", "oci"]:
            provider_metrics = [m for m in metrics if m["provider"] == provider]
            if provider_metrics:
                by_provider[provider] = {
                    "instance_count": len(provider_metrics),
                    "avg_cpu_util": round(np.mean([m["cpu_util"] for m in provider_metrics]), 2),
                    "avg_memory_util": round(np.mean([m["memory_util"] for m in provider_metrics]), 2),
                    "total_instances": len([i for i in self.instances.values() if i["provider"] == provider])
                }
        
        return {
            "total_instances": len(self.instances),
            "by_provider": by_provider,
            "idle_count": len([m for m in metrics if m["cpu_util"] < 10]),
            "overutilized_count": len([m for m in metrics if m["cpu_util"] > 80]),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global ingestor instance
cloud_ingestor = CloudMetricsIngestor()
