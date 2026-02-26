# Disable Terminal Input Until Login Implementation Plan

## Overview

Disable the user's ability to type into the terminal chat until they successfully authenticate with kiro-cli. This prevents unauthenticated command execution and ensures all commands are associated with an authenticated user.

## Current State Analysis

The terminal input system currently only blocks input during command execution, not based on authentication state.

### Terminal Input Control (thonnycontrib/smart_rover/gui/terminal_widget.py)

**Input Blocking Mechanism** (lines 120-149):
- `_on_key_press()` handler checks `self._is_executing()` callback
- Returns `"break"` to block input when callback returns `True`
- No authentication-based blocking exists

**Callback Pattern** (lines 18, 26):
- Line 18: `is_executing_callback` parameter in `__init__()`
- Line 26: Stored as `self._is_executing` instance variable
- Called in event handlers to check execution state

**Event Handlers**:
- Line 120-149: `_on_key_press()` - Generic key handler
- Line 151-160: `_on_enter_key()` - Enter key handler
- Line 162-172: `_on_up_key()` - History up handler
- Line 174-186: `_on_down_key()` - History down handler

### Authentication State (thonnycontrib/smart_rover/console/terminal_controller.py)

**State Storage**:
- Line 35: `self._is_logged_in = False` - Tracks auth status
- Lines 49-51: `is_logged_in` property exposes state

**State Updates**:
- Lines 143-156: `check_login_status()` - Initial status check
- Lines 158-173: `login()` - Updates state after login
- Lines 175-188: `logout()` - Sets state to False after logout

### GUI Integration (thonnycontrib/smart_rover/gui/dock_view.py)

**TerminalWidget Creation** (lines 70-77):
- Line 75: Passes `is_executing_callback` lambda
- No authentication callback currently passed

**Controller Reference**:
- Line 81: `self.controller` holds TerminalController instance
- Has access to `controller.is_logged_in` property

### Key Discoveries:
- Input blocking uses callback pattern for state checking
- Event handlers return `"break"` to block tkinter default behavior
- TerminalWidget is decoupled from controller via callbacks
- Authentication state already tracked in TerminalController
- Need to add second callback for authentication state

## Desired End State

### Functionality
- User cannot type in terminal when not logged in
- All keyboard input blocked (Enter, typing, history navigation)
- Input automatically enables after successful login
- Input automatically disables after logout
- Visual feedback shows terminal is disabled (existing animation/state)

### Verification
- On plugin startup, terminal input is disabled
- After clicking "Login" and authenticating, input becomes enabled
- After clicking "Logout", input becomes disabled again
- Commands cannot be entered while logged out
- History navigation disabled while logged out

## What We're NOT Doing

- NOT adding visual indicators (grayed out terminal, disabled message)
- NOT adding user prompts or error messages when trying to type
- NOT changing the login/logout button behavior
- NOT modifying authentication logic or state management
- NOT changing how commands are executed when logged in
- NOT adding new UI components or widgets
- NOT persisting login state across sessions

## Implementation Approach

We'll implement this in two phases:

1. **Phase 1**: Add `is_logged_in_callback` to TerminalWidget and update event handlers
2. **Phase 2**: Pass authentication callback from KiroDockView

This approach adds the infrastructure first (callback parameter and logic), then wires it up in the GUI layer.

---

## Phase 1: Add Authentication Callback to TerminalWidget

### Overview
Add a new `is_logged_in_callback` parameter to TerminalWidget and update all event handlers to check authentication state before allowing input.

### Changes Required:

#### 1. TerminalWidget - Add Authentication Callback Parameter
**File**: `thonnycontrib/smart_rover/gui/terminal_widget.py`

**Update `__init__` signature** (line 15-20), add new parameter after `is_executing_callback`:

```python
def __init__(self,
             master,
             on_command_callback: Callable[[str], None],
             on_history_up_callback: Callable[[], Optional[str]],
             on_history_down_callback: Callable[[], Optional[str]],
             is_executing_callback: Callable[[], bool],
             is_logged_in_callback: Callable[[], bool]):
    """Initialize the terminal widget."""
```

**Store callback** (after line 26), add new instance variable:

```python
self._is_executing = is_executing_callback
self._is_logged_in = is_logged_in_callback
```

#### 2. TerminalWidget - Update Key Press Handler
**File**: `thonnycontrib/smart_rover/gui/terminal_widget.py`

**Update `_on_key_press` method** (lines 120-149), add authentication check:

Replace line 122-123:
```python
if self._is_executing():
    return "break"
```

With:
```python
# Block input if executing or not logged in
if self._is_executing() or not self._is_logged_in():
    return "break"
```

**Explanation**: Blocks all keyboard input when either:
- A command is currently executing, OR
- User is not logged in

#### 3. TerminalWidget - Update Enter Key Handler
**File**: `thonnycontrib/smart_rover/gui/terminal_widget.py`

**Update `_on_enter_key` method** (lines 151-160), add authentication check:

Replace line 153-154:
```python
if self._is_executing():
    return "break"
```

With:
```python
# Block Enter if executing or not logged in
if self._is_executing() or not self._is_logged_in():
    return "break"
```

#### 4. TerminalWidget - Update Up Arrow Handler
**File**: `thonnycontrib/smart_rover/gui/terminal_widget.py`

**Update `_on_up_key` method** (lines 162-172), add authentication check:

Replace line 164-165:
```python
if self._is_executing():
    return "break"
```

With:
```python
# Block history navigation if executing or not logged in
if self._is_executing() or not self._is_logged_in():
    return "break"
```

#### 5. TerminalWidget - Update Down Arrow Handler
**File**: `thonnycontrib/smart_rover/gui/terminal_widget.py`

**Update `_on_down_key` method** (lines 174-186), add authentication check:

Replace line 176-177:
```python
if self._is_executing():
    return "break"
```

With:
```python
# Block history navigation if executing or not logged in
if self._is_executing() or not self._is_logged_in():
    return "break"
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/gui/terminal_widget.py`
- [x] No import errors when loading module: `python -c "from thonnycontrib.smart_rover.gui.terminal_widget import TerminalWidget; print('Success')"`

#### Manual Verification:
- [ ] TerminalWidget can be instantiated with new parameter
- [ ] No exceptions when callback is called
- [ ] Event handlers check authentication state

**Implementation Note**: After completing this phase, the code will not run yet because KiroDockView doesn't pass the new required parameter. Phase 2 will fix this.

---

## Phase 2: Wire Up Authentication Callback in GUI

### Overview
Update KiroDockView to pass the `is_logged_in_callback` when creating TerminalWidget, completing the callback chain from controller to widget.

### Changes Required:

#### 1. KiroDockView - Pass Authentication Callback
**File**: `thonnycontrib/smart_rover/gui/dock_view.py`

**Update TerminalWidget creation** (lines 70-77), add new callback parameter:

Replace lines 70-77:
```python
self.terminal_widget = TerminalWidget(
    terminal_frame,
    on_command_callback=self._on_command_entered,
    on_history_up_callback=self._on_history_up,
    on_history_down_callback=self._on_history_down,
    is_executing_callback=lambda: self.controller.is_executing if self.controller else False
)
```

With:
```python
self.terminal_widget = TerminalWidget(
    terminal_frame,
    on_command_callback=self._on_command_entered,
    on_history_up_callback=self._on_history_up,
    on_history_down_callback=self._on_history_down,
    is_executing_callback=lambda: self.controller.is_executing if self.controller else False,
    is_logged_in_callback=lambda: self.controller.is_logged_in if self.controller else False
)
```

**Explanation**:
- New `is_logged_in_callback` parameter added (line 76)
- Lambda checks if controller exists and returns `controller.is_logged_in`
- Returns `False` if controller not initialized (safety check)
- Parallels existing `is_executing_callback` pattern

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/gui/dock_view.py`
- [x] No import errors: `python -c "from thonnycontrib.smart_rover.gui.dock_view import KiroDockView; print('Success')"`
- [ ] Plugin loads in Thonny without errors

#### Manual Verification:
- [ ] Terminal input is disabled when not logged in (on startup)
- [ ] Terminal input enables after clicking "Login" and authenticating
- [ ] Terminal input disables after clicking "Logout"
- [ ] Cannot type any characters when logged out
- [ ] Cannot press Enter when logged out
- [ ] Cannot navigate history with arrows when logged out
- [ ] Input works normally when logged in
- [ ] Command execution still blocks input (both states checked)

**Implementation Note**: After completing this phase, the feature is complete. Test all authentication and input scenarios thoroughly.

---

## Testing Strategy

### Unit Tests
Not applicable - primarily integration between GUI and controller that requires manual testing.

### Integration Tests
Not applicable - requires actual Thonny IDE and kiro-cli installation.

### Manual Testing Steps

#### Initial State Testing:
1. **Plugin startup when logged out**:
   - Open Thonny with Kiro plugin
   - Verify terminal displays but cursor does not appear or blink
   - Try typing - verify no characters appear
   - Try pressing Enter - verify nothing happens
   - Try pressing Up/Down arrows - verify no history navigation
   - Verify "Login" button is enabled

2. **Plugin startup when logged in**:
   - Run `kiro-cli login` in external terminal first
   - Open Thonny with Kiro plugin
   - Verify terminal input works immediately after button enables
   - Verify "Logout" button appears

#### Login Flow Testing:
3. **Login from logged out state**:
   - Start with terminal input disabled
   - Click "Login" button
   - Complete authentication in browser
   - Verify button changes to "Logout"
   - Verify terminal input immediately becomes enabled
   - Type a test command and press Enter
   - Verify command executes normally

4. **Command execution while logged in**:
   - Enter a command that takes time to execute
   - Verify input is blocked during execution
   - Verify input re-enables after command completes
   - Verify both authentication and execution states are checked

#### Logout Flow Testing:
5. **Logout from logged in state**:
   - Start with terminal input enabled
   - Click "Logout" button
   - Verify button changes to "Login"
   - Verify terminal input immediately becomes disabled
   - Try typing - verify no characters appear
   - Try pressing Enter - verify nothing happens
   - Verify cursor stops blinking or disappears

#### Edge Cases:
6. **Rapid state changes**:
   - Click Login button
   - Immediately try typing before auth completes
   - Verify input stays disabled until callback fires

7. **Reset button interaction**:
   - Log in and verify input works
   - Enter a command
   - Click Reset button
   - Verify input remains enabled (auth state persists)
   - Log out
   - Click Reset button
   - Verify input remains disabled

8. **Command execution when not logged in**:
   - Ensure logged out state
   - Manually call controller.execute_command() via Python console (if possible)
   - Verify command execution is blocked at executor level (existing behavior)

## Performance Considerations

### Callback Performance:
- Lambda callback invoked on every keystroke
- Property access is O(1) - simple boolean flag read
- No performance impact expected
- Same pattern as existing `is_executing_callback`

### State Change Response Time:
- Authentication state changes trigger callback
- Callback updates controller state immediately
- Next keystroke event automatically sees new state
- Input enable/disable is instantaneous from user perspective

### No Additional Threading:
- Callbacks execute synchronously in event handlers
- No new threads or async operations introduced
- State check happens in main GUI thread

## Migration Notes

### Backwards Compatibility:
This change is **not backwards compatible** - it adds a required parameter to TerminalWidget constructor.

### No Data Migration:
- No persistent state changes
- No configuration file updates
- No database schema changes

### Testing Before Deployment:
- Thoroughly test all authentication scenarios
- Verify no regressions in command execution
- Test with various keyboard input patterns

## References

- Terminal input handling: `thonnycontrib/smart_rover/gui/terminal_widget.py:120-186`
- Execution state callback: `thonnycontrib/smart_rover/gui/terminal_widget.py:18, 26, 75`
- Authentication state: `thonnycontrib/smart_rover/console/terminal_controller.py:35, 49-51`
- GUI integration: `thonnycontrib/smart_rover/gui/dock_view.py:70-77`
- Login/logout implementation: `thoughts/shared/plans/2026-02-10-login-logout-button.md`
- Command executor refactoring: `thoughts/shared/plans/2026-02-12-refactor-execute-to-generic.md`
