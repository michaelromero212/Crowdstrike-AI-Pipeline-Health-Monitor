"""
Rightsizing recommendation engine for CrowdStrike AI Pipeline Health Monitor.
Analyzes infrastructure utilization and generates optimization recommendations.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
from app.services.cloud_ingestor import cloud_ingestor


class RightsizingEngine:
    """
    Analyzes infrastructure usage patterns and generates rightsizing recommendations.
    """
    
    # Thresholds for analysis
    CPU_IDLE_THRESHOLD = 10  # Below this = idle
    CPU_LOW_THRESHOLD = 30   # Below this = underutilized
    CPU_HIGH_THRESHOLD = 80  # Above this = overutilized
    MEMORY_LOW_THRESHOLD = 40
    MEMORY_HIGH_THRESHOLD = 90
    
    def __init__(self):
        self.recommendations_history: List[Dict] = []
    
    def analyze_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Analyze a single instance for optimization opportunities.
        
        Args:
            instance_id: Instance to analyze
            
        Returns:
            Analysis with recommendations
        """
        metrics = cloud_ingestor.collect_metrics(instance_id)
        if not metrics:
            return {"error": f"No metrics found for {instance_id}"}
        
        m = metrics[0]
        instance = cloud_ingestor.instances.get(instance_id, {})
        
        analysis = {
            "instance_id": instance_id,
            "provider": m["provider"],
            "instance_type": m["instance_type"],
            "region": m["region"],
            "current_utilization": {
                "cpu": m["cpu_util"],
                "memory": m["memory_util"],
                "disk_iops": m["disk_iops"]
            },
            "status": self._get_utilization_status(m["cpu_util"], m["memory_util"]),
            "recommendations": [],
            "estimated_savings": 0,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        # Generate recommendations based on utilization
        if m["cpu_util"] < self.CPU_IDLE_THRESHOLD:
            analysis["recommendations"].append({
                "type": "terminate_or_downsize",
                "priority": "high",
                "reason": f"CPU utilization is only {m['cpu_util']:.1f}%",
                "action": "Consider terminating if unused, or downsizing significantly"
            })
        elif m["cpu_util"] < self.CPU_LOW_THRESHOLD:
            analysis["recommendations"].append({
                "type": "downsize",
                "priority": "medium",
                "reason": f"CPU utilization is low at {m['cpu_util']:.1f}%",
                "action": "Consider downsizing to a smaller instance type"
            })
        elif m["cpu_util"] > self.CPU_HIGH_THRESHOLD:
            analysis["recommendations"].append({
                "type": "upsize_or_scale",
                "priority": "high",
                "reason": f"CPU utilization is high at {m['cpu_util']:.1f}%",
                "action": "Consider upsizing or adding horizontal scaling"
            })
        
        if m["memory_util"] > self.MEMORY_HIGH_THRESHOLD:
            analysis["recommendations"].append({
                "type": "add_memory",
                "priority": "high",
                "reason": f"Memory utilization is critical at {m['memory_util']:.1f}%",
                "action": "Consider instance type with more memory"
            })
        
        # Calculate estimated savings
        opportunities = cloud_ingestor.get_rightsizing_opportunities()
        for opp in opportunities:
            if opp["instance_id"] == instance_id:
                analysis["estimated_savings"] = opp["estimated_monthly_savings"]
                analysis["recommendations"].append({
                    "type": "rightsize",
                    "priority": "medium",
                    "reason": f"Could save ${opp['estimated_monthly_savings']:.2f}/month",
                    "action": f"Change from {opp['current_type']} to {opp['recommended_type']}"
                })
                break
        
        return analysis
    
    def _get_utilization_status(self, cpu: float, memory: float) -> str:
        """Determine overall utilization status."""
        if cpu < self.CPU_IDLE_THRESHOLD and memory < self.MEMORY_LOW_THRESHOLD:
            return "idle"
        elif cpu < self.CPU_LOW_THRESHOLD:
            return "underutilized"
        elif cpu > self.CPU_HIGH_THRESHOLD or memory > self.MEMORY_HIGH_THRESHOLD:
            return "overutilized"
        else:
            return "optimal"
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive rightsizing report across all infrastructure.
        
        Returns:
            Report with summary and detailed recommendations
        """
        instances = cloud_ingestor.get_instances()
        summary = cloud_ingestor.get_summary_stats()
        opportunities = cloud_ingestor.get_rightsizing_opportunities()
        idle_instances = cloud_ingestor.get_idle_instances()
        
        # Analyze all instances
        all_analyses = []
        for instance in instances:
            analysis = self.analyze_instance(instance["instance_id"])
            if "error" not in analysis:
                all_analyses.append(analysis)
        
        # Group by status
        by_status = {}
        for analysis in all_analyses:
            status = analysis["status"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(analysis)
        
        # Calculate total potential savings
        total_savings = sum(opp["estimated_monthly_savings"] for opp in opportunities)
        
        report = {
            "title": "Infrastructure Rightsizing Report",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_instances": len(instances),
                "by_provider": summary.get("by_provider", {}),
                "utilization_breakdown": {
                    status: len(analyses) for status, analyses in by_status.items()
                },
                "total_potential_monthly_savings": round(total_savings, 2),
                "idle_instance_count": len(idle_instances),
                "rightsizing_opportunities": len(opportunities)
            },
            "top_recommendations": opportunities[:10],
            "idle_instances": idle_instances[:10],
            "detailed_analyses": all_analyses[:20],  # Limit for report size
            "executive_summary": self._generate_executive_summary(
                len(instances), by_status, total_savings, len(opportunities)
            )
        }
        
        self.recommendations_history.append({
            "generated_at": report["generated_at"],
            "summary": report["summary"]
        })
        
        return report
    
    def _generate_executive_summary(self, total: int, by_status: Dict, 
                                    savings: float, opportunities: int) -> str:
        """Generate a text executive summary."""
        idle_count = len(by_status.get("idle", []))
        underutilized_count = len(by_status.get("underutilized", []))
        overutilized_count = len(by_status.get("overutilized", []))
        optimal_count = len(by_status.get("optimal", []))
        
        summary = f"""
## Executive Summary

Analyzed **{total} instances** across AWS, GCP, and OCI cloud providers.

### Key Findings:
- **{idle_count}** instances are idle (<10% CPU utilization)
- **{underutilized_count}** instances are underutilized (<30% CPU)
- **{overutilized_count}** instances are overutilized (>80% CPU)
- **{optimal_count}** instances are optimally utilized

### Cost Optimization Potential:
- **{opportunities}** rightsizing opportunities identified
- Estimated monthly savings: **${savings:,.2f}**

### Recommended Actions:
1. Review and terminate idle instances
2. Downsize underutilized instances
3. Add capacity to overutilized instances
4. Implement auto-scaling where appropriate
        """.strip()
        
        return summary
    
    def generate_ansible_playbook(self, recommendations: List[Dict]) -> str:
        """
        Generate an Ansible playbook for implementing recommendations.
        
        Args:
            recommendations: List of rightsizing recommendations
            
        Returns:
            Ansible playbook as YAML string
        """
        tasks = []
        
        for rec in recommendations[:5]:  # Limit to top 5
            if rec.get("provider") == "aws":
                tasks.append({
                    "name": f"Resize {rec['instance_id']} to {rec['recommended_type']}",
                    "ec2_instance": {
                        "instance_id": rec["instance_id"],
                        "instance_type": rec["recommended_type"],
                        "state": "present"
                    },
                    "tags": ["rightsize", "aws"]
                })
        
        playbook = f"""---
# Rightsizing Playbook - Generated {datetime.utcnow().isoformat()}
# REVIEW CAREFULLY BEFORE EXECUTING
- name: Apply rightsizing recommendations
  hosts: localhost
  connection: local
  gather_facts: false
  
  vars:
    dry_run: true  # Set to false to apply changes
    
  tasks:
    - name: Display dry run warning
      debug:
        msg: "DRY RUN MODE - No changes will be applied"
      when: dry_run
      
    # Add generated tasks here...
    - name: Log recommendations
      debug:
        msg: "Would apply {len(recommendations)} rightsizing changes"
"""
        
        return playbook
    
    def export_csv_report(self) -> str:
        """Export recommendations as CSV format."""
        opportunities = cloud_ingestor.get_rightsizing_opportunities()
        
        lines = ["instance_id,provider,current_type,recommended_type,current_cpu,monthly_savings,confidence"]
        
        for opp in opportunities:
            lines.append(
                f"{opp['instance_id']},{opp['provider']},{opp['current_type']},"
                f"{opp['recommended_type']},{opp['current_cpu_util']:.1f},"
                f"{opp['estimated_monthly_savings']:.2f},{opp['confidence']}"
            )
        
        return "\n".join(lines)


# Global engine instance
rightsizing_engine = RightsizingEngine()
