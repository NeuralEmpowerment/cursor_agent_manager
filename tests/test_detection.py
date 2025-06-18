#!/usr/bin/env python3
"""
Template Detection Test Script

This script helps test and validate the template detection system.
Use this to:
1. Test template detection without running the full monitor
2. Validate template images are working
3. Adjust confidence thresholds
4. Debug detection issues
"""

import os
import time
import cv2
import numpy as np
import pyautogui
from agent_monitor_poc import EnhancedTemplateMatchDetector, AgentState

# Configuration for testing - import from main module
from agent_monitor_poc import TEMPLATE_DIRECTORIES, STATE_TEMPLATE_MAPPING, load_templates_from_directories

# Load templates using the new directory system
state_templates = load_templates_from_directories(TEMPLATE_DIRECTORIES, STATE_TEMPLATE_MAPPING)
IDLE_TEMPLATES = state_templates.get(AgentState.IDLE, [])
ACTIVE_TEMPLATES = state_templates.get(AgentState.ACTIVE, [])

def test_template_loading():
    """Test if all template images can be loaded."""
    print("=" * 50)
    print("TESTING TEMPLATE LOADING")
    print("=" * 50)
    
    all_templates = IDLE_TEMPLATES + ACTIVE_TEMPLATES
    for template_path in all_templates:
        if os.path.exists(template_path):
            img = cv2.imread(template_path)
            if img is not None:
                print(f"✓ {template_path} - Loaded successfully ({img.shape})")
            else:
                print(f"✗ {template_path} - Failed to load image data")
        else:
            print(f"✗ {template_path} - File not found")
    print()

def test_single_detection():
    """Test a single detection cycle."""
    print("=" * 50)
    print("TESTING SINGLE DETECTION")
    print("=" * 50)
    
    try:
        detector = EnhancedTemplateMatchDetector(
            state_templates,
            confidence_threshold=0.7,  # Lower threshold for testing
            min_confidence_gap=0.05
        )
        
        print("Taking screenshot and analyzing...")
        state = detector.detect_state()
        
        print(f"Detected State: {state}")
        print(f"Overall Confidence: {detector.last_confidence:.3f}")
        
        # Show all state confidences
        for state_name, confidence in detector.state_confidences.items():
            print(f"{state_name} Confidence: {confidence:.3f}")
        
        if detector._last_match_rect:
            x, y, w, h = detector._last_match_rect
            print(f"Match Rectangle: ({x}, {y}, {w}, {h})")
        
        # Show confidence analysis
        confidences = list(detector.state_confidences.values())
        if len(confidences) >= 2:
            sorted_confs = sorted(confidences, reverse=True)
            confidence_gap = sorted_confs[0] - sorted_confs[1]
            print(f"Confidence Gap: {confidence_gap:.3f}")
        
        if confidence_gap < 0.1:
            print("⚠️  Warning: Confidence gap is small - may cause state switching")
        
    except Exception as e:
        print(f"Error during detection: {e}")
    print()

def test_continuous_detection(duration=30):
    """Test continuous detection for a specified duration."""
    print("=" * 50)
    print(f"TESTING CONTINUOUS DETECTION ({duration} seconds)")
    print("=" * 50)
    
    try:
        detector = EnhancedTemplateMatchDetector(
            state_templates,
            confidence_threshold=0.8,
            min_confidence_gap=0.1
        )
        
        start_time = time.time()
        detection_count = 0
        state_changes = 0
        last_state = None
        
        print("State | Confidence | Idle Conf | Active Conf | Gap   | Stable")
        print("-" * 65)
        
        while time.time() - start_time < duration:
            state = detector.detect_state()
            detection_count += 1
            
            if state != last_state and last_state is not None:
                state_changes += 1
            last_state = state
            
            # Show current detection info
            gap = abs(detector.last_idle_confidence - detector.last_active_confidence)
            stable_state = detector._get_stable_state(state)
            
            print(f"{state:6} | {detector.last_confidence:10.3f} | "
                  f"{detector.last_idle_confidence:9.3f} | "
                  f"{detector.last_active_confidence:11.3f} | "
                  f"{gap:5.3f} | {stable_state or 'None'}")
            
            time.sleep(2)
        
        print("-" * 65)
        print(f"Total detections: {detection_count}")
        print(f"State changes: {state_changes}")
        print(f"Change rate: {state_changes/detection_count:.1%}")
        
        if state_changes / detection_count > 0.3:
            print("⚠️  High state change rate detected - consider tuning parameters")
        
    except Exception as e:
        print(f"Error during continuous detection: {e}")
    print()

def test_confidence_thresholds():
    """Test different confidence thresholds to find optimal values."""
    print("=" * 50)
    print("TESTING CONFIDENCE THRESHOLDS")
    print("=" * 50)
    
    thresholds = [0.6, 0.7, 0.8, 0.9]
    gaps = [0.05, 0.1, 0.15, 0.2]
    
    for threshold in thresholds:
        for gap in gaps:
            try:
                detector = EnhancedTemplateMatchDetector(
                    IDLE_TEMPLATES, 
                    ACTIVE_TEMPLATES,
                    confidence_threshold=threshold,
                    min_confidence_gap=gap
                )
                
                state = detector.detect_state()
                print(f"Threshold: {threshold:.1f}, Gap: {gap:.2f} → "
                      f"State: {state:6}, Conf: {detector.last_confidence:.3f}")
                
            except Exception as e:
                print(f"Error with threshold {threshold}, gap {gap}: {e}")
    print()

def main():
    print("Template Detection Test Script")
    print("Press Ctrl+C to stop at any time\n")
    
    try:
        # Run all tests
        test_template_loading()
        test_single_detection()
        
        # Ask user for continuous test
        response = input("Run continuous detection test? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            duration = input("Duration in seconds (default 30): ").strip()
            duration = int(duration) if duration.isdigit() else 30
            test_continuous_detection(duration)
        
        # Ask user for threshold testing
        response = input("Test different confidence thresholds? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            test_confidence_thresholds()
        
        print("Testing complete!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    main() 