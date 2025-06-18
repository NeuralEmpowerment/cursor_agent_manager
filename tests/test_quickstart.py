#!/usr/bin/env python3
"""
Quickstart Test Script

Demonstrates the workflow described in DEV_QUICKSTART.md
for adding new events and testing the telemetry system.
"""

import sys
import os
import time

# Add parent directory to path to import from project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from container import initialize_telemetry_system
from telemetry import EventType

def main():
    print("🚀 Agent Monitor Quickstart Test")
    print("=" * 40)
    
    # Initialize the telemetry system
    print("1. Initializing telemetry system...")
    container = initialize_telemetry_system()
    service = container.telemetry_service()
    analytics = container.analytics_service()
    
    print("   ✅ Telemetry system initialized")
    
    # Record some test events
    print("\n2. Recording test events...")
    
    # Standard detection events
    service.record_detection(
        event_type=EventType.IDLE_DETECTION,
        message="Simulated idle detection",
        confidence=0.92,
        detection_method="QuickstartTest",
        state="idle",
        match_rect=(100, 200, 50, 30)
    )
    
    service.record_detection(
        event_type=EventType.ACTIVE_DETECTION,
        message="Simulated active detection", 
        confidence=0.88,
        detection_method="QuickstartTest",
        state="active"
    )
    
    # Custom events with metadata
    service.record_event(
        event_type=EventType.INFO,
        message="Quickstart test completed",
        test_type="quickstart",
        version="1.0",
        duration_seconds=5
    )
    
    print("   ✅ Test events recorded")
    
    # Demonstrate analytics
    print("\n3. Testing analytics...")
    
    # Get recent stats
    stats = service.get_recent_stats(hours=1)
    print(f"   📊 Recent stats:")
    print(f"      - Idle detections: {stats.total_idle_detections}")
    print(f"      - Active detections: {stats.total_active_detections}")
    print(f"      - Average confidence: {stats.average_confidence:.2f}")
    
    # Generate a simple report
    from datetime import datetime
    report = analytics.generate_daily_report(datetime.now())
    print(f"   📈 Today's report:")
    print(f"      - Total events: {sum(report['event_breakdown'].values()) if report['event_breakdown'] else 0}")
    print(f"      - Detection accuracy: {report['summary']['detection_accuracy_percent']}%")
    
    print("\n✅ Quickstart test completed successfully!")
    print("\nNext steps:")
    print("- Run: ./run_analytics.sh events --limit 5")
    print("- Run: ./run_analytics.sh stats")
    print("- Run: ./run_analytics.sh chart event_distribution --days 1")

if __name__ == "__main__":
    main() 