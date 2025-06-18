# Architecture Decision Records Index

This document provides a comprehensive index of all Architecture Decision Records (ADRs) for the Cursor Agent Monitor project.

## Quick Stats
- **Total ADRs**: 3
- **Proposed**: 0
- **Accepted**: 3
- **Deprecated**: 0
- **Superseded**: 0

## ADR Index

| ID | Title | Status | Deciders | Date | Superseded By |
|----|-------|--------|----------|------|---------------|
| [ADR-001](ADR-001.md) | Detection Engine Architecture | Accepted | Team | 2025-06-18 | - |
| [ADR-002](ADR-002.md) | Telemetry Storage Solution | Accepted | Team | 2025-06-18 | - |
| [ADR-003](ADR-003.md) | UI Framework Choice | Accepted | Team | 2025-06-18 | - |

*ADRs documenting core architectural decisions for the project*

## ADRs by Status

### Proposed (0)
*No proposed ADRs currently*

### Accepted (3)
- [ADR-001](ADR-001.md): Detection Engine Architecture
- [ADR-002](ADR-002.md): Telemetry Storage Solution  
- [ADR-003](ADR-003.md): UI Framework Choice

### Deprecated (0)
*No deprecated ADRs currently*

### Superseded (0)
*No superseded ADRs currently*

## ADRs by Category

### Architecture & Design
- [ADR-001](ADR-001.md): Detection Engine Architecture - Strategy pattern for state detection

### Technology Choices
- [ADR-002](ADR-002.md): Telemetry Storage Solution - SQLite database selection
- [ADR-003](ADR-003.md): UI Framework Choice - PyObjC/AppKit for native macOS UI

### Integration Patterns
- *Future ADRs will be categorized here*

### Performance & Scalability
- *Future ADRs will be categorized here*

### Security & Privacy
- *Future ADRs will be categorized here*

## Decision Timeline

### 2025-06-18
- Project initialization and documentation structure established
- ADR-001, ADR-002, and ADR-003 created

### Future Decisions
*ADRs will be tracked chronologically here*

## ADR Relationships

```
ADR-XXX (Parent)
├── ADR-YYY (Builds on)
└── ADR-ZZZ (Related to)
```

*Decision dependency graph will be maintained here*

## Recommended ADRs for This Project

Based on the current codebase, consider creating ADRs for:

1. **Detection Engine Architecture** (ADR-001)
   - Strategy pattern vs. other approaches
   - Template matching vs. OCR priorities
   - Confidence scoring algorithms

2. **Telemetry Storage Solution** (ADR-002)
   - SQLite vs. other database options
   - Data schema design decisions
   - Retention and cleanup policies

3. **UI Framework Choice** (ADR-003)
   - PyObjC for native macOS UI
   - Alternative UI approaches considered
   - Cross-platform considerations

4. **State Management Approach** (ADR-004)
   - State machine implementation
   - Event-driven vs. polling architecture
   - Thread safety strategies

5. **Audio System Design** (ADR-005)
   - Sound library selection
   - Caching vs. real-time loading
   - Cross-platform audio considerations

6. **Dependency Injection Pattern** (ADR-006)
   - Container-based DI implementation
   - Alternative patterns considered
   - Testing and mocking strategies

7. **Error Handling Strategy** (ADR-007)
   - Exception vs. error code approaches
   - Graceful degradation policies
   - User notification strategies

8. **Testing Architecture** (ADR-008)
   - Unit vs. integration test balance
   - Mocking strategies for UI testing
   - Acceptance test automation approach

## Maintenance Guidelines

### Creating New ADRs
1. Use the next available ADR-XXX number
2. Copy from `adr-XXX-template.md`
3. Fill in all required sections
4. Update this index file
5. Link to related acceptance tests (ACC-XXX)
6. Get appropriate review and approval

### Updating ADRs
1. **Proposed → Accepted**: Update status and implementation details
2. **Accepted → Deprecated**: Document reason and replacement approach
3. **Accepted → Superseded**: Link to superseding ADR
4. Always update change history

### Review Process
1. **Technical Review**: Architecture and implementation feasibility
2. **Stakeholder Review**: Business impact and requirements alignment
3. **Documentation Review**: Clarity and completeness
4. **Approval**: Final decision and status update

## Integration with Development Process

### Feature Development
- Review related ADRs before implementing features
- Create new ADRs for significant architectural decisions
- Update ADRs when implementation differs from decisions

### Code Review
- Verify code changes align with accepted ADRs
- Flag deviations for discussion
- Suggest new ADRs for emerging patterns

### Testing
- Link acceptance tests (ACC-XXX) to relevant ADRs
- Validate ADR assumptions through testing
- Update ADRs based on testing insights

## Templates and Tools

### Available Templates
- [adr-XXX-template.md](adr-XXX-template.md) - Standard ADR template
- Custom templates can be created for specific decision types

### Decision Support Tools
- Pros/cons analysis framework
- Decision matrix templates
- Stakeholder impact assessment

### Documentation Links
- [Acceptance Tests](../acceptance-tests/) - Related test specifications
- Technical documentation and design docs
- Requirements and user stories

## Change History

| Date | Author | Change Description |
|------|--------|-------------------|
| 2025-06-17 | Team | Initial ADR index structure created |
| 2025-06-18 | Team | Updated dates and created initial ADRs |

## Notes

This index will grow as architectural decisions are made and documented. Regular reviews should ensure decisions remain relevant and aligned with project evolution. 