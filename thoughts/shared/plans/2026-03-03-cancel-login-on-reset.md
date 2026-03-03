# Cancel Login/Logout on Reset Button Implementation Plan

## Overview

Enable the reset button to cancel running login/logout commands. Currently, when a user clicks login and then clicks reset before the login completes, the login command continues running in the background for up to 30 seconds (the timeout period). This plan focuses specifically on canceling login/logout operations.

## Current State Analysis

Login and logout operations have no cancellation mechanism:
- **Login execution**: Uses `subprocess.run()` which blocks until completion (`command_executor.py:43-51`)
- **No process tracking**: No reference to the subprocess is kept (`command_executor.py:15`)
- **30-second timeout**: Commands can only be interrupted by timeout (`settings.py:25`)
- **Reset ignores running commands**: Reset only clears UI state (`terminal_controller.py:127-134`)

### Current Flow:
1. User clicks login button → `terminal_controller.py:145-164`
2. `kiro-cli login` command executes via `CommandExecutor.execute()`
3. `subprocess.run()` blocks the background thread until completion
4. User clicks reset → only UI clears, subprocess keeps running
5. Login eventually completes (or times out after 30s)
6. Callback fires and updates login state

### Key Discoveries:
- Login/logout use `execute()` not `execute_chat()` (`terminal_controller.py:164, 181`)
- `subprocess.run()` cannot be interrupted once started
- No subprocess reference is stored - fire-and-forget pattern
- Browser opens before login as workaround (`terminal_controller.py:158`)

## Desired End State

After implementation:
- Reset button immediately cancels running login/logout commands
- Login button is re-enabled after reset (already implemented)
- Browser tab can remain open (not forcibly closed)
- Subsequent login attempts work correctly
- No orphaned kiro-cli processes

### Verification
- Click login → immediately click reset → login command stops
- Click logout → immediately click reset → logout command stops
- Login button is re-enabled (already working from previous fix)
- Can successfully login after canceling
- No zombie processes left running

## What We're NOT Doing

- NOT implementing command termination for chat commands (only login/logout)
- NOT closing browser windows/tabs opened by login
- NOT adding graceful shutdown with SIGTERM (using immediate kill)
- NOT changing the callback architecture
- NOT adding command queuing or concurrent execution
- NOT persisting login state across resets

## Implementation Approach

Add minimal subprocess tracking to CommandExecutor and implement a termination method. Use `subprocess.Popen()` instead of `subprocess.run()` to gain a handle to the process that can be terminated. Focus only on what's needed for login/logout cancellation.

## Phase 1: Add Subprocess Tracking to CommandExecutor

### Overview
Modify CommandExecutor to track the current subprocess so it can be terminated. Switch from `subprocess.run()` to `subprocess.Popen()` to enable process control.

### Changes Required:

#### 1. CommandExecutor - Add Process Tracking
**File**: `thonnycontrib/smart_rover/console/command_executor.py`
**Changes**: Add instance variable for current process and switch to Popen

Update `__init__` method (lines 13-15):

```python
def __init__(self):
    """Initialize the command executor."""
    self._is_executing = False
    self._current_process = None
```

#### 2. CommandExecutor - Switch to Popen in execute()
**File**: `thonnycontrib/smart_rover/console/command_executor.py`
**Changes**: Replace subprocess.run with Popen and communicate

Replace the `run_command()` nested function inside `execute()` method (lines 41-74):

```python
def run_command():
    try:
        # Use Popen instead of run for process control
        self._current_process = subprocess.Popen(
            command.text,
            shell=True,
            executable=ExecutionConfig.SHELL_EXECUTABLE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=command.working_directory
        )

        try:
            # Wait for completion with timeout
            stdout, stderr = self._current_process.communicate(
                timeout=ExecutionConfig.TIMEOUT_SECONDS
            )

            command_result = CommandResult(
                stdout=stdout,
                stderr=stderr,
                return_code=self._current_process.returncode,
                success=(self._current_process.returncode == 0)
            )

            callback(command_result)

        except subprocess.TimeoutExpired:
            # Kill the process on timeout
            self._current_process.kill()
            self._current_process.communicate()  # Clean up zombie
            callback(CommandResult(
                success=False,
                error_message=f"Command timed out ({ExecutionConfig.TIMEOUT_SECONDS} seconds)"
            ))

    except Exception as e:
        callback(CommandResult(
            success=False,
            error_message=f"Error executing command: {str(e)}"
        ))
    finally:
        self._current_process = None
        self._is_executing = False
```

#### 3. CommandExecutor - Add Termination Method
**File**: `thonnycontrib/smart_rover/console/command_executor.py`
**Changes**: Add method to terminate current subprocess

Add new method after `execute_chat()` (after line 99):

```python
def terminate_current(self) -> None:
    """Terminate the currently running command if any.

    This immediately kills the subprocess and resets execution state.
    Used when the reset button is clicked to cancel login/logout operations.
    """
    if self._current_process and self._current_process.poll() is None:
        # Process is still running, kill it immediately
        try:
            self._current_process.kill()
            self._current_process.wait(timeout=1.0)  # Wait for cleanup
        except Exception:
            pass  # Process may have already terminated
        finally:
            self._current_process = None

    # Reset execution state regardless of process state
    self._is_executing = False
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/command_executor.py`
- [x] No import errors: `python -c "from thonnycontrib.smart_rover.console.command_executor import CommandExecutor; print('Success')"`

#### Manual Verification:
- [ ] Login still works normally when not interrupted
- [ ] Logout still works normally when not interrupted
- [ ] Command output is captured correctly
- [ ] Timeout mechanism still works (test with 35-second command)

**Implementation Note**: After completing this phase and verifying existing functionality works, proceed to Phase 2.

---

## Phase 2: Update Reset to Cancel Login/Logout

### Overview
Modify the reset() method in TerminalController to terminate any running command before resetting state.

### Changes Required:

#### 1. TerminalController - Update reset() Method
**File**: `thonnycontrib/smart_rover/console/terminal_controller.py`
**Changes**: Add command termination before reset operations

Update the `reset()` method (lines 127-134):

```python
def reset(self) -> None:
    """Reset the terminal state, cancel any running command, and re-enable auth button."""
    # Terminate any running command (login/logout/chat)
    self._executor.terminate_current()

    # Reset terminal state
    self._is_first_command = True
    self._animation_stop()

    # Re-enable auth button with current state
    if self._auth_state_callback:
        self._auth_state_callback(self._is_logged_in)
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/terminal_controller.py`
- [x] Module loads correctly: `python -c "from thonnycontrib.smart_rover.console.terminal_controller import TerminalController; print('Success')"`

#### Manual Verification:
- [ ] Reset cancels running login command
- [ ] Reset cancels running logout command
- [ ] Login button is re-enabled after reset
- [ ] Terminal becomes responsive immediately
- [ ] Animation stops as before
- [ ] Welcome message displays correctly

**Implementation Note**: After completing this phase, proceed to comprehensive testing in Phase 3.

---

## Phase 3: Comprehensive Testing

### Overview
Verify the cancellation works correctly in all scenarios and handles edge cases.

### Success Criteria:

#### Automated Verification:
- [x] All Python files compile without errors
- [ ] Plugin loads in Thonny without errors
- [ ] No exceptions during normal operation

#### Manual Verification:

**Login Cancellation:**
- [ ] Click login → immediately click reset → login stops immediately
- [ ] Verify login button shows "Login" and is enabled after reset
- [ ] Click login again after canceling → login works correctly
- [ ] Verify browser tab remains open (not closed)

**Logout Cancellation:**
- [ ] Log in successfully first
- [ ] Click logout → immediately click reset → logout stops immediately
- [ ] Verify login button shows "Logout" or "Login" correctly after reset
- [ ] Verify authentication state is correct

**Timing Variations:**
- [ ] Cancel login immediately (< 1 second after clicking)
- [ ] Cancel login mid-operation (5-10 seconds after clicking)
- [ ] Cancel login just before it would complete naturally
- [ ] Same tests for logout

**Process Cleanup:**
- [ ] Run `ps aux | grep kiro-cli` before login
- [ ] Click login → click reset
- [ ] Run `ps aux | grep kiro-cli` again
- [ ] Verify no orphaned kiro-cli processes remain

**Rapid Interactions:**
- [ ] Click login → reset → login → reset rapidly
- [ ] Verify no crashes or errors
- [ ] Verify terminal remains functional

**Edge Cases:**
- [ ] Reset with no command running → works normally
- [ ] Command completes naturally then reset → works normally
- [ ] Multiple rapid resets → no errors

**Integration with Other Features:**
- [ ] Reset during chat command → chat cancels correctly
- [ ] Login state persists correctly across resets
- [ ] Terminal prompt reappears after reset
- [ ] Command history still works after reset

**Implementation Note**: This is the final phase. After all tests pass, the feature is complete.

---

## Testing Strategy

### Manual Testing Steps

#### Test 1: Basic Login Cancellation
1. Open plugin, ensure logged out
2. Click "Login" button
3. Immediately click "Reset" button (within 2 seconds)
4. **Verify**: Terminal clears and shows welcome message
5. **Verify**: Login button shows "Login" and is enabled
6. **Verify**: No error messages appear
7. Click "Login" again
8. **Verify**: Login proceeds normally

#### Test 2: Mid-Operation Login Cancellation
1. Click "Login" button
2. Wait for browser to open (5-10 seconds)
3. Click "Reset" button
4. **Verify**: Login process stops
5. **Verify**: Login button is re-enabled
6. Check terminal: `ps aux | grep kiro-cli`
7. **Verify**: No kiro-cli processes running

#### Test 3: Logout Cancellation
1. Complete login successfully
2. Click "Logout" button
3. Immediately click "Reset" button
4. **Verify**: Logout stops
5. **Verify**: Login button is re-enabled
6. Run a kiro-cli command to check actual auth state
7. **Verify**: State is consistent with button

#### Test 4: No Command Running
1. Start with no command executing
2. Click "Reset" button
3. **Verify**: Works normally (no errors)
4. **Verify**: Login button maintains correct state

#### Test 5: Rapid Interactions
1. Click login → reset → login → reset (rapid sequence)
2. **Verify**: No crashes or exceptions
3. **Verify**: Terminal remains functional
4. **Verify**: Login button in correct state

#### Test 6: Chat Command Cancellation
1. Execute a kiro-cli chat command
2. Click reset while waiting for response
3. **Verify**: Command cancels
4. **Verify**: Terminal clears
5. **Verify**: Can execute new commands

#### Test 7: Process Cleanup
1. In external terminal: `watch -n 1 'ps aux | grep kiro-cli'`
2. In plugin: Click login
3. In plugin: Click reset
4. **Verify**: kiro-cli process disappears from watch output
5. **Verify**: No zombie or orphaned processes

### Edge Cases to Verify

1. **Process already completed**: Reset after command naturally finishes
2. **Process about to complete**: Reset at the last moment
3. **No subprocess**: Reset when no command ever executed
4. **Multiple resets**: Rapid repeated reset clicks
5. **Browser state**: Verify browser tab not affected by cancel

## Performance Considerations

### Process Termination:
- `kill()` is nearly instant (milliseconds)
- No waiting for graceful shutdown
- Immediate response to user action

### Memory and Resources:
- Popen has same memory footprint as subprocess.run
- communicate() buffers output in memory (unchanged)
- Process cleanup prevents zombie processes

### Thread Safety:
- `_current_process` cleared in finally block
- Race condition handled: check `poll()` before kill
- `_is_executing` flag reset ensures new commands can run

## Migration Notes

This change is backward compatible:
- Same external API (no changes to how controller calls executor)
- Same callback patterns and CommandResult structure
- Same threading model (daemon threads)
- Only internal implementation of execute() changes
- Adds one new method (terminate_current) that's only called by reset

## References

- Login implementation: `thonnycontrib/smart_rover/console/terminal_controller.py:145-164`
- Logout implementation: `thonnycontrib/smart_rover/console/terminal_controller.py:168-181`
- Current execute method: `thonnycontrib/smart_rover/console/command_executor.py:22-75`
- Reset button handler: `thonnycontrib/smart_rover/console/terminal_controller.py:127-134`
- Existing comprehensive plan: `thoughts/shared/plans/2026-02-19-reset-button-command-termination.md`
- Button re-enable fix: `thoughts/shared/plans/2026-03-03-reset-enables-login-button.md`
- Timeout configuration: `thonnycontrib/smart_rover/config/settings.py:25`
