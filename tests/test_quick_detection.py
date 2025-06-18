#!/usr/bin/env python3
"""Quick detection test to diagnose confidence issues."""

from agent_monitor_poc import *
import time

def main():
    print('=== CURRENT DETECTION TEST ===')
    
    # Test current detection
    state_templates = load_templates_from_directories(TEMPLATE_DIRECTORIES, STATE_TEMPLATE_MAPPING)
    detector = EnhancedTemplateMatchDetector(
        state_templates, 
        confidence_threshold=CONFIDENCE_THRESHOLD,
        min_confidence_gap=MIN_CONFIDENCE_GAP
    )

    print(f'Config: threshold={CONFIDENCE_THRESHOLD}, min_gap={MIN_CONFIDENCE_GAP}')
    print()
    
    for i in range(5):
        state = detector.detect_state()
        conf = detector.last_confidence if detector.last_confidence is not None else 0.0
        print(f'Detection {i+1}: {state} (conf: {conf:.3f})')
        print(f'  All confidences: {detector.state_confidences}')
        
        # Check confidence gap
        confidences = list(detector.state_confidences.values())
        if len(confidences) >= 2:
            sorted_confs = sorted(confidences, reverse=True)
            gap = sorted_confs[0] - sorted_confs[1]
            print(f'  Confidence gap: {gap:.3f} (need >= {MIN_CONFIDENCE_GAP})')
        print()
        time.sleep(2)

if __name__ == "__main__":
    main() 