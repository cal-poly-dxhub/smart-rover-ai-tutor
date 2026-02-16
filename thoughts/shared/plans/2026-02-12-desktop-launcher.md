# Desktop Launcher for install.sh Implementation Plan

## Overview

Create a reliable .desktop file that launches install.sh in a terminal window, regardless of where the project directory is located. The current implementation crashes due to incorrect shell parameter handling and improper directory resolution.

## Current State Analysis

### Existing Files:
- **install.sh** (install.sh:1-257): Fully functional installation script for Smart Rover AI Tutor
  - Already executable
  - Uses proper `SCRIPT_DIR` resolution (line 7)
  - Has colored output and error handling

- **smart-rover-installer.desktop** (smart-rover-installer.desktop:1-9): Non-functional .desktop launcher
  - **Problem** (line 6): Uses `sh -c 'cd "$(dirname "$0")" ...' sh %k`
    - `$0` evaluates to "sh", not the .desktop file path
    - Uses bash-specific `read -p` syntax with `sh` shell
    - Complex embedded shell logic hard to debug
  - **Crashes** when double-clicked

### Key Discoveries:
- The `%k` field code provides the .desktop file location but may include `file://` URI prefix
- The `Path=` field in .desktop files requires absolute paths (not portable across systems)
- Using `Terminal=true` automatically opens a terminal but doesn't control which terminal emulator is used
- Best practice: Keep .desktop Exec simple, move complex logic to a dedicated wrapper script

## Desired End State

After implementation:
1. User can double-click `smart-rover-installer.desktop` from any location
2. Terminal window opens showing install.sh progress with colored output
3. Terminal remains open after installation completes (success or failure)
4. User presses Enter to close terminal
5. Works regardless of where the project directory is located (portable)

### Success Criteria:

#### Automated Verification:
- [ ] Wrapper script is executable: `test -x install-wrapper.sh`
- [ ] .desktop file validates without errors: `desktop-file-validate smart-rover-installer.desktop` (if available)
- [ ] No bash syntax errors in wrapper: `bash -n install-wrapper.sh`

#### Manual Verification:
- [ ] Double-clicking .desktop file from project directory opens terminal and runs install.sh
- [ ] Copying .desktop file to Desktop and double-clicking works correctly
- [ ] Terminal displays colored output from install.sh
- [ ] Terminal waits for Enter keypress before closing
- [ ] If install.sh is not executable, wrapper makes it executable automatically
- [ ] Error messages are visible if installation fails

## What We're NOT Doing

- NOT modifying install.sh (it's working correctly)
- NOT hardcoding absolute paths (must remain portable)
- NOT requiring manual chmod before first use
- NOT creating a GUI installer (terminal-based is sufficient)
- NOT supporting Windows .desktop equivalents (Linux-only)

## Implementation Approach

Modify install.sh to pause before exiting (so users can read the results), then update the .desktop file to properly locate and execute install.sh. This approach:
- Minimal changes (only two files modified)
- No extra files needed
- Follows .desktop file best practices
- Ensures portability (no hardcoded paths)
- Simpler and more maintainable

## Phase 1: Update install.sh to Pause Before Exit

### Overview
Add a pause mechanism to install.sh so the terminal window stays open after installation completes, allowing users to read the results.

### Changes Required:

#### 1. Modify install.sh exit behavior
**File**: `install.sh`
**Location**: Lines 252-253 (end of main function)
**Changes**: Add read prompt before exit

**Current** (install.sh:252):
```bash
    exit $EXIT_CODE
}
```

**New**:
```bash
    echo ""
    read -p "Press Enter to close this window..."
    exit $EXIT_CODE
}
```

**Why this works**:
- Pauses after all output is displayed (both success and error cases)
- Uses `read -p` which is bash-specific (matching the script's shebang)
- Consistent with user expectations for desktop-launched applications
- Allows users to read error messages before window closes

**Implementation Steps**:
1. Read install.sh to confirm current exit location
2. Use Edit tool to add pause before exit
3. Test manually: `bash install.sh` and verify it waits for Enter

### Success Criteria:

#### Automated Verification:
- [ ] File contains read prompt: `grep -q 'read -p.*Press Enter' install.sh`
- [ ] No bash syntax errors: `bash -n install.sh`
- [ ] File is still executable: `test -x install.sh`

#### Manual Verification:
- [ ] Running `bash install.sh` completes normally and waits for Enter
- [ ] Both success and error paths wait for Enter
- [ ] Pressing Enter closes the terminal normally
- [ ] Exit code is still preserved after the read prompt
- [ ] All colored output displays correctly before the pause

**Implementation Note**: This is a minimal, non-breaking change. The script can still be run from command line or .desktop launcher with identical behavior.

---

## Phase 2: Simplify .desktop File

### Overview
Update the .desktop file to simply call the wrapper script with bash. Remove all complex shell logic from the Exec field.

### Changes Required:

#### 1. Update smart-rover-installer.desktop
**File**: `smart-rover-installer.desktop`
**Changes**: Replace complex Exec line with simple wrapper call

**Current** (smart-rover-installer.desktop:6-9):
```desktop
Exec=sh -c 'cd "$(dirname "$0")" && chmod +x install.sh && ./install.sh; echo ""; read -p "Press Enter to close..."' sh %k
Icon=utilities-terminal
Terminal=true
Categories=Development;Education;
```

**New**:
```desktop
Exec=bash install-wrapper.sh
Path=%k
Icon=utilities-terminal
Terminal=true
Categories=Development;Education;
```

**Why this works**:
- `Exec=bash install-wrapper.sh` is simple and reliable
- Wrapper script handles all directory resolution logic
- `Terminal=true` ensures it opens in a terminal window
- All complexity moved to wrapper (easier to debug and test)

**Alternative if %k doesn't work for Path**:
```desktop
Exec=bash -c 'cd "$(dirname "$(readlink -f "$0")")" && bash install-wrapper.sh' bash %k
Icon=utilities-terminal
Terminal=true
Categories=Development;Education;
```

**Implementation Steps**:
1. Edit the Exec field to call wrapper script
2. Test by double-clicking the .desktop file
3. If issues occur, use alternative approach with explicit directory change

### Success Criteria:

#### Automated Verification:
- [ ] .desktop file validates (if desktop-file-validate available): `desktop-file-validate smart-rover-installer.desktop`
- [ ] File contains correct Exec line: `grep -q "Exec=bash install-wrapper.sh" smart-rover-installer.desktop`

#### Manual Verification:
- [ ] Double-clicking .desktop file from project directory works
- [ ] Copying .desktop file to ~/Desktop and double-clicking works
- [ ] Terminal opens and shows install.sh output with colors
- [ ] Installation proceeds normally
- [ ] Terminal waits for Enter before closing
- [ ] Can be launched multiple times successfully

**Implementation Note**: The Path field with %k is experimental. If it doesn't work, fall back to the alternative Exec line that explicitly changes directory. Test both scenarios:
1. Running from project directory
2. Running from copied file on Desktop

---

## Phase 3: Documentation and Cleanup

### Overview
Add usage instructions and ensure both files are properly tracked in git.

### Changes Required:

#### 1. Update README.md
**File**: `README.md`
**Changes**: Add instructions for using the .desktop launcher

Add section:
```markdown
## Installation

### Using Desktop Launcher (Linux)

1. Double-click `smart-rover-installer.desktop` to launch the installer
2. The installation script will run in a terminal window
3. Follow the on-screen instructions
4. Press Enter when complete to close the terminal

### Manual Installation (Linux)

```bash
bash install.sh
```

The installer will:
- Install kiro-cli
- Copy Steering configuration to ~/.kiro/steering
- Install Thonny plugin to ~/.config/Thonny/plugins/
- Configure kiro-cli settings
```

#### 2. Verify git tracking
**Command**: Check that new files are tracked
```bash
git status
```

Expected output should show:
- `install-wrapper.sh` (new file)
- Modified `smart-rover-installer.desktop`
- Modified `README.md` (if updated)

### Success Criteria:

#### Automated Verification:
- [ ] README.md contains desktop launcher instructions: `grep -q "smart-rover-installer.desktop" README.md`
- [ ] Both wrapper and .desktop files exist: `test -f install-wrapper.sh && test -f smart-rover-installer.desktop`

#### Manual Verification:
- [ ] README.md instructions are clear and accurate
- [ ] Both files are tracked in git (not ignored)
- [ ] Documentation matches actual behavior
- [ ] New users can follow instructions successfully

**Implementation Note**: This phase is documentation only. No functional changes. Verify that the instructions match the actual implementation before finalizing.

---

## Testing Strategy

### Unit Tests (Manual):
1. **Wrapper script isolation**:
   - Run `bash install-wrapper.sh` from project directory
   - Run from a different directory (should still work)
   - Temporarily remove install.sh and verify error handling
   - Verify exit codes are preserved

2. **Desktop file validation**:
   - Run `desktop-file-validate smart-rover-installer.desktop` (if available)
   - Check that Exec field is properly formatted
   - Verify Terminal=true is set

### Integration Tests (Manual):
1. **From project directory**:
   - Double-click .desktop file
   - Verify terminal opens with colored output
   - Let installation complete
   - Verify terminal waits for Enter

2. **From Desktop location**:
   - Copy .desktop file to ~/Desktop
   - Double-click from Desktop
   - Verify same behavior as above

3. **Multiple runs**:
   - Run installer multiple times
   - Verify it handles already-installed state correctly

### Edge Cases:
1. **Permissions**:
   - Start with install.sh not executable
   - Verify wrapper makes it executable automatically

2. **Moved directory**:
   - Move entire project to different location
   - Verify .desktop file still works

3. **Symlinked .desktop**:
   - Create symlink to .desktop file
   - Verify it still finds install.sh

### Manual Testing Steps:

#### Test 1: Basic Functionality
1. Navigate to project directory in file manager
2. Double-click `smart-rover-installer.desktop`
3. Verify terminal opens
4. Observe colored output from install.sh
5. Wait for completion
6. Press Enter to close
7. **Expected**: Installation runs successfully, terminal closes on Enter

#### Test 2: Desktop Shortcut
1. Copy `smart-rover-installer.desktop` to ~/Desktop
2. Right-click → Properties → Permissions → "Allow executing file as program" (if needed)
3. Double-click from Desktop
4. **Expected**: Same behavior as Test 1

#### Test 3: Error Handling
1. Temporarily rename install.sh to install.sh.bak
2. Run .desktop file
3. **Expected**: Clear error message, waits for Enter, no crash

#### Test 4: Non-executable install.sh
1. Run `chmod -x install.sh`
2. Run .desktop file
3. **Expected**: Wrapper makes it executable and runs successfully

## Performance Considerations

No performance concerns - this is a simple launcher for a one-time installation script. The wrapper adds negligible overhead (< 100ms).

## Migration Notes

### For Existing Users:
- No breaking changes
- Old .desktop file will be replaced with new version
- New install-wrapper.sh file will be added
- No user action required beyond re-pulling from git

### For New Users:
- Simply double-click the .desktop file to install
- No manual chmod or terminal commands needed

## References

- Original install.sh script: `install.sh:1-257`
- Current .desktop file: `smart-rover-installer.desktop:1-9`
- .desktop specification research: Web search on freedesktop.org standards (see research agent output)
- Linux .desktop best practices: ArchWiki Desktop Entries
