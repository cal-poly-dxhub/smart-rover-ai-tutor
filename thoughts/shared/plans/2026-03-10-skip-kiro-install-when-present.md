# Skip kiro-cli Installation When Already Present

## Overview

Modify the install.sh script so that when kiro-cli is already installed, it runs `kiro-cli update` instead of re-downloading and re-installing from scratch. This is faster, less error-prone, and uses kiro-cli's built-in update mechanism.

## Current State Analysis

The current `install_kiro_cli` function (lines 72-174 in install.sh):
- Checks if kiro-cli exists using `command -v kiro-cli` (line 78)
- If found, sets `IS_INSTALLED=true` and proceeds to update anyway (lines 79-83)
- Downloads and installs kiro-cli regardless of existing installation
- Only uses the `IS_INSTALLED` flag to determine the success message

### Key Discovery:
- The script always downloads and installs kiro-cli, even when it's already present
- The check for existing installation is only used for informational messages
- kiro-cli has a built-in `kiro-cli update` command for self-updating

## Desired End State

After implementation:
- When kiro-cli is already installed, the script runs `kiro-cli update` instead of downloading and re-installing
- The script reports the current version before updating and the new version after
- Fresh installation from zip still occurs when kiro-cli is not present

## What We're NOT Doing

- NOT removing the version detection capability
- NOT modifying the installation process when kiro-cli is absent
- NOT changing the behavior of other installation steps (Steering, thonnycontrib, configuration)

## Implementation Approach

Add an early branch in the `install_kiro_cli` function: when kiro-cli is detected, run `kiro-cli update` and return early. When not detected, proceed with the full download and installation.

## Phase 1: Modify install_kiro_cli Function

### Overview
Update the install_kiro_cli function to return early when kiro-cli is already installed.

### Changes Required:

#### 1. Update install_kiro_cli function
**File**: `install.sh`
**Changes**: Add early return after detecting existing kiro-cli installation

```bash
# Step 3: Install or update kiro-cli
install_kiro_cli() {
    print_step "Checking for kiro-cli installation..."

    # Check if kiro-cli is already installed
    if command -v kiro-cli >/dev/null 2>&1; then
        OLD_VERSION=$(kiro-cli --version 2>/dev/null || echo "unknown")
        print_success "kiro-cli is already installed (version: $OLD_VERSION)"
        print_step "Running kiro-cli update..."

        if kiro-cli update; then
            NEW_VERSION=$(kiro-cli --version 2>/dev/null || echo "unknown")
            if [[ "$OLD_VERSION" == "$NEW_VERSION" ]]; then
                print_success "kiro-cli is up to date (version: $NEW_VERSION)"
            else
                print_success "kiro-cli updated: $OLD_VERSION -> $NEW_VERSION"
            fi
        else
            print_warning "kiro-cli update failed, continuing with existing version"
        fi

        # Export PATH to ensure kiro-cli remains accessible
        export PATH="$HOME/.local/bin:$PATH"

        return 0
    fi

    print_step "Installing kiro-cli..."

    # Create temporary directory for download and extraction
    TEMP_DIR=$(mktemp -d)
    TEMP_ZIP="$TEMP_DIR/kirocli.zip"

    # [Rest of the function remains unchanged from line 89 onwards]
```

### Success Criteria:

#### Automated Verification:
- [x] Script syntax is valid: `bash -n install.sh`
- [ ] Script runs without errors when kiro-cli is absent: `bash install.sh` (in clean environment)
- [ ] Script completes successfully: `echo $?` returns 0

#### Manual Verification:
- [ ] When kiro-cli is already installed, script runs `kiro-cli update` instead of downloading
- [ ] Success message shows version before and after update
- [ ] If `kiro-cli update` fails, script continues with a warning (not a fatal error)
- [ ] Other installation steps (Steering, thonnycontrib) still execute
- [ ] No attempt to download kirocli-aarch64-linux-musl.zip when kiro-cli exists
- [ ] Fresh install still works correctly when kiro-cli is not present

---

## Testing Strategy

### Unit Tests:
- Verify script behavior with kiro-cli already installed
- Verify script behavior without kiro-cli (clean system)
- Check return codes in both scenarios

### Integration Tests:
- Full installation flow with pre-existing kiro-cli
- Full installation flow on clean system

### Manual Testing Steps:
1. With kiro-cli already installed, run install.sh
2. Verify it runs `kiro-cli update` instead of downloading the zip
3. Verify version reporting before and after update
4. Check that Steering and thonnycontrib are still installed
5. Test on clean system (no kiro-cli) to ensure fresh installation still works
6. Test with kiro-cli present but network unavailable to verify graceful failure

## Performance Considerations

- Uses kiro-cli's built-in update mechanism which handles incremental updates efficiently
- Avoids downloading and extracting the full zip package unnecessarily
- Reduces installation time when kiro-cli is already present

## Migration Notes

- Existing installations are not affected
- Script remains backward compatible
- `kiro-cli update` failure is non-fatal; the script continues with the existing version

## References

- Original install.sh: `install.sh:72-174`
- Previous installation plan: `thoughts/shared/plans/2026-02-12-linux-arm-install-script.md`
- README installation instructions: `README.md:20-24`