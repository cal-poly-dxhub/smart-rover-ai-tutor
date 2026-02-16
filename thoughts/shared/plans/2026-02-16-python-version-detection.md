# Python Version Detection for Thonny Plugin Installation

## Overview

Modify the `copy_thonnycontrib()` function in `install.sh` to dynamically detect which Python version exists in Thonny's plugin directory structure, rather than hardcoding Python 3.13. This ensures the installer works across different Python versions that Thonny might be using.

## Current State Analysis

### Existing Implementation (install.sh:156-195)
The `copy_thonnycontrib()` function currently hardcodes the destination path to Python 3.13:

```bash
DEST_DIR="$HOME/.config/Thonny/plugins/lib/python3.13/site-packages/thonnycontrib"
```

**Problems with current approach**:
- Fails if user's Thonny installation uses a different Python version
- No flexibility for different Python environments
- Documented as needing enhancement in planning docs

**Existing patterns to follow**:
- Command existence checking: `command -v` pattern (lines 52, 68, 105, 202)
- Directory existence checking: `[[ -d "$PATH" ]]` pattern (lines 131, 140, 164, 173)
- Version detection: Similar to `kiro-cli --version` pattern (lines 70, 106)
- Colored output: `print_warning`, `print_success`, `print_error` functions
- Continue-on-error: Uses global EXIT_CODE tracking

## Desired End State

The `copy_thonnycontrib()` function will:
1. Check for existing Python version directories in `~/.config/Thonny/plugins/lib/` from highest to lowest (3.15 down to 3.7)
2. Use the **highest** version found
3. If no version found, default to Python 3.13 with a warning message
4. Dynamically construct the destination path based on detected version
5. Proceed with the copy operation using the detected path

### Verification Steps
After implementation:
- Test with existing Python 3.13 directory: should detect and use it
- Test with Python 3.12 directory: should detect and use it
- Test with no existing directories: should default to 3.13 with warning
- Test with multiple versions (3.11, 3.12, 3.13): should use 3.13 (highest)

## What We're NOT Doing

- NOT checking system Python installations (only Thonny's plugin directory structure)
- NOT prompting user for version selection (fully automated)
- NOT copying to multiple Python versions (only the highest found)
- NOT going below Python 3.7 or above Python 3.15
- NOT changing any other parts of the installation script
- NOT modifying the Python plugin code itself
- NOT validating whether Python is actually installed on the system

## Implementation Approach

### Strategy
Add a Python version detection loop at the beginning of `copy_thonnycontrib()` function that:
1. Iterates through Python versions 3.15 → 3.7 (descending order)
2. Checks if `~/.config/Thonny/plugins/lib/python3.X/` directory exists
3. Stops at first (highest) match found
4. Falls back to 3.13 if no version found
5. Uses detected version to construct DEST_DIR path

### Key Design Decisions
- **Detection method**: Check directory existence in Thonny's plugin structure
- **Search order**: Highest to lowest (3.15 → 3.7) to prefer newer versions
- **Fallback**: Python 3.13 (current hardcoded value) for backwards compatibility
- **User feedback**: Warning message when falling back to default version

## Phase 1: Add Python Version Detection Logic

### Overview
Modify the `copy_thonnycontrib()` function to detect the Python version dynamically before setting DEST_DIR.

### Changes Required

#### 1. Modify `copy_thonnycontrib()` function in install.sh
**File**: `install.sh`
**Lines**: 156-195
**Changes**: Add version detection logic after function declaration, before setting DEST_DIR

**New implementation**:

```bash
# Step 5: Copy thonnycontrib package
copy_thonnycontrib() {
    print_step "Copying thonnycontrib plugin..."

    SOURCE_DIR="$SCRIPT_DIR/thonnycontrib"

    # Detect Python version used by Thonny (check from highest to lowest)
    PYTHON_VERSION=""
    THONNY_LIB_DIR="$HOME/.config/Thonny/plugins/lib"

    print_step "Detecting Python version in Thonny plugins directory..."

    # Check versions from 3.15 down to 3.7
    for version in 3.15 3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7; do
        if [[ -d "$THONNY_LIB_DIR/python$version" ]]; then
            PYTHON_VERSION="$version"
            print_success "Detected Python $PYTHON_VERSION in Thonny plugins"
            break
        fi
    done

    # Fallback to default version if none found
    if [[ -z "$PYTHON_VERSION" ]]; then
        PYTHON_VERSION="3.13"
        print_warning "No Python version detected in Thonny plugins, using default: $PYTHON_VERSION"
        print_warning "Directory will be created at installation time"
    fi

    # Construct destination path with detected version
    DEST_DIR="$HOME/.config/Thonny/plugins/lib/python$PYTHON_VERSION/site-packages/thonnycontrib"

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
```

**Key changes explained**:
1. **Lines 161-164**: Initialize variables for Python version and Thonny lib directory
2. **Lines 166**: Add status message for detection phase
3. **Lines 168-174**: Loop through versions 3.15 → 3.7, check directory existence, break on first match
4. **Lines 176-180**: Fallback to Python 3.13 with warning if no version detected
5. **Line 183**: Dynamically construct DEST_DIR using detected version
6. **Lines 185-211**: Existing copy logic remains unchanged

### Success Criteria

#### Automated Verification:
- [x] Script runs without syntax errors: `bash -n install.sh`
- [x] No shellcheck warnings: `shellcheck install.sh` (if available)
- [x] Function returns 0 on successful copy
- [x] Function returns 1 on errors (source not found, copy failed, verification failed)

#### Manual Verification:
- [ ] **Test Case 1 - Existing Python 3.13 directory**:
  - Setup: `mkdir -p ~/.config/Thonny/plugins/lib/python3.13`
  - Run: `./install.sh`
  - Expected: Detects Python 3.13, copies successfully, shows success message
  - Verify: `ls ~/.config/Thonny/plugins/lib/python3.13/site-packages/thonnycontrib/smart_rover/__init__.py`

- [ ] **Test Case 2 - Existing Python 3.12 directory**:
  - Setup: `rm -rf ~/.config/Thonny/plugins/lib/python3.13 && mkdir -p ~/.config/Thonny/plugins/lib/python3.12`
  - Run: `./install.sh`
  - Expected: Detects Python 3.12, copies successfully
  - Verify: `ls ~/.config/Thonny/plugins/lib/python3.12/site-packages/thonnycontrib/smart_rover/__init__.py`

- [ ] **Test Case 3 - No existing Python directories**:
  - Setup: `rm -rf ~/.config/Thonny/plugins/lib/python*`
  - Run: `./install.sh`
  - Expected: Shows warning about using default 3.13, creates directory, copies successfully
  - Verify: `ls ~/.config/Thonny/plugins/lib/python3.13/site-packages/thonnycontrib/smart_rover/__init__.py`

- [ ] **Test Case 4 - Multiple Python versions exist**:
  - Setup: `mkdir -p ~/.config/Thonny/plugins/lib/python{3.11,3.12,3.13}`
  - Run: `./install.sh`
  - Expected: Detects and uses Python 3.13 (highest), copies to that version only
  - Verify: `ls ~/.config/Thonny/plugins/lib/python3.13/site-packages/thonnycontrib/smart_rover/__init__.py`
  - Verify: Python 3.11 and 3.12 directories do NOT contain thonnycontrib

- [ ] **Test Case 5 - Lower version only (Python 3.8)**:
  - Setup: `rm -rf ~/.config/Thonny/plugins/lib/python* && mkdir -p ~/.config/Thonny/plugins/lib/python3.8`
  - Run: `./install.sh`
  - Expected: Detects Python 3.8, copies successfully
  - Verify: `ls ~/.config/Thonny/plugins/lib/python3.8/site-packages/thonnycontrib/smart_rover/__init__.py`

- [ ] **Test Case 6 - Version at boundary (Python 3.7)**:
  - Setup: `rm -rf ~/.config/Thonny/plugins/lib/python* && mkdir -p ~/.config/Thonny/plugins/lib/python3.7`
  - Run: `./install.sh`
  - Expected: Detects Python 3.7, copies successfully
  - Verify: `ls ~/.config/Thonny/plugins/lib/python3.7/site-packages/thonnycontrib/smart_rover/__init__.py`

- [ ] **Test Case 7 - Version at boundary (Python 3.15)**:
  - Setup: `rm -rf ~/.config/Thonny/plugins/lib/python* && mkdir -p ~/.config/Thonny/plugins/lib/python3.15`
  - Run: `./install.sh`
  - Expected: Detects Python 3.15, copies successfully
  - Verify: `ls ~/.config/Thonny/plugins/lib/python3.15/site-packages/thonnycontrib/smart_rover/__init__.py`

- [ ] **Output messages are clear and informative**:
  - Detection message appears: "Detecting Python version..."
  - Success message shows detected version: "Detected Python 3.X in Thonny plugins"
  - Warning message appears when falling back: "No Python version detected..., using default: 3.13"
  - Final success message shows correct path with detected version

**Implementation Note**: This is a single-phase implementation. After completing the changes and verifying all automated and manual tests pass, the implementation is complete.

## Testing Strategy

### Pre-Implementation Testing
Before making changes:
1. Run current install.sh to verify baseline functionality
2. Document current behavior with Python 3.13 directory

### Unit-Level Testing
Test the version detection logic:
```bash
# Test version detection in isolation
THONNY_LIB_DIR="/tmp/test-thonny/plugins/lib"
mkdir -p "$THONNY_LIB_DIR/python3.12"

for version in 3.15 3.14 3.13 3.12 3.11 3.10 3.9 3.8 3.7; do
    if [[ -d "$THONNY_LIB_DIR/python$version" ]]; then
        echo "Found: python$version"
        break
    fi
done
```

### Integration Testing
Run full install.sh script with different scenarios:
1. Fresh installation (no Thonny directories)
2. Existing installation with Python 3.13
3. Existing installation with Python 3.12
4. Multiple Python versions present

### Edge Case Testing
- Empty Thonny plugins directory
- Corrupted Python version directory (exists but empty)
- Very old Python version (3.7)
- Very new Python version (3.15)
- Python directories with unusual permissions

### Regression Testing
Ensure existing functionality still works:
- [ ] Steering directory copy still works
- [ ] kiro-cli installation still works
- [ ] Error handling still works correctly
- [ ] Exit codes are correct
- [ ] Colored output displays correctly

## Performance Considerations

**Loop Performance**:
- Checking 9 directories (3.15 → 3.7) is negligible overhead
- Directory existence check (`[[ -d ]]`) is a fast filesystem operation
- Breaks on first match, so typically checks 1-3 directories maximum

**No Performance Impact Expected**:
- Detection adds ~5-10ms to installation time
- Existing copy operation is the bottleneck (copying actual files)
- No network calls or heavy computations

## Migration Notes

**Backwards Compatibility**:
- Default fallback to Python 3.13 ensures existing behavior for fresh installs
- Users with existing Python 3.13 installations will see no change
- Users with other Python versions will now work correctly (previously failed silently)

**No User Action Required**:
- Changes are transparent to end users
- No configuration files to update
- No breaking changes to plugin installation

**For Developers**:
- If hardcoding test paths in other scripts, be aware this is now dynamic
- Documentation should be updated to remove references to "Python 3.13 only"

## Error Handling

### Scenarios and Responses

1. **Source directory missing** (existing behavior maintained):
   - Error message: "thonnycontrib directory not found at: $SOURCE_DIR"
   - Returns 1, installation continues with other steps

2. **Copy operation fails** (existing behavior maintained):
   - Error message: "Failed to copy thonnycontrib directory"
   - Returns 1, installation continues with other steps

3. **Verification fails** (existing behavior maintained):
   - Error message: "Plugin entry point not found after copy"
   - Returns 1, installation continues with other steps

4. **No Python version detected** (new behavior):
   - Warning message: "No Python version detected in Thonny plugins, using default: 3.13"
   - Warning message: "Directory will be created at installation time"
   - Continues with default version, creates directory structure
   - Returns 0 or 1 based on copy operation success

### Exit Code Behavior
- Function returns 0 on success (detection + copy both succeed)
- Function returns 1 on any error (source missing, copy failed, verification failed)
- Uses global EXIT_CODE tracking (existing pattern)
- Script continues execution even on failure (set +e pattern)

## References

- Original installation script: `install.sh`
- Existing planning document: `thoughts/shared/plans/2026-02-12-linux-arm-install-script.md`
- Project Python requirements: `pyproject.toml` (requires-python = ">=3.9")
- Pattern source: install.sh lines 36-47 (architecture detection), 52-59 (command checking), 131-153 (directory operations)

## Implementation Checklist

- [x] Modify `copy_thonnycontrib()` function with version detection loop
- [x] Add print statements for detection progress
- [ ] Test with Python 3.13 directory (most common case)
- [ ] Test with Python 3.12 directory (alternative version)
- [ ] Test with no Python directories (fallback case)
- [ ] Test with multiple Python directories (highest version wins)
- [ ] Test with Python 3.7 (lower boundary)
- [ ] Test with Python 3.15 (upper boundary)
- [ ] Verify all success/warning messages display correctly
- [ ] Verify file copy completes successfully in all cases
- [ ] Verify no regression in other installation steps
- [ ] Update documentation if needed
- [ ] Update README.md if Python version mentioned
- [ ] Consider updating planning documents to reflect implementation
