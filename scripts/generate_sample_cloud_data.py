#!/usr/bin/env python3
"""
Generate sample cloud infrastructure data for CrowdStrike AI Pipeline Health Monitor demo.
This populates the database with realistic multi-cloud metrics.
"""

import requests
import random
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"


def main():
    print("🏗️  Generating sample cloud infrastructure data...")
    
    # The cloud ingestor auto-generates instances, so just trigger metric collection
    try:
        # Get infrastructure summary to trigger data generation
        response = requests.get(f"{API_BASE}/infrastructure/summary")
        response.raise_for_status()
        summary = response.json()
        
        print(f"\n📊 Infrastructure Summary:")
        print(f"  Total instances: {summary['total_instances']}")
        print(f"  Idle instances: {summary['idle_count']}")
        print(f"  Overutilized: {summary['overutilized_count']}")
        
        # Get cost summary
        response = requests.get(f"{API_BASE}/infrastructure/cost-summary")
        response.raise_for_status()
        costs = response.json()
        
        print(f"\n💰 Cost Summary:")
        print(f"  Monthly cost: ${costs['estimated_monthly_cost']:.2f}")
        print(f"  Potential savings: ${costs['potential_monthly_savings']:.2f}")
        
        # Get rightsizing opportunities
        response = requests.get(f"{API_BASE}/rightsizing/opportunities?limit=5")
        response.raise_for_status()
        opportunities = response.json()
        
        print(f"\n💡 Top Rightsizing Opportunities:")
        for opp in opportunities[:5]:
            print(f"  - {opp['instance_id']}: {opp['current_type']} → {opp['recommended_type']} (${opp['estimated_monthly_savings']:.2f}/mo)")
        
        print("\n✅ Sample data generated successfully!")
        print(f"   View at: http://localhost:3000 (Infrastructure tab)")
        
    except requests.RequestException as e:
        print(f"❌ Failed to generate data: {e}")
        print("   Make sure the backend is running: docker-compose up")


if __name__ == "__main__":
    main()
