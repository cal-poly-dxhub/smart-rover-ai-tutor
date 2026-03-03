# Reset Button Re-enables Login Button Implementation Plan

## Overview

Fix the reset button to re-enable the login button when clicked. Currently, if reset is clicked while a login/logout command is executing, the login button remains disabled indefinitely because the authentication callback never fires.

## Current State Analysis

The login button state is managed through a callback pattern:
- **Button disabled**: When login/logout is clicked (`dock_view.py:123, 127`)
- **Button re-enabled**: Only via `_on_auth_state_changed` callback when command completes (`dock_view.py:132`)
- **Reset operation**: Only resets `_is_first_command` and stops animation (`terminal_controller.py:129-130`)

### Current Flow:
1. User clicks login/logout button → `_update_auth_button_state(enabled=False)` called
2. Login/logout command executes → callback fires on completion
3. `_on_auth_state_changed(is_logged_in)` → `_update_auth_button_state(enabled=True, is_logged_in=...)` called
4. Button re-enabled with correct text

### Problem Flow:
1. User clicks login button → button disabled → login command executing
2. User clicks reset button → `controller.reset()` called
3. **Issue**: Button remains disabled because auth callback hasn't fired
4. **Issue**: No mechanism to re-enable button from reset operation

### Key Discoveries:
- Login button state is purely callback-driven (`dock_view.py:130-132`)
- No direct connection between reset and login button state
- `auth_button_enabled` property exists in controller but is never used by UI (`terminal_controller.py:55-57`)
- Reset doesn't interact with command executor state (`terminal_controller.py:127-130`)
- If command is terminated (per `2026-02-19-reset-button-command-termination.md`), callback may not fire

## Desired End State

After implementation:
- Reset button immediately re-enables the login button
- Login button shows correct state ("Login" or "Logout") based on actual auth status
- Works correctly whether or not a command is executing
- Maintains backward compatibility with existing callback pattern

### Verification
- Click login → immediately click reset → login button is re-enabled
- Click logout → immediately click reset → login button is re-enabled
- Click reset with no command running → login button state unchanged
- Login state persists correctly after reset

## What We're NOT Doing

- NOT implementing command termination (handled separately in `2026-02-19-reset-button-command-termination.md`)
- NOT changing the callback-based architecture for auth state
- NOT adding new UI elements or indicators
- NOT modifying how login/logout commands execute
- NOT adding authentication state validation or polling
- NOT changing how `_is_logged_in` state is tracked

## Implementation Approach

Add a reset handler for authentication button state that re-enables the button when reset is clicked. This ensures the button is always usable after reset, regardless of command execution state.

## Phase 1: Update Reset Method to Re-enable Auth Button

### Overview
Modify the reset() method to trigger the auth state callback, ensuring the auth button is re-enabled with the current authentication state when reset is clicked.

### Changes Required:

#### 1. TerminalController - Update reset() Method
**File**: `thonnycontrib/smart_rover/console/terminal_controller.py`
**Changes**: Add callback invocation to re-enable auth button during reset

Update the `reset()` method (lines 127-130):

```python
def reset(self) -> None:
    """Reset the terminal state and re-enable auth button."""
    self._is_first_command = True
    self._animation_stop()

    # Re-enable auth button with current state
    if self._auth_state_callback:
        self._auth_state_callback(self._is_logged_in)
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/terminal_controller.py`
- [x] No import errors: `python -c "from thonnycontrib.smart_rover.console.terminal_controller import TerminalController; print('Success')"`

#### Manual Verification:
- [ ] No errors when reset is called
- [ ] Auth callback fires with current login state when reset is clicked

**Implementation Note**: After completing this phase and all automated verification passes, proceed to Phase 2 to verify the full integration.

---

## Phase 2: Verify Integration with Command Termination (If Implemented)

### Overview
Ensure the reset functionality works correctly with command termination from the `2026-02-19-reset-button-command-termination.md` plan if it has been implemented.

### Analysis Required:

Check if command termination has been implemented:
1. Does `CommandExecutor` have a `terminate_current()` method?
2. Does reset call `self._executor.terminate_current()`?
3. If yes, verify the order of operations is correct

### Changes Required (If Command Termination Is Implemented):

#### 1. TerminalController - Ensure Correct Reset Order
**File**: `thonnycontrib/smart_rover/console/terminal_controller.py`
**Changes**: Ensure auth button reset happens after command termination

If command termination is implemented, the reset() method should look like:

```python
def reset(self) -> None:
    """Reset the terminal state, terminate any running command, and re-enable auth button."""
    # Terminate any running command first
    self._executor.terminate_current()

    # Reset terminal state
    self._is_first_command = True
    self._animation_stop()

    # Re-enable auth button with current state
    if self._auth_state_callback:
        self._auth_state_callback(self._is_logged_in)
```

**If command termination is NOT implemented**: No changes needed, Phase 1 implementation is sufficient.

### Success Criteria:

#### Automated Verification:
- [ ] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/terminal_controller.py`
- [ ] Module loads correctly: `python -c "from thonnycontrib.smart_rover.console.terminal_controller import TerminalController; print('Success')"`

#### Manual Verification:
- [ ] Reset properly terminates commands (if termination is implemented)
- [ ] Auth button is re-enabled after command termination
- [ ] No race conditions or errors

**Implementation Note**: After completing this phase, proceed to comprehensive testing in Phase 3.

---

## Phase 3: Comprehensive Testing and Edge Cases

### Overview
Verify the fix works in all scenarios and handles edge cases correctly.

### Success Criteria:

#### Automated Verification:
- [ ] All Python files compile without errors
- [ ] Plugin loads in Thonny without errors
- [ ] No exceptions during normal operation

#### Manual Verification:

**Basic Reset Scenarios:**
- [ ] Reset with no command running → login button maintains state
- [ ] Reset after login completed → login button shows "Logout" and is enabled
- [ ] Reset after logout completed → login button shows "Login" and is enabled

**Reset During Command Execution:**
- [ ] Click login button → immediately click reset → login button re-enabled
- [ ] Click logout button → immediately click reset → login button re-enabled
- [ ] Verify correct button text after reset (matches actual login state)

**Reset During Other Commands:**
- [ ] Execute chat command → click reset → verify auth button state correct
- [ ] Execute long-running command → click reset → verify auth button enabled

**Rapid Interaction:**
- [ ] Click login → click reset → click login again → verify works correctly
- [ ] Click logout → click reset → click logout again → verify works correctly
- [ ] Multiple rapid resets → verify no errors or state corruption

**Authentication State Verification:**
- [ ] If logged in, reset shows "Logout" button (enabled)
- [ ] If logged out, reset shows "Login" button (enabled)
- [ ] Login state persists correctly across reset
- [ ] Can successfully login/logout after reset

**Integration with Welcome Message:**
- [ ] Reset displays welcome message correctly
- [ ] Auth button state updates after welcome message
- [ ] Terminal remains functional after reset

**Implementation Note**: This is the final phase. After all tests pass, the feature is complete.

---

## Testing Strategy

### Unit Tests
Not applicable - this is GUI state management that requires integration testing with Tkinter.

### Integration Tests
Not applicable - requires manual testing with actual Thonny plugin environment.

### Manual Testing Steps

#### Test 1: Reset Re-enables Disabled Login Button
1. Start plugin with logged out state (login button shows "Login")
2. Click "Login" button
3. Immediately click "Reset" button (before login completes)
4. **Verify**: Login button is re-enabled and shows "Login"
5. Click "Login" again and verify it works

#### Test 2: Reset Maintains Logged-In State
1. Log in successfully (button shows "Logout")
2. Click "Reset" button
3. **Verify**: Login button shows "Logout" and is enabled
4. **Verify**: Can click "Logout" and it works correctly

#### Test 3: Reset During Logout
1. Start with logged-in state (button shows "Logout")
2. Click "Logout" button
3. Immediately click "Reset" button (before logout completes)
4. **Verify**: Login button is re-enabled
5. **Verify**: Check actual auth state with a kiro-cli command

#### Test 4: Reset with No Command Running
1. Start with any auth state
2. Wait for all commands to complete
3. Click "Reset" button
4. **Verify**: Login button remains enabled with correct text
5. **Verify**: Login/logout functionality still works

#### Test 5: Rapid Reset Clicks
1. Click "Login" button
2. Click "Reset" button multiple times rapidly
3. **Verify**: No errors or exceptions
4. **Verify**: Login button is enabled with correct state
5. **Verify**: Terminal remains functional

#### Test 6: Reset After Timeout
1. Modify timeout to 5 seconds for testing (if needed)
2. Run a long command that times out
3. Click "Reset" during or after timeout
4. **Verify**: Login button is enabled
5. **Verify**: Login/logout works after reset

#### Test 7: Cross-Command Interaction
1. Execute a kiro-cli chat command
2. While command is running, click "Reset"
3. **Verify**: Terminal clears and resets
4. **Verify**: Login button is enabled with correct state
5. Click login/logout button
6. **Verify**: Auth command executes successfully

### Edge Cases to Verify

1. **Callback Safety**: Verify `_auth_state_callback` is None-checked before calling
2. **State Consistency**: Verify `_is_logged_in` remains correct across resets
3. **Thread Safety**: Verify no race conditions between reset and callback
4. **Multiple Resets**: Verify rapid resets don't corrupt state
5. **Welcome Message**: Verify reset displays welcome message correctly

## Performance Considerations

### Callback Performance:
- Calling `reset_auth_button()` is immediate (no I/O)
- Simply triggers existing callback with current state
- No additional overhead beyond existing callback pattern

### Reset Performance:
- No change to reset operation performance
- Auth button update happens synchronously
- No blocking operations added

### Thread Safety:
- Callback is already scheduled on main thread via `_schedule` in existing code
- No new thread safety concerns introduced
- Existing callback pattern handles thread safety

## Migration Notes

This change is backward compatible:
- No API changes to existing methods
- Adds new method that doesn't conflict with existing code
- Only modifies internal reset() behavior
- Existing callback pattern unchanged

## References

- Login button implementation: `thoughts/shared/plans/2026-02-10-login-logout-button.md`
- Reset button command termination: `thoughts/shared/plans/2026-02-19-reset-button-command-termination.md`
- Current terminal controller: `thonnycontrib/smart_rover/console/terminal_controller.py:127-142`
- Current dock view: `thonnycontrib/smart_rover/gui/dock_view.py:113-132`
- Auth button state management: `thonnycontrib/smart_rover/gui/dock_view.py:134-141`
- Git status: Reset button fix in worktree `reset-button-fix`
