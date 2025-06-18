# Acceptance Tests

This directory contains acceptance tests for the Cursor Agent Monitor project.

## Files

- **`acceptance-tests.md`** - Main acceptance test document with user stories and requirements

## Usage

### For Development
- Review the acceptance tests before implementing features
- Use requirements as a checklist for feature completion
- Update tests when adding new functionality

### For Testing
- Go through each test manually to verify the application works
- Check off requirements that pass
- Document any failing requirements

### For AI Review
- The single-file format makes it easy for AI to review all tests at once
- AI can validate implementation against the requirements
- Simple format allows for quick updates and modifications

## Adding New Tests

1. Open `acceptance-tests.md`
2. Add a new test section with:
   - User story: "As a user, I want..."
   - Requirements: List of what the app should do
3. Update the version number and date at the top
4. Commit the changes

## Format

Each test follows this simple format:

```markdown
## Test X: Feature Name

**User Story**: As a user, I want [goal] so that [benefit].

**Requirements**:
- The app should [requirement 1]
- The app should [requirement 2]
- The app should [requirement 3]
```

This format is:
- Easy to read and understand
- Simple for AI to parse and validate
- Quick to update and maintain
- Focused on user value and clear requirements 