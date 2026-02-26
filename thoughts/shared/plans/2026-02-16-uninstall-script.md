# Smart Rover AI Tutor Uninstaller Implementation Plan

## Overview

Create a bash uninstallation script for Linux Debian ARM64 that completely removes the Smart Rover AI Tutor Thonny plugin, including kiro-cli package, configuration files, plugin files, and user data.

## Current State Analysis

### What Exists:
- **Installation script**: `install.sh` at repository root that installs all components
- **Desktop launcher**: `smart-rover-installer.desktop` file (not installed by script)
- **Installed components** (when installed):
  - kiro-cli package installed via dpkg at system level
  - Steering config directory: `~/.kiro/steering/` (5 markdown files)
  - thonnycontrib plugin: `~/.config/Thonny/plugins/lib/python{VERSION}/site-packages/thonnycontrib/smart_rover/`
  - kiro-cli user data: `~/.kiro/` directory containing credentials, settings, conversation history
  - kiro-cli setting modified: `chat.greeting.enabled = false`

### Key Discoveries from Installation Analysis:
- Installation plan exists: `thoughts/shared/plans/2026-02-12-linux-arm-install-script.md`
- Installation targets multiple locations requiring different removal approaches
- Python version detection logic: Checks versions 3.15 down to 3.7 (install.sh:169-175)
- kiro-cli installed via dpkg, can be removed with `sudo dpkg -r kiro-cli`
- Desktop launcher file not installed by script, likely copied manually by user
- Some installations may have multiple Python version directories with duplicate plugin files

### Constraints:
- Target: Linux Debian with ARM64 (aarch64) processor (same as installer)
- Must handle partial installations gracefully (some components may not exist)
- Continue on errors rather than exit immediately (same pattern as installer)
- Safe to run multiple times (idempotent operations)
- Should provide clear feedback on what was/wasn't removed

## Desired End State

A single `uninstall.sh` bash script at repository root that:
1. Removes kiro-cli package completely via dpkg
2. Removes entire `~/.kiro/` directory (includes steering config, credentials, settings, conversation history)
3. Removes thonnycontrib plugin from all detected Python version directories in Thonny
4. Checks for and reports on desktop launcher file (provides manual removal instructions)
5. Reports success/failure status for each step
6. Continues execution even if individual steps fail
7. Provides summary of what was removed and what remains

### Verification:
- [ ] Script executes without syntax errors: `bash -n uninstall.sh`
- [ ] kiro-cli is not available: `command -v kiro-cli` returns non-zero exit code
- [ ] Steering directory removed: `test ! -d ~/.kiro/`
- [ ] thonnycontrib packages removed: `find ~/.config/Thonny/plugins/lib/python*/site-packages/thonnycontrib/smart_rover -type d 2>/dev/null` returns nothing
- [ ] Script reports what was found and removed
- [ ] Script is safe to run multiple times without errors

## What We're NOT Doing

- Not removing Thonny IDE itself
- Not removing Python or system packages (except kiro-cli)
- Not creating backup/restore functionality
- Not removing the uninstaller script itself
- Not removing the repository or source files
- Not handling Windows or macOS uninstallation
- Not removing system-wide Python packages (only user-level Thonny plugins)
- Not automatically removing desktop launcher file (user may have customized location)

## Implementation Approach

Create a single-phase bash script that:
1. Mirrors the installer's structure and style for consistency
2. Uses descriptive functions for each uninstallation step
3. Tracks success/failure status without exiting on errors
4. Provides clear user feedback matching installer's output format
5. Detects what's installed before attempting removal
6. Handles edge cases (partial installs, missing components)
7. Provides manual cleanup instructions for items it cannot remove automatically

## Phase 1: Create Uninstallation Script

### Overview
Write a bash script that removes all components installed by `install.sh`, using the same structure, color scheme, and error handling patterns for user familiarity.

### Changes Required:

#### 1. Create uninstall.sh at Repository Root
**File**: `uninstall.sh`
**Changes**: Create new bash uninstallation script

```bash
#!/bin/bash

# Smart Rover AI Tutor - Uninstallation Script for Linux ARM64 (Debian)
# This script removes kiro-cli, configuration files, and the Thonny plugin

set +e  # Continue on errors
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXIT_CODE=0
ITEMS_REMOVED=0
ITEMS_NOT_FOUND=0

# Color codes for output (matching install.sh)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions (matching install.sh)
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ITEMS_REMOVED=$((ITEMS_REMOVED + 1))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    EXIT_CODE=1
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_not_found() {
    echo -e "${YELLOW}○${NC} $1 (not found, skipping)"
    ITEMS_NOT_FOUND=$((ITEMS_NOT_FOUND + 1))
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
        print_warning "Continuing anyway - uninstallation should work on any architecture"
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
        print_warning "dpkg not found. kiro-cli removal will be skipped."
        return 0
    fi
}

# Step 3: Uninstall kiro-cli package
uninstall_kiro_cli() {
    print_step "Uninstalling kiro-cli package..."

    # Check if kiro-cli is installed
    if ! command -v kiro-cli >/dev/null 2>&1; then
        print_not_found "kiro-cli"
        return 0
    fi

    # Get current version before uninstalling
    CURRENT_VERSION=$(kiro-cli --version 2>/dev/null || echo "unknown")
    print_step "Found kiro-cli version: $CURRENT_VERSION"

    # Check if package is installed via dpkg
    if ! dpkg -l kiro-cli >/dev/null 2>&1; then
        print_warning "kiro-cli command exists but package not found in dpkg"
        print_warning "May have been installed manually - cannot remove automatically"
        return 1
    fi

    # Uninstall package
    print_step "Removing kiro-cli package..."
    if sudo dpkg -r kiro-cli >/dev/null 2>&1; then
        print_success "kiro-cli package removed"
    else
        print_error "Failed to remove kiro-cli package"
        print_warning "Try manually: sudo dpkg -r kiro-cli"
        return 1
    fi

    # Verify removal
    if ! command -v kiro-cli >/dev/null 2>&1; then
        print_success "Verified kiro-cli is no longer available"
        return 0
    else
        print_warning "kiro-cli command still exists after removal"
        print_warning "May be installed in multiple locations"
        return 1
    fi
}

# Step 4: Remove .kiro directory (includes steering config, credentials, settings, conversation history)
remove_kiro_directory() {
    print_step "Removing ~/.kiro/ directory..."

    KIRO_DIR="$HOME/.kiro"

    # Check if directory exists
    if [[ ! -d "$KIRO_DIR" ]]; then
        print_not_found "~/.kiro/ directory"
        return 0
    fi

    # Count files before removal
    FILE_COUNT=$(find "$KIRO_DIR" -type f 2>/dev/null | wc -l)
    DIR_SIZE=$(du -sh "$KIRO_DIR" 2>/dev/null | cut -f1)

    print_step "Found ~/.kiro/ directory ($FILE_COUNT files, $DIR_SIZE)"
    print_warning "This will remove all kiro-cli data including:"
    print_warning "  - Steering configuration"
    print_warning "  - Authentication credentials"
    print_warning "  - Settings and preferences"
    print_warning "  - Conversation history"

    # Remove directory
    if rm -rf "$KIRO_DIR" 2>/dev/null; then
        print_success "Removed ~/.kiro/ directory ($FILE_COUNT files)"

        # Verify removal
        if [[ ! -d "$KIRO_DIR" ]]; then
            return 0
        else
            print_error "Directory still exists after removal"
            return 1
        fi
    else
        print_error "Failed to remove ~/.kiro/ directory"
        print_warning "Try manually: rm -rf ~/.kiro"
        return 1
    fi
}

# Step 5: Remove thonnycontrib plugin from all Python versions
remove_thonnycontrib() {
    print_step "Removing thonnycontrib plugin from Thonny..."

    THONNY_LIB_DIR="$HOME/.config/Thonny/plugins/lib"
    FOUND_ANY=false
    REMOVED_COUNT=0

    # Check if Thonny plugins directory exists
    if [[ ! -d "$THONNY_LIB_DIR" ]]; then
        print_not_found "Thonny plugins directory"
        return 0
    fi

    # Check all Python versions from 3.15 down to 3.7
    for version in 3.15 3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7; do
        PLUGIN_DIR="$THONNY_LIB_DIR/python$version/site-packages/thonnycontrib"

        if [[ -d "$PLUGIN_DIR" ]]; then
            FOUND_ANY=true
            FILE_COUNT=$(find "$PLUGIN_DIR" -type f -name "*.py" 2>/dev/null | wc -l)

            print_step "Found plugin in Python $version ($FILE_COUNT .py files)"

            # Remove thonnycontrib directory
            if rm -rf "$PLUGIN_DIR" 2>/dev/null; then
                print_success "Removed plugin from Python $version"
                REMOVED_COUNT=$((REMOVED_COUNT + 1))

                # Verify removal
                if [[ -d "$PLUGIN_DIR" ]]; then
                    print_error "Plugin directory still exists after removal"
                fi
            else
                print_error "Failed to remove plugin from Python $version"
                print_warning "Try manually: rm -rf $PLUGIN_DIR"
            fi
        fi
    done

    if [[ "$FOUND_ANY" == false ]]; then
        print_not_found "thonnycontrib plugin in any Python version"
        return 0
    fi

    if [[ $REMOVED_COUNT -gt 0 ]]; then
        print_success "Removed plugin from $REMOVED_COUNT Python version(s)"
        return 0
    else
        print_error "Found plugin(s) but failed to remove any"
        return 1
    fi
}

# Step 6: Check for desktop launcher file
check_desktop_launcher() {
    print_step "Checking for desktop launcher file..."

    # Common desktop file locations
    LOCATIONS=(
        "$HOME/.local/share/applications/smart-rover-installer.desktop"
        "$HOME/Desktop/smart-rover-installer.desktop"
        "/usr/share/applications/smart-rover-installer.desktop"
        "/usr/local/share/applications/smart-rover-installer.desktop"
    )

    FOUND_LOCATIONS=()

    # Check each location
    for location in "${LOCATIONS[@]}"; do
        if [[ -f "$location" ]]; then
            FOUND_LOCATIONS+=("$location")
        fi
    done

    if [[ ${#FOUND_LOCATIONS[@]} -eq 0 ]]; then
        print_not_found "Desktop launcher file"
        return 0
    fi

    # Report found locations
    print_warning "Found desktop launcher file(s) at:"
    for location in "${FOUND_LOCATIONS[@]}"; do
        echo "  - $location"
    done
    print_warning "These were not installed by the installer and should be removed manually if desired"
    print_warning "To remove manually, run:"
    for location in "${FOUND_LOCATIONS[@]}"; do
        echo "    rm \"$location\""
    done

    return 0
}

# Step 7: Clean up empty parent directories
cleanup_empty_dirs() {
    print_step "Cleaning up empty parent directories..."

    CLEANED_ANY=false

    # Remove empty Thonny site-packages directories
    THONNY_LIB_DIR="$HOME/.config/Thonny/plugins/lib"
    if [[ -d "$THONNY_LIB_DIR" ]]; then
        for version in 3.15 3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7; do
            SITE_PACKAGES="$THONNY_LIB_DIR/python$version/site-packages"
            if [[ -d "$SITE_PACKAGES" ]] && [[ -z "$(ls -A "$SITE_PACKAGES" 2>/dev/null)" ]]; then
                rmdir "$SITE_PACKAGES" 2>/dev/null && print_success "Removed empty directory: python$version/site-packages"
                CLEANED_ANY=true
            fi

            PYTHON_DIR="$THONNY_LIB_DIR/python$version"
            if [[ -d "$PYTHON_DIR" ]] && [[ -z "$(ls -A "$PYTHON_DIR" 2>/dev/null)" ]]; then
                rmdir "$PYTHON_DIR" 2>/dev/null && print_success "Removed empty directory: python$version"
                CLEANED_ANY=true
            fi
        done
    fi

    if [[ "$CLEANED_ANY" == false ]]; then
        print_not_found "Empty directories to clean up"
    fi

    return 0
}

# Main uninstallation flow
main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  Smart Rover AI Tutor - Linux ARM64 Uninstallation Script     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "This will remove:"
    echo "  • kiro-cli package (complete removal)"
    echo "  • ~/.kiro/ directory (configuration, credentials, history)"
    echo "  • Thonny plugin files (all Python versions)"
    echo ""
    echo "WARNING: This operation cannot be undone!"
    echo ""
    read -p "Do you want to continue? (yes/no): " -r REPLY
    echo ""

    if [[ ! "$REPLY" =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Uninstallation cancelled by user."
        exit 0
    fi

    check_architecture
    check_debian
    uninstall_kiro_cli
    remove_kiro_directory
    remove_thonnycontrib
    check_desktop_launcher
    cleanup_empty_dirs

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"

    if [[ $EXIT_CODE -eq 0 ]]; then
        echo "║  ${GREEN}✓ Uninstallation completed successfully!${NC}                       ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Summary:"
        echo "  • Items removed: $ITEMS_REMOVED"
        echo "  • Items not found: $ITEMS_NOT_FOUND"
        echo ""
        echo "Smart Rover AI Tutor has been completely removed from your system."

        if command -v thonny >/dev/null 2>&1; then
            echo ""
            echo "Note: Thonny IDE is still installed. If you want to remove it:"
            echo "  sudo apt remove thonny"
        fi
    else
        echo "║  ${YELLOW}⚠ Uninstallation completed with some errors${NC}                    ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Summary:"
        echo "  • Items removed: $ITEMS_REMOVED"
        echo "  • Items not found: $ITEMS_NOT_FOUND"
        echo ""
        echo "Please review the error messages above and clean up manually if needed."
    fi

    echo ""
    read -p "Press Enter to close this window..."
    exit $EXIT_CODE
}

# Run main uninstallation
main
```

#### 2. Create Desktop Launcher for Uninstaller (Optional)
**File**: `smart-rover-uninstaller.desktop`
**Changes**: Create new desktop launcher file for easy access to uninstaller

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Smart Rover AI Tutor Uninstaller
Comment=Uninstall Smart Rover AI Tutor plugin from Thonny IDE
Exec=bash -c 'DIR="$(dirname "$(realpath "$1" 2>/dev/null || readlink -f "$1" 2>/dev/null || echo "$1")")/smart-rover-ai-tutor"; echo "Directory: $DIR"; cd "$DIR" || exit 1; chmod +x uninstall.sh 2>/dev/null; if [ -f uninstall.sh ]; then bash uninstall.sh; else echo "Error: uninstall.sh not found in $DIR"; fi; echo ""; read -p "Press Enter to close..."' _ %k
Icon=user-trash
Terminal=true
Categories=Development;Education;
```

#### 3. Update README.md with Uninstallation Instructions
**File**: `README.md`
**Changes**: Add uninstallation section after installation instructions

Find the installation section and add after it:

```markdown
## Uninstallation

To completely remove Smart Rover AI Tutor from your system:

### Option 1: Using the Uninstall Script

1. Navigate to the repository directory
2. Run the uninstallation script:
   ```bash
   chmod +x uninstall.sh
   ./uninstall.sh
   ```

### Option 2: Using the Desktop Launcher (if available)

Double-click the `smart-rover-uninstaller.desktop` file and follow the prompts.

### What Gets Removed

The uninstaller removes:
- **kiro-cli package**: Complete removal via dpkg
- **Configuration directory**: `~/.kiro/` including credentials, settings, and conversation history
- **Thonny plugin**: All Python version installations in `~/.config/Thonny/plugins/`
- **Empty directories**: Cleanup of empty parent directories

**Note**: Thonny IDE itself is not removed. To remove Thonny:
```bash
sudo apt remove thonny
```

### Manual Uninstallation

If the script doesn't work or you prefer manual removal:

```bash
# Remove kiro-cli package
sudo dpkg -r kiro-cli

# Remove configuration and data
rm -rf ~/.kiro/

# Remove Thonny plugin (check your Python version)
rm -rf ~/.config/Thonny/plugins/lib/python*/site-packages/thonnycontrib/smart_rover/

# Remove desktop launcher files (if copied manually)
rm ~/.local/share/applications/smart-rover-*.desktop
rm ~/Desktop/smart-rover-*.desktop
```
```

### Success Criteria:

#### Automated Verification:
- [x] Script has no syntax errors: `bash -n uninstall.sh`
- [x] Script is executable: `chmod +x uninstall.sh && test -x uninstall.sh`
- [x] Desktop launcher has correct format and points to uninstall.sh

#### Manual Verification:
- [ ] Run script on system with Smart Rover installed: `./uninstall.sh`
- [ ] Confirm user prompt appears and works correctly (yes/no)
- [ ] Verify kiro-cli is removed: `command -v kiro-cli` returns non-zero
- [ ] Verify .kiro directory is removed: `test ! -d ~/.kiro && echo "Removed"`
- [ ] Verify plugin removed from all Python versions: `find ~/.config/Thonny/plugins/lib/python*/site-packages/thonnycontrib/smart_rover -type d 2>/dev/null` returns nothing
- [ ] Run script second time on already uninstalled system - should complete without errors
- [ ] Verify summary shows correct count of removed/not-found items
- [ ] Check that Thonny still launches (if installed)
- [ ] Verify desktop launcher file is detected and reported with manual removal instructions

**Implementation Note**: The script uses the same "continue on errors" approach as the installer, with detailed status tracking. It reports what was found and removed, what wasn't found, and what failed. User confirmation is required before proceeding with removal.

---

## Testing Strategy

### Unit Tests:
- Script syntax validation: `bash -n uninstall.sh`
- Check executable permissions work: `chmod +x uninstall.sh`
- Verify color codes render correctly in terminal
- Test confirmation prompt (yes/no/invalid input)

### Integration Tests on Fresh Install:
1. Install Smart Rover using `install.sh`
2. Verify all components are installed
3. Run `uninstall.sh`
4. Confirm user prompt works
5. Verify all components removed:
   - `command -v kiro-cli` fails
   - `~/.kiro/` doesn't exist
   - No `thonnycontrib` directories remain
6. Check summary reports correct counts
7. Verify Thonny still works (if installed)

### Edge Case Tests:

**Partial Installation:**
1. Manually remove some components (e.g., delete `~/.kiro/`)
2. Run uninstaller
3. Verify it handles missing components gracefully
4. Check "not found" items are reported correctly

**Multiple Python Versions:**
1. Manually copy plugin to multiple Python version directories
2. Run uninstaller
3. Verify all versions are detected and removed
4. Check empty directories are cleaned up

**Already Uninstalled:**
1. Run uninstaller on clean system (nothing installed)
2. Verify it completes without errors
3. Check all items reported as "not found"
4. Verify exit code is 0 (success)

**Permission Issues:**
1. Test without sudo access (if dpkg removal fails gracefully)
2. Test with readonly files (should report errors but continue)

### Idempotency Test:
1. Install Smart Rover
2. Run uninstaller once
3. Run uninstaller again immediately
4. Verify second run completes cleanly
5. Check no errors or warnings on second run

### Desktop Launcher Test:
1. Place `smart-rover-uninstaller.desktop` in `~/Desktop/`
2. Make executable: `chmod +x ~/Desktop/smart-rover-uninstaller.desktop`
3. Double-click the launcher
4. Verify terminal opens and uninstaller runs
5. Test confirmation prompt works via desktop launcher

## Performance Considerations

- **Execution time**: 5-15 seconds typical (mostly user confirmation time)
- **Disk I/O**: Minimal - only removing files, not copying
- **Network**: No network access required (unlike installer)
- **Disk space freed**: ~50-100 MB total (kiro-cli + plugin + user data)
- **No system impact**: Removal is instant, no performance degradation

## Security Considerations

### User Confirmation:
- Script requires explicit "yes" confirmation before removing anything
- Warns user that operation cannot be undone
- Lists what will be removed before proceeding

### Data Loss Prevention:
- Clear warnings about removing credentials and conversation history
- Desktop launcher file is reported but not auto-removed (user may have customized it)
- Thonny IDE is never removed (only the plugin)

### Permission Safety:
- Only uses sudo for dpkg removal (package manager operation)
- User-level file removal doesn't require elevated privileges
- No system-wide file removal (only user's home directory)

### Verification Steps:
- Double-checks directory existence before removal
- Verifies removal succeeded after each operation
- Reports failures clearly without hiding errors

## Migration Notes

### Reinstallation After Uninstall:
- User will need to re-authenticate with kiro-cli after reinstall
- All conversation history will be lost
- Steering configuration will be restored from repository
- No backup/restore mechanism - user must manually backup important data before uninstalling

### Upgrading vs Uninstalling:
- For upgrades, use `install.sh` directly (it updates kiro-cli and overwrites plugin)
- Uninstaller is for complete removal only
- Upgrade preserves `~/.kiro/` data (credentials, history)
- Uninstall removes everything

### Desktop Launcher Handling:
- Installer doesn't install launcher (user copies manually)
- Uninstaller detects launcher but doesn't auto-remove
- Prevents accidental removal of customized launchers
- User must manually remove if desired

## Known Limitations

1. **Desktop launcher removal**: Not automatic - user must remove manually
2. **Non-dpkg installations**: Cannot remove kiro-cli if installed via other methods
3. **Linux only**: No Windows/macOS support (matching installer limitation)
4. **Debian/Ubuntu only**: Requires dpkg (matching installer limitation)
5. **No backup**: No automatic backup before removal
6. **Thonny detection**: Doesn't verify if Thonny is running (may require restart)

## Future Enhancements (Out of Scope)

- Backup functionality before uninstall
- Selective uninstall (choose components to remove)
- Windows and macOS support
- Automatic Thonny restart after uninstall
- Automatic desktop launcher detection and removal
- Support for non-dpkg kiro-cli installations
- Integration with package managers (apt, snap, etc.)

## References

- Original installation plan: `thoughts/shared/plans/2026-02-12-linux-arm-install-script.md`
- Installation script: `install.sh:1-283`
- Desktop installer launcher: `smart-rover-installer.desktop:1-9`
- kiro-cli usage analysis: Internal research from codebase-analyzer agent
- Debian package removal: `dpkg -r` command documentation
