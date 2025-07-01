#!/usr/bin/env python3
"""
Priority Logic Unit Tests

Tests the state detection priority logic with controlled mock data.
Verifies that run_command is properly prioritized over other states.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_monitor_poc import EnhancedTemplateMatchDetector, AgentState

class MockTemplateDetector(EnhancedTemplateMatchDetector):
    """Mock detector that allows us to inject confidence scores for testing."""
    
    def __init__(self, mock_confidences=None, confidence_threshold=0.8, min_confidence_gap=0.08):
        # Initialize with empty templates since we're mocking
        self.state_templates = {
            AgentState.IDLE: [],
            AgentState.ACTIVE: [],
            AgentState.RUN_COMMAND: [],
            AgentState.COMMAND_RUNNING: []
        }
        self.confidence_threshold = confidence_threshold
        self.min_confidence_gap = min_confidence_gap
        self.last_confidence = None
        self.state_confidences = {}
        self._last_match_rect = None
        self._detection_history = []
        self._last_state_change = 0
        self._min_state_change_interval = 5
        self._required_confirmations = 1  # Set to 1 for testing
        
        # Set mock confidences
        self.mock_confidences = mock_confidences or {}
    
    def detect_state(self):
        """Override to use mock confidences instead of actual template matching."""
        # Use mock confidences
        self.state_confidences = self.mock_confidences.copy()
        
        # Find valid states (above threshold)
        valid_states = {}
        for state, confidence in self.state_confidences.items():
            if confidence >= self.confidence_threshold:
                valid_states[state] = {'confidence': confidence, 'rect': None, 'template': 'mock'}
        
        detected_state = AgentState.UNKNOWN
        
        if len(valid_states) == 0:
            detected_state = AgentState.UNKNOWN
        elif len(valid_states) == 1:
            state = list(valid_states.keys())[0]
            detected_state = state
            self.last_confidence = valid_states[state]['confidence']
        else:
            # Multiple states valid - apply priority logic
            sorted_states = sorted(valid_states.items(), key=lambda x: x[1]['confidence'], reverse=True)
            
            best_state, best_result = sorted_states[0]
            second_state, second_result = sorted_states[1] if len(sorted_states) > 1 else (None, {'confidence': 0.0})
            
            confidence_gap = best_result['confidence'] - second_result['confidence']
            
            # Priority 1: Run command (always prioritized if above threshold)
            if AgentState.RUN_COMMAND in valid_states:
                detected_state = AgentState.RUN_COMMAND
                self.last_confidence = valid_states[AgentState.RUN_COMMAND]['confidence']
                
            # Priority 2: Command running (prioritized if above threshold)
            elif AgentState.COMMAND_RUNNING in valid_states:
                detected_state = AgentState.COMMAND_RUNNING
                self.last_confidence = valid_states[AgentState.COMMAND_RUNNING]['confidence']
                
            # Priority 3: Highest confidence wins
            elif confidence_gap >= self.min_confidence_gap:
                detected_state = best_state
                self.last_confidence = best_result['confidence']
            else:
                # Too close - stay unknown
                detected_state = AgentState.UNKNOWN
        
        return detected_state

def test_run_command_over_active():
    """Test RUN_001: Run command prioritized over active"""
    print("Test RUN_001: Run command over active")
    
    mock_confidences = {
        'active': 0.90,
        'run_command': 0.82,
        'idle': 0.75
    }
    
    detector = MockTemplateDetector(mock_confidences)
    result = detector.detect_state()
    
    print(f"  Confidences: {mock_confidences}")
    print(f"  Expected: run_command")
    print(f"  Actual: {result}")
    print(f"  Result: {'✅ PASS' if result == AgentState.RUN_COMMAND else '❌ FAIL'}")
    print()
    
    return result == AgentState.RUN_COMMAND

def test_run_command_over_idle():
    """Test RUN_002: Run command prioritized over idle"""
    print("Test RUN_002: Run command over idle")
    
    mock_confidences = {
        'active': 0.75,  # Below threshold
        'run_command': 0.82,
        'idle': 0.95
    }
    
    detector = MockTemplateDetector(mock_confidences)
    result = detector.detect_state()
    
    print(f"  Confidences: {mock_confidences}")
    print(f"  Expected: run_command")
    print(f"  Actual: {result}")
    print(f"  Result: {'✅ PASS' if result == AgentState.RUN_COMMAND else '❌ FAIL'}")
    print()
    
    return result == AgentState.RUN_COMMAND

def test_highest_confidence_no_run_command():
    """Test CONF_001: Highest confidence wins when no run command"""
    print("Test CONF_001: Highest confidence wins (no run command)")
    
    mock_confidences = {
        'active': 0.82,
        'run_command': 0.75,  # Below threshold
        'idle': 0.95
    }
    
    detector = MockTemplateDetector(mock_confidences)
    result = detector.detect_state()
    
    print(f"  Confidences: {mock_confidences}")
    print(f"  Expected: idle")
    print(f"  Actual: {result}")
    print(f"  Result: {'✅ PASS' if result == AgentState.IDLE else '❌ FAIL'}")
    print()
    
    return result == AgentState.IDLE

def test_unknown_when_gap_too_small():
    """Test CONF_002: Unknown when confidence gap too small"""
    print("Test CONF_002: Unknown when gap too small")
    
    mock_confidences = {
        'active': 0.83,
        'run_command': 0.75,  # Below threshold
        'idle': 0.81
    }
    
    detector = MockTemplateDetector(mock_confidences, min_confidence_gap=0.08)
    result = detector.detect_state()
    
    gap = 0.83 - 0.81  # 0.02, less than 0.08
    print(f"  Confidences: {mock_confidences}")
    print(f"  Gap: {gap:.2f} (< 0.08)")
    print(f"  Expected: unknown")
    print(f"  Actual: {result}")
    print(f"  Result: {'✅ PASS' if result == AgentState.UNKNOWN else '❌ FAIL'}")
    print()
    
    return result == AgentState.UNKNOWN

def test_run_command_with_multiple_states():
    """Test RUN_003: Run command over multiple states"""
    print("Test RUN_003: Run command over multiple states")
    
    mock_confidences = {
        'active': 0.95,  # Highest confidence
        'run_command': 0.85,  # Lower but above threshold
        'idle': 0.90
    }
    
    detector = MockTemplateDetector(mock_confidences)
    result = detector.detect_state()
    
    print(f"  Confidences: {mock_confidences}")
    print(f"  Expected: run_command (despite active having highest confidence)")
    print(f"  Actual: {result}")
    print(f"  Result: {'✅ PASS' if result == AgentState.RUN_COMMAND else '❌ FAIL'}")
    print()
    
    return result == AgentState.RUN_COMMAND

def main():
    """Run all priority logic tests."""
    print("=" * 60)
    print("PRIORITY LOGIC UNIT TESTS")
    print("=" * 60)
    print()
    
    tests = [
        test_run_command_over_active,
        test_run_command_over_idle,
        test_highest_confidence_no_run_command,
        test_unknown_when_gap_too_small,
        test_run_command_with_multiple_states
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"❌ {total - passed} tests failed")
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 