# Git Strategy and Versioning

This document outlines the git workflow, commit conventions, and versioning strategy for the Cursor Agent Monitor project.

## 🏷️ Versioning Strategy

We use **Semantic Versioning (SemVer)** - `MAJOR.MINOR.PATCH`

### Version Bumping Rules

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backward compatible manner  
- **PATCH** version when you make backward compatible bug fixes

### Examples
- `1.0.0` → `1.0.1` (Bug fix)
- `1.0.0` → `1.1.0` (New feature)
- `1.0.0` → `2.0.0` (Breaking change)

## 📝 Commit Message Convention

We follow **Conventional Commits** specification for clear, standardized commit messages.

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

### Examples
```bash
feat(detection): add run_command state detection

- Implement priority logic for RUN_COMMAND over ACTIVE state
- Add new template matching for Accept/Run buttons
- Include dedicated alert sound for urgent commands

fix(audio): resolve sound playback issues in diagnostic mode

- Move sound playing logic outside diagnostic blocks
- Ensure alerts play regardless of debug settings
- Fix run_command alert not triggering

docs(readme): update installation instructions

- Add macOS-specific setup steps
- Include troubleshooting section
- Update dependency requirements

chore: bump version to 1.0.1
```

## 🌟 Release Process

### 1. Automated Release with Script

```bash
# Patch release (bug fixes)
./release.sh patch

# Minor release (new features)
./release.sh minor

# Major release (breaking changes)
./release.sh major
```

### 2. Manual Release Process

If you prefer manual control:

```bash
# 1. Ensure clean working directory
git status

# 2. Update VERSION file
echo "1.0.1" > VERSION

# 3. Update CHANGELOG.md
# Add your changes under new version section

# 4. Commit version bump
git add VERSION CHANGELOG.md
git commit -m "chore: bump version to 1.0.1"

# 5. Create and push tag
git tag -a v1.0.1 -m "Release 1.0.1"
git push origin main
git push origin v1.0.1
```

## 🌐 Branching Strategy

### Main Branch
- `main`: Production-ready code
- Always stable and deployable
- Protected branch with required reviews

### Feature Development
```bash
# Create feature branch
git checkout -b feat/new-detection-method

# Work on your feature
git add .
git commit -m "feat(detection): implement OCR fallback method"

# Push and create PR
git push origin feat/new-detection-method
```

### Hotfix Process
```bash
# Create hotfix branch from main
git checkout -b hotfix/critical-sound-bug main

# Fix the issue
git commit -m "fix(audio): resolve critical sound playback issue"

# Merge back to main
git checkout main
git merge hotfix/critical-sound-bug
git push origin main

# Create patch release
./release.sh patch
```

## 📋 Pre-commit Checklist

Before committing, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass (`./run_tests.sh`)
- [ ] No console.log or debug prints left in code
- [ ] Documentation updated if needed
- [ ] Commit message follows convention
- [ ] Changes are atomic and focused

## 🔖 Tag Strategy

### Tag Naming
- Release tags: `v1.0.0`, `v1.1.0`, `v2.0.0`
- Pre-release tags: `v1.0.0-beta.1`, `v1.0.0-rc.1`
- Development tags: `v1.0.0-dev.20250106`

### Tag Creation
```bash
# Lightweight tag
git tag v1.0.0

# Annotated tag (recommended)
git tag -a v1.0.0 -m "Release 1.0.0

Major improvements:
- Smart priority logic
- Run command detection
- Enhanced alert system"

# Sign tag with GPG
git tag -s v1.0.0 -m "Release 1.0.0"
```

## 🚀 CI/CD Integration

### GitHub Actions Triggers
- **Push to main**: Run tests, build artifacts
- **Tag push**: Create release, publish artifacts
- **Pull request**: Run tests, validate code

### Release Automation
```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags:
      - 'v*'
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create Release
        uses: actions/create-release@v1
```

## 📊 Maintenance

### Regular Tasks
- **Weekly**: Review and clean up stale branches
- **Monthly**: Audit dependencies for security updates
- **Quarterly**: Review and update documentation

### Branch Cleanup
```bash
# List merged branches
git branch --merged main

# Delete merged feature branches
git branch -d feat/completed-feature

# Delete remote tracking references
git remote prune origin
```

## 🔗 Useful Commands

```bash
# View commit history with graph
git log --oneline --graph --all

# See changes since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Find commits that introduced specific text
git log -S "search_text" --oneline

# Show file changes in last commit
git show --stat

# Interactive rebase to clean up commits
git rebase -i HEAD~3
```

## 📚 References

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Keep a Changelog](https://keepachangelog.com/) 