# Cursor Rules

See [.context](../context/index.md) for the context in which these rules are used.

- [Cursor Rules](#cursor-rules)
  - [Development Process](#development-process)
  - [Style Guide](#style-guide)

## Development Process

Build the project incrementally in well-defined stages. Start with foundational components like base configuration and project setup. Before proceeding to the next stage, ensure all current work:

- Builds successfully
- Passes all tests
- Meets linting requirements
- Functions as expected

Commit changes frequently to create clear snapshots of working progress. Don't let uncommitted changes accumulate - this helps maintain a clean, trackable development history and makes troubleshooting easier.

## Style Guide

1. No default exports
2. Class name and class files names should be PascalCase
3. index.ts files should only be used to export from other files. Files which contain logic, like classes, should have a descriptive name. (i.e. PascalClass = PascalClass.ts)
