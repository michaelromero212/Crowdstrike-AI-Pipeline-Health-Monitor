# Infrastructure Optimization Report Template

**Report Date:** [YYYY-MM-DD]  
**Prepared By:** [Name]  
**Review Period:** [Start Date] - [End Date]

---

## Executive Summary

This report summarizes infrastructure optimization opportunities identified during the review period. Total estimated monthly savings: **$X,XXX**.

### Key Findings

| Category | Count | Est. Monthly Savings |
|----------|-------|---------------------|
| Idle Instances | X | $X,XXX |
| Oversized Instances | X | $X,XXX |
| Orphaned Volumes | X | $XXX |
| Reserved Instance Opportunities | X | $X,XXX |

### Priority Actions

1. **Critical (This Week):**
   - Terminate X idle instances in [region]
   - Downsize X overprovisioned ML instances

2. **High (This Month):**
   - Migrate X instances to reserved pricing
   - Clean up orphaned storage volumes

3. **Medium (This Quarter):**
   - Implement auto-scaling for variable workloads
   - Review spot instance opportunities

---

## Detailed Findings

### 1. Idle Instance Analysis

Instances with <10% average CPU utilization over the review period.

| Instance ID | Provider | Type | Avg CPU | Days Idle | Monthly Cost | Action |
|-------------|----------|------|---------|-----------|--------------|--------|
| aws-0001 | AWS | m5.xlarge | 3.2% | 28 | $140 | Terminate |
| gcp-0005 | GCP | n1-standard-4 | 7.1% | 14 | $138 | Review |

**Recommendation:** Review with application owners and terminate if no longer needed.

### 2. Rightsizing Opportunities

Instances where resource allocation exceeds actual usage.

| Instance ID | Current Type | Recommended | CPU P95 | Memory P95 | Savings/mo |
|-------------|--------------|-------------|---------|------------|------------|
| aws-0012 | c5.2xlarge | c5.large | 22% | 35% | $185 |
| oci-0003 | VM.Standard.E3 | VM.Standard.E2 | 18% | 28% | $95 |

**Recommendation:** Schedule maintenance window for instance type changes.

### 3. Storage Optimization

Volumes with significant unused capacity or no recent access.

| Volume ID | Provider | Provisioned | Used | Last Access | Action |
|-----------|----------|-------------|------|-------------|--------|
| vol-abc123 | AWS | 1TB | 50GB | 45 days | Archive/Delete |
| disk-xyz | GCP | 500GB | 100GB | 30 days | Resize |

**Recommendation:** Implement lifecycle policies and archive cold data.

---

## Remediation Playbooks

### Playbook 1: Terminate Idle Instance

```bash
# AWS Example
aws ec2 stop-instances --instance-ids i-1234567890abcdef0
# Verify no dependent services
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0
```

### Playbook 2: Rightsize Instance

```yaml
# Ansible playbook
- name: Rightsize EC2 instance
  hosts: localhost
  tasks:
    - name: Stop instance
      ec2_instance:
        instance_ids: "{{ instance_id }}"
        state: stopped
        
    - name: Modify instance type
      ec2_instance:
        instance_ids: "{{ instance_id }}"
        instance_type: "{{ new_type }}"
        
    - name: Start instance
      ec2_instance:
        instance_ids: "{{ instance_id }}"
        state: running
```

### Playbook 3: K8s Resource Adjustment

```bash
kubectl patch deployment inference-service -p \
  '{"spec":{"template":{"spec":{"containers":[{
    "name":"inference",
    "resources":{
      "requests":{"cpu":"500m","memory":"1Gi"},
      "limits":{"cpu":"1","memory":"2Gi"}
    }
  }]}}}}'
```

---

## Validation Steps

After implementing changes:

1. **Verify Service Health**
   - Check application metrics for errors
   - Confirm inference latency within SLA

2. **Monitor Resource Usage**
   - Watch CPU/memory for 24-48 hours
   - Alert on >80% sustained utilization

3. **Cost Confirmation**
   - Verify billing reflects changes
   - Update cost allocation tags

---

## Next Review

Schedule next optimization review for: [Date]

Focus areas:
- Reserved instance renewals
- New workload patterns
- Cloud provider pricing updates
