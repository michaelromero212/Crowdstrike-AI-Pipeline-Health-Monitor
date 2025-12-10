#!/usr/bin/env python3
"""
Failure injection script for CrowdStrike AI Pipeline Health Monitor demo.

Usage:
    python inject_failure.py --type latency --severity high
    python inject_failure.py --type correctness --severity medium
    python inject_failure.py --type drift
    python inject_failure.py --clear
"""

import argparse
import requests
import sys

API_BASE = "http://localhost:8000"


def inject_failure(failure_type: str, severity: str = "medium"):
    """Inject a failure into the model client."""
    print(f"💉 Injecting {severity} {failure_type} failure...")
    
    try:
        response = requests.post(
            f"{API_BASE}/inject-failure",
            json={"failure_type": failure_type, "severity": severity}
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Failure injected at {result['timestamp']}")
        return result
    except requests.RequestException as e:
        print(f"❌ Failed to inject failure: {e}")
        sys.exit(1)


def clear_failures():
    """Clear all injected failures."""
    print("🧹 Clearing all failures...")
    
    try:
        response = requests.post(f"{API_BASE}/clear-failures")
        response.raise_for_status()
        result = response.json()
        print(f"✅ Failures cleared at {result.get('timestamp', 'unknown')}")
        return result
    except requests.RequestException as e:
        print(f"❌ Failed to clear failures: {e}")
        sys.exit(1)


def run_health_checks():
    """Run all health checks to demonstrate failure detection."""
    print("🔍 Running all health checks...")
    
    try:
        response = requests.post(f"{API_BASE}/healthchecks/run-all")
        response.raise_for_status()
        result = response.json()
        
        print(f"\n📊 Results: {result['passed']}/{result['total']} passed")
        for check in result['results']:
            status = "✅" if check['passed'] else "❌"
            print(f"  {status} {check['check_name']}: {'PASSED' if check['passed'] else 'FAILED'}")
        
        return result
    except requests.RequestException as e:
        print(f"❌ Failed to run checks: {e}")
        sys.exit(1)


def get_model_health():
    """Get current model client health status."""
    try:
        response = requests.get(f"{API_BASE}/model-health")
        response.raise_for_status()
        health = response.json()
        
        print("\n📋 Model Client Status:")
        print(f"  Status: {health['status']}")
        print(f"  Version: {health['model_version']}")
        print(f"  Failure Mode:")
        print(f"    - Latency Multiplier: {health['failure_mode']['latency_multiplier']}x")
        print(f"    - Error Rate: {health['failure_mode']['error_rate']:.0%}")
        print(f"    - Drift Enabled: {health['failure_mode']['drift_enabled']}")
        print(f"    - Correctness Flip Rate: {health['failure_mode']['correctness_flip_rate']:.0%}")
        
        return health
    except requests.RequestException as e:
        print(f"❌ Failed to get health: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Inject failures for CrowdStrike AI Pipeline Health Monitor demo"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["latency", "correctness", "drift", "error"],
        help="Type of failure to inject"
    )
    parser.add_argument(
        "--severity", "-s",
        choices=["low", "medium", "high"],
        default="medium",
        help="Severity of the failure (default: medium)"
    )
    parser.add_argument(
        "--clear", "-c",
        action="store_true",
        help="Clear all injected failures"
    )
    parser.add_argument(
        "--run-checks", "-r",
        action="store_true",
        help="Run health checks after injection"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current model health status"
    )
    
    args = parser.parse_args()
    
    if args.status:
        get_model_health()
        return
    
    if args.clear:
        clear_failures()
        if args.run_checks:
            print()
            run_health_checks()
        return
    
    if not args.type:
        parser.print_help()
        print("\n⚠️  Please specify --type or --clear")
        sys.exit(1)
    
    inject_failure(args.type, args.severity)
    
    if args.run_checks:
        print()
        run_health_checks()
    
    print("\n💡 Tip: Open http://localhost:3000 to see the dashboard update")


if __name__ == "__main__":
    main()
