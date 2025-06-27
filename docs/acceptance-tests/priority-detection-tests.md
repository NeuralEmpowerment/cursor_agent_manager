# Priority Detection Acceptance Tests

## Overview
This document defines the acceptance criteria for state detection priority logic in the Agent Monitor system.

## Test Categories

### 1. Run Command Priority Tests

#### Test: RUN_001 - Run Command Over Active
**Given:** Both `run_command` and `active` states are detected with confidence ≥ threshold  
**When:** The detection system evaluates priority  
**Then:** `run_command` state should be selected regardless of confidence differences  
**Rationale:** Run commands require immediate user action and should always be prioritized

**Example Scenario:**
```
Confidence scores:
- active: 0.85 (above threshold)
- run_command: 0.82 (above threshold)
Expected result: run_command (despite lower confidence)
```

#### Test: RUN_002 - Run Command Over Idle
**Given:** Both `run_command` and `idle` states are detected with confidence ≥ threshold  
**When:** The detection system evaluates priority  
**Then:** `run_command` state should be selected  
**Rationale:** Commands waiting for execution take priority over idle waiting

#### Test: RUN_003 - Run Command Over Multiple States
**Given:** `run_command`, `active`, and `idle` all detected with confidence ≥ threshold  
**When:** The detection system evaluates priority  
**Then:** `run_command` state should be selected regardless of other confidence scores  

### 2. Confidence-Based Selection Tests

#### Test: CONF_001 - Highest Confidence Wins (No Run Command)
**Given:** Only `active` and `idle` states detected with confidence ≥ threshold  
**When:** The detection system evaluates priority  
**Then:** The state with highest confidence should be selected if confidence gap ≥ min_gap  

**Example Scenario:**
```
Confidence scores:
- idle: 0.95
- active: 0.82
- Gap: 0.13 (> min_gap of 0.08)
Expected result: idle
```

#### Test: CONF_002 - Unknown When Gap Too Small
**Given:** Multiple states detected with confidence ≥ threshold  
**And:** Confidence gap < min_confidence_gap  
**When:** The detection system evaluates priority  
**Then:** State should be `unknown` to prevent flickering  

**Example Scenario:**
```
Confidence scores:
- idle: 0.85
- active: 0.82
- Gap: 0.03 (< min_gap of 0.08)
Expected result: unknown
```

### 3. Threshold Tests

#### Test: THRESH_001 - Below Threshold Ignored
**Given:** A state has confidence < confidence_threshold  
**When:** The detection system evaluates states  
**Then:** That state should not be considered for selection  

#### Test: THRESH_002 - Single Valid State
**Given:** Only one state has confidence ≥ threshold  
**When:** The detection system evaluates states  
**Then:** That state should be selected regardless of confidence level  

### 4. Template Quality Warning Tests

#### Test: WARN_001 - Multiple High Confidence Warning
**Given:** Multiple states have confidence ≥ 0.95  
**When:** The detection system processes results  
**Then:** A template warning should be displayed in diagnostic mode  
**Rationale:** High confidence across multiple states suggests overly generic templates

#### Test: WARN_002 - Single Perfect Match No Warning
**Given:** Only one state has confidence ≥ 0.95  
**When:** The detection system processes results  
**Then:** No template warning should be displayed  
**Rationale:** Perfect matches are good when they're unique

### 5. State Stability Tests

#### Test: STAB_001 - Confirmation Requirements
**Given:** A state is detected  
**When:** It hasn't been consistently detected for required_confirmations cycles  
**Then:** The detector should return the unstable state but monitor should wait for stability  

#### Test: STAB_002 - State Change Timing
**Given:** A new stable state is detected  
**And:** Less than min_state_change_interval has passed since last change  
**When:** The detection system evaluates  
**Then:** State changes should be rate-limited to prevent rapid switching  

## Priority Matrix

| Scenario | Run Command | Active | Idle | Expected Result |
|----------|-------------|---------|-------|----------------|
| R=0.9, A=0.95, I=0.85 | ✓ | ✓ | ✓ | run_command |
| R=0.7, A=0.95, I=0.85 | ✗ | ✓ | ✓ | idle (highest) |
| R=0.9, A=0.7, I=0.85 | ✓ | ✗ | ✓ | run_command |
| R=0.7, A=0.82, I=0.85 | ✗ | ✓ | ✓ | idle (highest) |
| R=0.7, A=0.83, I=0.81 | ✗ | ✓ | ✓ | unknown (gap < 0.08) |

*Legend: ✓ = above threshold (0.8), ✗ = below threshold*

## Configuration Values for Tests

```python
CONFIDENCE_THRESHOLD = 0.8
MIN_CONFIDENCE_GAP = 0.08
REQUIRED_CONFIRMATIONS = 2
MIN_STATE_CHANGE_INTERVAL = 5
```

## Test Implementation

### Automated Test Structure
```python
def test_run_command_priority():
    """Test RUN_001: Run command prioritized over active"""
    detector = create_test_detector()
    mock_confidences = {
        'active': 0.85,
        'run_command': 0.82,
        'idle': 0.75
    }
    result = detector.detect_with_mock_confidences(mock_confidences)
    assert result == AgentState.RUN_COMMAND
```

### Manual Test Scenarios
1. **Run Command Priority**: Trigger both active and run_command states simultaneously
2. **Confidence Gap**: Test edge cases around the 0.08 gap threshold  
3. **Template Quality**: Use overly generic templates to trigger warnings
4. **State Stability**: Rapidly switch between states to test stability logic

## Success Criteria

- ✅ Run commands always prioritized when above threshold
- ✅ Highest confidence wins when no run command present
- ✅ Unknown state prevents flickering on close confidence scores
- ✅ Template quality warnings help identify generic templates
- ✅ State changes are stable and rate-limited appropriately

## Related Documentation

- [ADR-001: Detection Strategy](../adrs/ADR-001.md) - Original architecture decision
- [Template Directory Structure](../../assets/ui-cursor/README.md) - Template organization
- [Configuration Guide](../../README.md#configuration) - Tuning parameters 