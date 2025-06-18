#!/usr/bin/env python3
"""
Test script for the new telemetry system
"""

import sys
import os
from datetime import datetime
from container import TelemetryContainer, initialize_telemetry_system
from telemetry import EventType

def test_basic_functionality():
    """Test basic telemetry functionality."""
    print("Testing Telemetry System Integration...")
    print("=" * 50)
    
    try:
        # Initialize container
        print("1. Initializing dependency injection container...")
        container = initialize_telemetry_system()
        print("   ✓ Container initialized successfully")
        
        # Get services
        print("2. Getting telemetry and analytics services...")
        telemetry_service = container.telemetry_service()
        analytics_service = container.analytics_service()
        repository = container.telemetry_repository()
        print("   ✓ Services retrieved successfully")
        
        # Test database info
        print("3. Testing database connectivity...")
        db_info = repository.get_database_info()
        print(f"   ✓ Database: {db_info['db_path']}")
        print(f"   ✓ Current events: {db_info['total_events']}")
        print(f"   ✓ Database size: {db_info['db_size_mb']} MB")
        
        # Test recording events
        print("4. Testing event recording...")
        
        # Record some test events
        telemetry_service.record_detection(
            event_type=EventType.IDLE_DETECTION,
            message="Test idle detection",
            confidence=0.95,
            detection_method="TestDetector",
            state="idle",
            match_rect=(100, 200, 50, 30)
        )
        
        telemetry_service.record_detection(
            event_type=EventType.ACTIVE_DETECTION,
            message="Test active detection",
            confidence=0.87,
            detection_method="TestDetector",
            state="active"
        )
        
        telemetry_service.record_event(
            event_type=EventType.COMMAND_EXECUTION,
            message="Test command execution",
            command="test command",
            execution_time=0.5
        )
        
        print("   ✓ Test events recorded successfully")
        
        # Test retrieving events
        print("5. Testing event retrieval...")
        recent_events = repository.get_events(limit=5)
        print(f"   ✓ Retrieved {len(recent_events)} recent events")
        
        for event in recent_events:
            print(f"     - {event.timestamp}: {event.event_type.value} ({event.message})")
        
        # Test statistics
        print("6. Testing statistics...")
        stats = repository.get_session_stats()
        print(f"   ✓ Idle detections: {stats.total_idle_detections}")
        print(f"   ✓ Active detections: {stats.total_active_detections}")
        print(f"   ✓ Detection failures: {stats.total_detection_failures}")
        print(f"   ✓ Average confidence: {stats.average_confidence:.2f}")
        
        # Test analytics
        print("7. Testing analytics...")
        report = analytics_service.generate_daily_report(datetime.now())
        print(f"   ✓ Daily report generated for {report['date']}")
        print(f"     - Total events: {sum(report['event_breakdown'].values()) if report['event_breakdown'] else 0}")
        
        trends = analytics_service.get_detection_accuracy_trends(days=1)
        print(f"   ✓ Accuracy trends: {trends['average_accuracy']:.1f}% average")
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Telemetry system is working correctly.")
        
        # Show some usage examples
        print("\nUsage Examples:")
        print("  ./run_analytics.sh info")
        print("  ./run_analytics.sh events --limit 10")
        print("  ./run_analytics.sh stats")
        print("  ./run_analytics.sh chart accuracy_trend")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1) 