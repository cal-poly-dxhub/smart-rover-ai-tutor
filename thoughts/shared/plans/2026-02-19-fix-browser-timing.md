# Fix Browser Opening Timing for Login Command

## Overview

Fix the timing issue in the terminal_controller.py login method where the browser opening command and kiro-cli login command are executed without proper sequencing. The login command should wait for the browser to open before executing.

## Current State Analysis

The current implementation (`terminal_controller.py:158-185`) attempts to execute two commands:
1. Opens a browser window with `x-www-browser`
2. Runs `kiro-cli login` immediately after

The problem: Both commands are fired immediately, but due to the `_is_executing` mutex in CommandExecutor (`command_executor.py:32-37`), only one command can run at a time. This can cause:
- The login command to fail with "A command is already executing" if browser is still opening
- The login command to run before the browser is fully open

### Key Discoveries:
- CommandExecutor uses a single-command mutex pattern (`command_executor.py:15,32-37`)
- Commands execute in daemon threads (`command_executor.py:75`)
- Callbacks are invoked when commands complete (`command_executor.py:60`)
- Sequential execution requires chaining via callbacks

## Desired End State

The login method should:
1. Open a browser window first
2. Wait for the browser command to complete (successfully or with error)
3. Then execute the kiro-cli login command
4. Maintain proper error handling for both commands

### Verification
- Browser opens before login prompt appears
- No "command is already executing" errors
- Login flow works correctly with proper timing
- Failed browser opening doesn't prevent login attempt

## What We're NOT Doing

- NOT adding platform detection (user confirmed this isn't needed)
- NOT adding complex error handling for browser failures
- NOT implementing retry logic
- NOT adding timeout mechanisms beyond existing ones
- NOT changing the CommandExecutor's single-command limitation

## Implementation Approach

Chain the commands using the callback pattern. The browser command's callback will trigger the login command, ensuring proper sequencing.

## Phase 1: Fix Command Chaining in login() Method

### Overview
Modify the login() method to properly chain the browser opening and login commands using callbacks.

### Changes Required:

#### 1. Terminal Controller - Fix login() Method
**File**: `thonnycontrib/smart_rover/console/terminal_controller.py`
**Changes**: Modify lines 158-185 to chain commands properly

Replace the current login() method (lines 158-185) with:

```python
def login(self) -> None:
    """Execute kiro-cli login command."""
    def handle_login_result(result: CommandResult):
        # After login attempt, update state
        # If no error, login was successful or already logged in
        is_logged_in = "error" not in result.stdout.lower() and "error" not in result.stderr.lower()
        self._is_logged_in = is_logged_in
        if self._auth_state_callback:
            self._auth_state_callback(is_logged_in)

    def handle_browser_result(result: CommandResult):
        # Browser command completed (success or failure)
        # Now execute the actual login command
        # We proceed with login even if browser failed to open
        login_command = Command(
            text="kiro-cli login",
            working_directory=self._cwd
        )
        self._executor.execute(login_command, handle_login_result)

    # REMOVE when the bug for kiro-cli is fixed for this version of linux.
    # Kiro fails the login process when "kiro-cli login" opens a new browser window.
    # Therefore open a new window beforehand and wait for it to complete.
    open_window_command = Command(
        text="x-www-browser",
        working_directory=self._cwd
    )
    self._executor.execute(open_window_command, handle_browser_result)
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/terminal_controller.py`
- [x] No import errors: `python -c "from thonnycontrib.smart_rover.console.terminal_controller import TerminalController; print('Success')"`

#### Manual Verification:
- [ ] Browser opens before login command executes
- [ ] Login command executes after browser command completes
- [ ] No "command is already executing" errors occur
- [ ] Login succeeds and updates button state correctly
- [ ] If browser fails to open, login still attempts to execute

**Implementation Note**: This is a single-phase fix. After verifying the automated tests pass, the implementation is complete.

---

## Testing Strategy

### Manual Testing Steps

1. **Test successful browser opening**:
   - Click "Login" button
   - Verify browser opens first
   - Verify login prompt appears after browser is open
   - Complete authentication
   - Verify button changes to "Logout"

2. **Test browser command failure**:
   - Temporarily rename `x-www-browser` to simulate missing command
   - Click "Login" button
   - Verify login command still executes despite browser failure
   - Verify authentication can still complete

3. **Test rapid clicking prevention**:
   - Click "Login" button multiple times rapidly
   - Verify only one browser opens
   - Verify only one login sequence occurs

4. **Test state consistency**:
   - Login successfully
   - Verify button shows "Logout"
   - Click "Logout"
   - Verify button shows "Login"
   - Click "Login" again
   - Verify proper sequencing still occurs

## Performance Considerations

### Command Execution Timing:
- Browser opening adds ~0.5-2 seconds before login prompt
- Total login time increases by browser launch time
- Both commands run in background threads (non-blocking)

### Callback Chain Performance:
- Minimal overhead from callback nesting
- Commands execute sequentially, not in parallel
- Thread creation happens twice (once per command)

## Migration Notes

Not applicable - this is a bug fix to existing functionality.

## References

- Original login button implementation: `thoughts/shared/plans/2026-02-10-login-logout-button.md`
- CommandExecutor threading model: `thonnycontrib/smart_rover/console/command_executor.py:22-75`
- Callback pattern examples: `thonnycontrib/smart_rover/console/terminal_controller.py:143-156`
- Linux workaround context: User-provided comment in code