#!/bin/bash

# Cursor Agent Monitor - Release Script
# Automates versioning, tagging, and release process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log_error "Not in a git repository!"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    log_warning "You have uncommitted changes!"
    echo "Please commit or stash them before creating a release."
    echo ""
    echo "Current status:"
    git status --short
    exit 1
fi

# Get current version
if [ -f "VERSION" ]; then
    CURRENT_VERSION=$(cat VERSION)
    log_info "Current version: ${CURRENT_VERSION}"
else
    log_error "VERSION file not found!"
    exit 1
fi

# Parse command line arguments
RELEASE_TYPE=${1:-patch}  # patch, minor, major

case $RELEASE_TYPE in
    patch|minor|major)
        log_info "Release type: ${RELEASE_TYPE}"
        ;;
    *)
        log_error "Invalid release type: ${RELEASE_TYPE}"
        echo "Usage: $0 [patch|minor|major]"
        echo "  patch: 1.0.0 -> 1.0.1 (bug fixes)"
        echo "  minor: 1.0.0 -> 1.1.0 (new features, backward compatible)"
        echo "  major: 1.0.0 -> 2.0.0 (breaking changes)"
        exit 1
        ;;
esac

# Calculate new version
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

case $RELEASE_TYPE in
    patch)
        PATCH=$((PATCH + 1))
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
TAG_NAME="v${NEW_VERSION}"

log_info "New version will be: ${NEW_VERSION}"

# Confirm release
echo ""
read -p "Create release ${NEW_VERSION}? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Release cancelled."
    exit 0
fi

# Update VERSION file
echo "$NEW_VERSION" > VERSION
log_success "Updated VERSION file to ${NEW_VERSION}"

# Add and commit version bump
git add VERSION
git commit -m "chore: bump version to ${NEW_VERSION}

- Updated VERSION file
- Preparing for release ${TAG_NAME}"

log_success "Committed version bump"

# Create and sign the tag
git tag -a "$TAG_NAME" -m "Release ${NEW_VERSION}

## What's New in ${NEW_VERSION}

See CHANGELOG.md for detailed release notes.

## Quick Start

\`\`\`bash
# Clone the repository
git clone <repository-url>
cd agent_monitor_poc

# Set up environment
./setup.sh

# Run the agent monitor
./run.sh
\`\`\`

## Documentation

- README.md - Project overview and usage
- CHANGELOG.md - Detailed release notes
- DEV_QUICKSTART.md - Development guide
"

log_success "Created tag ${TAG_NAME}"

# Show what was done
echo ""
log_success "Release ${NEW_VERSION} created successfully!"
echo ""
echo "Next steps:"
echo "1. Push the changes and tag:"
echo "   ${YELLOW}git push origin main${NC}"
echo "   ${YELLOW}git push origin ${TAG_NAME}${NC}"
echo ""
echo "2. Create a GitHub release (if using GitHub):"
echo "   - Go to your repository on GitHub"
echo "   - Click 'Releases' -> 'Create a new release'"
echo "   - Select tag ${TAG_NAME}"
echo "   - Copy release notes from CHANGELOG.md"
echo ""
echo "3. Optional: Build and distribute artifacts"
echo "   ${YELLOW}./build.sh${NC} (if you have a build script)"

# Optionally push automatically
echo ""
read -p "Push to origin automatically? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main
    git push origin "$TAG_NAME"
    log_success "Pushed to origin!"
fi

log_success "Release process complete!" 