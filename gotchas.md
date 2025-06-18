# PyObjC Agent Monitor Development Gotchas

## Method Naming Conventions

### Issue: Incorrect Objective-C Method Signatures
When translating Objective-C methods to Python using PyObjC, method naming conventions are crucial:

- ❌ Wrong: `createStyledBox_withFrame_title(self, frame, title)`
- ✅ Correct: `createStyledBox_withFrame_title_(self, frame, title)`

**Key Rules:**
1. Each colon (`:`) in Objective-C becomes an underscore (`_`) in Python
2. The method name MUST end with an underscore
3. Number of underscores must match the number of arguments
4. Maintain camelCase naming (starting with lowercase)

### Examples:
```objc
// Objective-C
-(void)createStyledBox:(NSRect)frame withTitle:(NSString*)title;
```
```python
# Python
def createStyledBox_withTitle_(self, frame, title):
```

## Window Styling

### Issue: Window Transparency and Corners
- Window styling needs specific method calls in the correct order
- Background color and opacity settings must be properly configured

**Solution:**
```python
def setupWindow(self):
    self.window.setBackgroundColor_(NSColor.clearColor())
    self.window.setOpaque_(False)
    # Additional styling as needed
```

## Debug Visualization

### Issue: Template Matching Validation
- Template matching confidence scores vary (0.75-0.88)
- Need visual feedback for accuracy verification

**Solution:**
- Added debug visualization toggle
- Store screenshots and detection rectangles
- Display match confidence scores
- Track statistics (detections, failures, last detection time)

## Error Handling

### Issue: Run Script Failures
- Initial run.sh script had reliability issues
- Error handling was insufficient

**Solution:**
- Improved error handling in run.sh
- Added proper logging
- Implemented graceful failure handling

## State Management

### Issue: Application State Control
- Needed reliable pause/resume functionality
- Required mute/unmute controls

**Solution:**
- Implemented proper state tracking
- Added atomic state transitions
- Created clear visual indicators for current state

## Best Practices Learned

1. **Method Signatures:**
   - Always verify PyObjC method signatures carefully
   - Test with small examples before implementing in main code
   - Keep documentation handy for reference

2. **UI Development:**
   - Use dark mode compatible colors
   - Implement proper window styling early
   - Consider debug visualization during development

3. **Error Handling:**
   - Add comprehensive error handling from the start
   - Include detailed logging
   - Plan for graceful degradation

4. **Testing:**
   - Test edge cases for button detection
   - Verify state transitions
   - Validate UI responsiveness

5. **Documentation:**
   - Document version-specific requirements
   - Keep track of gotchas as they're discovered
   - Include examples of both incorrect and correct implementations 