#!/usr/bin/env python3
"""
Template Capture Tool

This tool helps you capture and analyze the current UI state to improve template matching.
Use this when the detection system isn't working correctly.
"""

import pyautogui
import cv2
import numpy as np
import os
from datetime import datetime

def capture_current_state():
    """Capture current screenshot and show confidence against existing templates."""
    from agent_monitor_poc import (
        TEMPLATE_DIRECTORIES, STATE_TEMPLATE_MAPPING, load_templates_from_directories, 
        EnhancedTemplateMatchDetector, CONFIDENCE_THRESHOLD, MIN_CONFIDENCE_GAP
    )
    
    print("Capturing current state...")
    screenshot = pyautogui.screenshot()
    
    # Load existing templates
    state_templates = load_templates_from_directories(TEMPLATE_DIRECTORIES, STATE_TEMPLATE_MAPPING)
    
    if not state_templates:
        print("No templates found!")
        return
    
    # Create detector using global config
    detector = EnhancedTemplateMatchDetector(
        state_templates, 
        confidence_threshold=CONFIDENCE_THRESHOLD,
        min_confidence_gap=MIN_CONFIDENCE_GAP
    )
    
    # Test current state
    state = detector.detect_state()
    
    print(f"\n=== CURRENT STATE ANALYSIS ===")
    print(f"Detected State: {state}")
    if detector.last_confidence is not None:
        print(f"Overall Confidence: {detector.last_confidence:.3f}")
    else:
        print("Overall Confidence: None (unknown state)")
    print("\nAll State Confidences:")
    for state_name, confidence in detector.state_confidences.items():
        print(f"  {state_name}: {confidence:.3f}")
    
    # Save current screenshot for reference
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"debug_screenshot_{timestamp}.png"
    screenshot.save(screenshot_path)
    print(f"\nScreenshot saved as: {screenshot_path}")
    
    return state, detector.state_confidences, CONFIDENCE_THRESHOLD, MIN_CONFIDENCE_GAP

def suggest_action(detected_state, confidences, confidence_threshold, min_confidence_gap):
    """Suggest what to do based on current detection."""
    print(f"\n=== RECOMMENDATIONS ===")
    print(f"Using global config: threshold={confidence_threshold:.2f}, min_gap={min_confidence_gap:.2f}")
    
    sorted_confs = sorted(confidences.items(), key=lambda x: x[1], reverse=True)
    best_state, best_conf = sorted_confs[0]
    
    if len(sorted_confs) > 1:
        second_state, second_conf = sorted_confs[1]
        gap = best_conf - second_conf
        print(f"Confidence gap: {gap:.3f} (need ≥ {min_confidence_gap:.2f} for reliable detection)")
        
        if gap < min_confidence_gap:
            print("❌ PROBLEM: Confidence gap too small!")
            print("Solutions:")
            print("1. Take better template screenshots that are more distinct")
            print("2. Crop templates more precisely to unique UI elements")
            print(f"3. Remove or replace the {second_state} template if it's too similar")
            
            if best_conf > confidence_threshold:
                print(f"4. The {best_state} template seems good - focus on improving {second_state}")
    
    if best_conf < confidence_threshold:
        print(f"❌ PROBLEM: Best confidence ({best_conf:.3f}) is too low!")
        print("Solutions:")
        print(f"1. Take a new {best_state} template from current UI state")
        print("2. Ensure template captures the most distinctive UI element")
        print("3. Check that UI hasn't changed (dark mode, themes, etc.)")

def save_as_template():
    """Save current screenshot as a new template."""
    print("\n=== SAVE AS TEMPLATE ===")
    print("Available states:")
    for i, state in enumerate(['idle', 'active', 'run_command'], 1):
        print(f"{i}. {state}")
    
    choice = input("Which state does this represent? (1-3): ").strip()
    
    state_map = {'1': 'idle', '2': 'active', '3': 'run_command'}
    if choice not in state_map:
        print("Invalid choice!")
        return
    
    state = state_map[choice]
    
    # Take screenshot
    screenshot = pyautogui.screenshot()
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{state}_template_{timestamp}.png"
    
    # Determine directory
    dir_map = {
        'idle': 'assets/ui-cursor/agent_idle',
        'active': 'assets/ui-cursor/agent_active', 
        'run_command': 'assets/ui-cursor/run_command'
    }
    
    directory = dir_map[state]
    filepath = os.path.join(directory, filename)
    
    # Save
    screenshot.save(filepath)
    print(f"✅ Template saved as: {filepath}")
    print("Restart the monitor to use the new template!")

def main():
    print("Template Capture & Analysis Tool")
    print("=" * 40)
    print("(Press Ctrl+C anytime to exit)")
    
    try:
        while True:
            print("\nOptions:")
            print("1. Analyze current state")
            print("2. Save current screen as template")
            print("3. Exit")
            
            choice = input("\nChoose option (1-3): ").strip()
            
            if choice == '1':
                try:
                    state, confidences, threshold, min_gap = capture_current_state()
                    suggest_action(state, confidences, threshold, min_gap)
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif choice == '2':
                try:
                    save_as_template()
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif choice == '3':
                print("Goodbye!")
                break
            else:
                print("Invalid choice!")
                
    except KeyboardInterrupt:
        print("\n\n👋 Exiting capture tool... Goodbye!")
    except EOFError:
        print("\n\n👋 Exiting capture tool... Goodbye!")

if __name__ == "__main__":
    main() 