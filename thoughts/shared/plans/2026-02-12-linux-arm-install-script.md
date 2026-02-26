# Linux ARM64 Installation Script Implementation Plan

## Overview

Create a bash installation script for Linux Debian with ARM processor that automates the setup of the Smart Rover AI Tutor Thonny plugin, including kiro-cli installation, configuration files, and Python package deployment.

## Current State Analysis

### What Exists:
- **Steering directory**: `Steering/` at repository root with 5 markdown documentation files
  - Files: context.md, rules.md, tech.md, content_policy.md, codebase_path.md
- **thonnycontrib package**: `thonnycontrib/smart_rover/` namespace package with full Python implementation
  - Structure: config/, console/, gui/, models/, utils/ subdirectories
  - 16 Python files implementing the Thonny plugin
- **kiro-cli integration**: Plugin wraps external kiro-cli tool (not built in this repo)
  - Commands used: `kiro-cli chat`, `kiro-cli login`, `kiro-cli logout`
  - Credential storage: `~/.local/share/kiro-cli/data.sqlite3`
- **No existing install scripts**: Repository uses pyproject.toml for Python packaging only

### Key Discoveries:
- Official kiro-cli installation: `.deb` package from `https://desktop-release.q.us-east-1.amazonaws.com/latest/kiro-cli.deb` (from https://kiro.dev/docs/cli/installation/)
- kiro-cli installs to `~/.local/bin/` by default
- Thonny plugin path: `~/.config/Thonny/plugins/lib/python3.13/site-packages/`
- kiro-cli settings command format: `kiro-cli settings <key> <value>`

### Constraints:
- Target: Linux Debian with ARM64 (aarch64) processor
- Must handle existing installations (override Steering and thonnycontrib)
- Continue on errors rather than exit immediately
- Update kiro-cli if already installed (always install latest version)

## Desired End State

A single `install.sh` bash script at repository root that:
1. Installs or updates kiro-cli to the latest version
2. Copies Steering documentation to `~/.kiro/steering/`
3. Copies thonnycontrib package to Thonny's plugin directory
4. Configures kiro-cli to disable chat greeting
5. Reports success/failure status for each step
6. Continues execution even if individual steps fail

### Verification:
- [ ] Script executes without syntax errors: `bash -n install.sh`
- [ ] kiro-cli is available: `command -v kiro-cli`
- [ ] Steering files exist: `ls ~/.kiro/steering/*.md`
- [ ] thonnycontrib package exists: `ls ~/.config/Thonny/plugins/lib/python3.13/site-packages/thonnycontrib/smart_rover/__init__.py`
- [ ] Setting is configured: `kiro-cli settings chat.greeting.enabled` returns "false"

## What We're NOT Doing

- Not creating uninstall script
- Not validating Python 3.13 installation
- Not checking Thonny installation or version
- Not handling non-Debian Linux distributions (no RPM/pacman support)
- Not building kiro-cli from source
- Not creating systemd services or startup scripts
- Not handling permissions issues with sudo prompts (user must have appropriate permissions)
- Not creating backup restore functionality

## Implementation Approach

Create a single-phase bash script that:
1. Uses descriptive functions for each installation step
2. Tracks success/failure status without exiting on errors
3. Provides clear user feedback for each operation
4. Uses idempotent operations (safe to run multiple times)
5. Validates prerequisites before main installation steps

## Phase 1: Create Installation Script

### Overview
Write a bash script that orchestrates all installation steps with proper error handling, user feedback, and status tracking.

### Changes Required:

#### 1. Create install.sh at Repository Root
**File**: `install.sh`
**Changes**: Create new bash installation script

```bash
#!/bin/bash

# Smart Rover AI Tutor - Installation Script for Linux ARM64 (Debian)
# This script installs kiro-cli, copies configuration files, and sets up the Thonny plugin

set +e  # Continue on errors
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXIT_CODE=0

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    EXIT_CODE=1
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Check system architecture
check_architecture() {
    print_step "Checking system architecture..."
    ARCH=$(uname -m)
    if [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
        print_success "Detected ARM64 architecture: $ARCH"
        return 0
    else
        print_warning "Expected ARM64 architecture, but detected: $ARCH"
        print_warning "Installation may not work correctly on this system"
        return 0
    fi
}

# Step 2: Check for Debian-based system
check_debian() {
    print_step "Checking for Debian-based system..."
    if command -v dpkg >/dev/null 2>&1; then
        print_success "Debian package manager (dpkg) detected"
        return 0
    else
        print_error "dpkg not found. This script is designed for Debian-based systems."
        return 1
    fi
}

# Step 3: Install or update kiro-cli
install_kiro_cli() {
    print_step "Installing kiro-cli..."

    # Check if kiro-cli is already installed
    IS_INSTALLED=false
    OLD_VERSION="none"
    if command -v kiro-cli >/dev/null 2>&1; then
        IS_INSTALLED=true
        OLD_VERSION=$(kiro-cli --version 2>/dev/null || echo "unknown")
        print_warning "kiro-cli is already installed (version: $OLD_VERSION)"
        print_step "Updating to latest version..."
    fi

    # Download .deb package
    print_step "Downloading kiro-cli.deb..."
    TEMP_DEB=$(mktemp)
    if wget -q --show-progress https://desktop-release.q.us-east-1.amazonaws.com/latest/kiro-cli.deb -O "$TEMP_DEB"; then
        print_success "Downloaded kiro-cli.deb"
    else
        print_error "Failed to download kiro-cli.deb"
        rm -f "$TEMP_DEB"
        return 1
    fi

    # Install package
    print_step "Installing kiro-cli package..."
    if sudo dpkg -i "$TEMP_DEB" 2>/dev/null; then
        print_success "kiro-cli package installed"
    else
        print_warning "dpkg reported errors, attempting to fix dependencies..."
        if sudo apt-get install -f -y >/dev/null 2>&1; then
            print_success "Dependencies fixed, kiro-cli installed"
        else
            print_error "Failed to install kiro-cli"
            rm -f "$TEMP_DEB"
            return 1
        fi
    fi

    # Clean up
    rm -f "$TEMP_DEB"

    # Verify installation
    if command -v kiro-cli >/dev/null 2>&1; then
        NEW_VERSION=$(kiro-cli --version 2>/dev/null || echo "installed")
        if [[ "$IS_INSTALLED" == true ]]; then
            if [[ "$OLD_VERSION" == "$NEW_VERSION" ]]; then
                print_success "kiro-cli is up to date (version: $NEW_VERSION)"
            else
                print_success "kiro-cli updated: $OLD_VERSION → $NEW_VERSION"
            fi
        else
            print_success "kiro-cli successfully installed (version: $NEW_VERSION)"
        fi
        return 0
    else
        print_error "kiro-cli installation verification failed"
        return 1
    fi
}

# Step 4: Copy Steering directory
copy_steering() {
    print_step "Copying Steering configuration..."

    SOURCE_DIR="$SCRIPT_DIR/Steering"
    DEST_DIR="$HOME/.kiro/steering"

    # Check source directory exists
    if [[ ! -d "$SOURCE_DIR" ]]; then
        print_error "Steering directory not found at: $SOURCE_DIR"
        return 1
    fi

    # Create parent directory if needed
    mkdir -p "$HOME/.kiro"

    # Remove existing destination if it exists
    if [[ -d "$DEST_DIR" ]]; then
        print_warning "Removing existing Steering directory at: $DEST_DIR"
        rm -rf "$DEST_DIR"
    fi

    # Copy directory
    if cp -r "$SOURCE_DIR" "$DEST_DIR"; then
        FILE_COUNT=$(find "$DEST_DIR" -type f | wc -l)
        print_success "Copied Steering directory ($FILE_COUNT files) to: $DEST_DIR"
        return 0
    else
        print_error "Failed to copy Steering directory"
        return 1
    fi
}

# Step 5: Copy thonnycontrib package
copy_thonnycontrib() {
    print_step "Copying thonnycontrib plugin..."

    SOURCE_DIR="$SCRIPT_DIR/thonnycontrib"
    DEST_DIR="$HOME/.config/Thonny/plugins/lib/python3.13/site-packages/thonnycontrib"

    # Check source directory exists
    if [[ ! -d "$SOURCE_DIR" ]]; then
        print_error "thonnycontrib directory not found at: $SOURCE_DIR"
        return 1
    fi

    # Create parent directory if needed
    mkdir -p "$(dirname "$DEST_DIR")"

    # Remove existing destination if it exists
    if [[ -d "$DEST_DIR" ]]; then
        print_warning "Removing existing thonnycontrib directory at: $DEST_DIR"
        rm -rf "$DEST_DIR"
    fi

    # Copy directory
    if cp -r "$SOURCE_DIR" "$DEST_DIR"; then
        FILE_COUNT=$(find "$DEST_DIR" -type f -name "*.py" | wc -l)
        print_success "Copied thonnycontrib package ($FILE_COUNT .py files) to: $DEST_DIR"

        # Verify key files exist
        if [[ -f "$DEST_DIR/smart_rover/__init__.py" ]]; then
            print_success "Verified plugin entry point exists"
            return 0
        else
            print_error "Plugin entry point not found after copy"
            return 1
        fi
    else
        print_error "Failed to copy thonnycontrib directory"
        return 1
    fi
}

# Step 6: Configure kiro-cli settings
configure_kiro_cli() {
    print_step "Configuring kiro-cli settings..."

    # Check if kiro-cli is available
    if ! command -v kiro-cli >/dev/null 2>&1; then
        print_error "kiro-cli not found in PATH, cannot configure settings"
        return 1
    fi

    # Set chat.greeting.enabled to false
    if kiro-cli settings chat.greeting.enabled false >/dev/null 2>&1; then
        print_success "Disabled chat greeting: chat.greeting.enabled = false"
        return 0
    else
        print_warning "Failed to set kiro-cli setting (may require authentication)"
        print_warning "Run manually after login: kiro-cli settings chat.greeting.enabled false"
        return 0
    fi
}

# Main installation flow
main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  Smart Rover AI Tutor - Linux ARM64 Installation Script       ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    check_architecture
    check_debian
    install_kiro_cli
    copy_steering
    copy_thonnycontrib
    configure_kiro_cli

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"

    if [[ $EXIT_CODE -eq 0 ]]; then
        echo "║  ${GREEN}✓ Installation completed successfully!${NC}                         ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Next steps:"
        echo "  1. Launch Thonny IDE"
        echo "  2. Open Tools → Kiro"
        echo "  3. Click 'Login' to authenticate with kiro-cli"
        echo "  4. Start using the Smart Rover AI Tutor!"
    else
        echo "║  ${YELLOW}⚠ Installation completed with some errors${NC}                      ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Please review the error messages above and fix any issues."
        echo "You can re-run this script after resolving the errors."
    fi

    exit $EXIT_CODE
}

# Run main installation
main
```

### Success Criteria:

#### Automated Verification:
- [ ] Script has no syntax errors: `bash -n install.sh`
- [ ] Script is executable: `chmod +x install.sh && test -x install.sh`
- [ ] Script detects ARM64 architecture correctly on target system
- [ ] Script verifies dpkg is available on Debian systems

#### Manual Verification:
- [ ] Run script on Debian ARM64 system: `./install.sh`
- [ ] Verify kiro-cli is installed: `kiro-cli --version`
- [ ] Verify Steering files copied: `ls -la ~/.kiro/steering/` shows 5 .md files
- [ ] Verify thonnycontrib copied: `ls -la ~/.config/Thonny/plugins/lib/python3.13/site-packages/thonnycontrib/smart_rover/` shows package structure
- [ ] Verify setting configured: `kiro-cli settings chat.greeting.enabled` returns "false" (may require login first)
- [ ] Launch Thonny and verify plugin appears in Tools menu
- [ ] Verify plugin loads without errors in Thonny console

**Implementation Note**: The script uses "continue on errors" approach with status tracking. Each step reports success/failure but doesn't halt execution. At the end, script exits with code 0 (success) or 1 (errors occurred).

---

## Testing Strategy

### Pre-Installation Tests:
- Verify script on local system: `bash -n install.sh`
- Test architecture detection: `uname -m` should return "aarch64"
- Verify source files exist: `ls Steering/` and `ls thonnycontrib/`

### Installation Tests:
Run on clean Debian ARM64 system:
1. Execute script: `./install.sh`
2. Verify each step reports success (green checkmarks)
3. Check kiro-cli: `which kiro-cli` and `kiro-cli --version`
4. Check Steering: `cat ~/.kiro/steering/context.md`
5. Check thonnycontrib: `python3 -c "import sys; sys.path.append('$HOME/.config/Thonny/plugins/lib/python3.13/site-packages'); from thonnycontrib.smart_rover import load_plugin; print('OK')"`

### Re-Run Tests (Idempotency):
Run script a second time to verify it handles existing installations:
1. Execute again: `./install.sh`
2. Verify kiro-cli update check occurs (should show "already installed" then update/verify latest version)
3. Verify Steering and thonnycontrib get replaced
4. No errors should occur

### Integration Tests:
1. Launch Thonny IDE
2. Check Tools menu contains "Kiro" option
3. Open Kiro panel, verify terminal UI appears
4. Click Login button, complete authentication
5. Run help command in terminal
6. Verify no startup errors in Thonny console

## Dependencies

### System Requirements:
- Linux Debian or Ubuntu (ARM64/aarch64)
- dpkg package manager
- wget (for downloading .deb)
- sudo privileges (for dpkg installation)
- Internet connection (for downloading kiro-cli)

### Thonny Requirements:
- Thonny IDE installed (version 4-6)
- Python 3.13 (as specified in destination path)

### Runtime Dependencies:
- bash shell (version 4.0+)
- Standard Unix tools: cp, rm, mkdir, find, wc

## Performance Considerations

- **Download size**: kiro-cli.deb is typically 5-20 MB (one-time download)
- **Disk space**: ~50 MB total for kiro-cli + plugin files
- **Execution time**: 30-60 seconds typical (depends on internet speed)
- **No performance impact** on Thonny runtime - files copied once during installation

## Migration Notes

### Upgrading from Manual Installation:
- Script will override existing Steering and thonnycontrib directories
- No backup is created (force fresh install as specified)
- Users should manually backup custom modifications before running

### Path Differences:
- If user installed thonnycontrib via pip, it may be in different site-packages
- This script installs to user-level Thonny plugins directory, not system Python
- Multiple installations possible (system vs Thonny) - Thonny will use its plugins directory

### Python Version Dependency:
- Script hardcodes Python 3.13 in path: `python3.13/site-packages`
- If Thonny uses different Python version, path must be adjusted
- Future enhancement: Auto-detect Python version used by Thonny

## References

- kiro-cli installation docs: https://kiro.dev/docs/cli/installation/
- kiro-cli .deb package: https://desktop-release.q.us-east-1.amazonaws.com/latest/kiro-cli.deb
- Thonny plugin structure: `thonnycontrib` namespace package convention
- Existing codebase: `thonnycontrib/smart_rover/__init__.py:1-21` (plugin entry point)
- Configuration files: `Steering/` directory (5 markdown files)
