# Login/Logout Button Implementation Plan

## Overview

Add a login/logout toggle button to the Kiro plugin GUI that allows users to authenticate with kiro-cli. The button will be positioned on the bottom left (opposite the Reset button), will toggle between "Login" and "Logout" states, and will execute `kiro-cli login` or `kiro-cli logout` commands silently (without terminal output).

## Current State Analysis

The Kiro plugin is a Thonny IDE extension that provides a terminal interface for interacting with kiro-cli. Key components:

### GUI Structure (thonnycontrib/smart_rover/gui/dock_view.py)
- `KiroDockView` extends `ttk.Frame` and is the main container
- Button frame at bottom with Reset button positioned on the right (line 47: `reset_button.pack(side="right")`)
- Terminal widget fills the center space
- Uses Tkinter/ttk for GUI components

### Command Execution (thonnycontrib/smart_rover/console/terminal_controller.py, command_executor.py)
- Commands executed asynchronously via `CommandExecutor` using subprocess and threading
- `_is_executing` flag prevents concurrent command execution
- Two execution methods available:
  - `execute(command: Command, callback)` - Generic subprocess executor for any command
  - `execute_chat(command: Command, callback)` - Wraps commands in kiro-cli chat interface
- All chat command output displayed in terminal via `output_callback`

### Authentication Pattern
- Kiro CLI stores credentials in `~/.local/share/kiro-cli/data.sqlite3`
- `kiro-cli login` returns error message when already logged in
- `kiro-cli logout` signs out and clears credentials
- No dedicated status check command exists

### Key Discoveries:
- Reset button pattern: `thonnycontrib/smart_rover/gui/dock_view.py:42-47` shows simple button with command callback
- Command execution: `thonnycontrib/smart_rover/console/command_executor.py:22-75` has generic `execute()` method for any subprocess command
- Chat wrapping: `command_executor.py:77-99` has `execute_chat()` that wraps commands in kiro-cli chat interface
- State management: `is_executing` property pattern used in `command_executor.py:17-20` and `terminal_controller.py:41-44`
- Button positioning: `side="right"` for Reset button, so `side="left"` will position auth button on left

## Desired End State

### Functionality
- Login/logout button visible on bottom left of GUI (opposite Reset button)
- On initialization, run `kiro-cli login` to check status:
  - If output contains "error" → user is logged in → show "Logout" button
  - If no error → user is not logged in → show "Login" button
- When "Login" clicked: run `kiro-cli login`, transform to "Logout" button
- When "Logout" clicked: run `kiro-cli logout`, transform to "Login" button
- Button disabled during command execution (prevent double-clicks)
- Commands execute silently (no terminal output shown)

### Verification
- Button appears in bottom left corner
- Initial state correctly reflects authentication status
- Clicking button executes appropriate command and toggles state
- Button disables during execution and re-enables after completion
- No terminal output from authentication commands

## What We're NOT Doing

- NOT adding authentication to existing chat commands (they already use kiro-cli)
- NOT implementing credential storage or token management (handled by kiro-cli)
- NOT adding visual indicators beyond button text (no icons, colors, or status messages)
- NOT adding error messages to terminal for failed authentication (silent operation)
- NOT adding configuration options for authentication method
- NOT implementing session expiration detection or auto-refresh
- NOT adding multi-account support

## Implementation Approach

We'll implement this in three phases:

1. **Phase 1**: Add authentication methods to `TerminalController`
2. **Phase 2**: Add authentication button to GUI with state management
3. **Phase 3**: Add initialization logic to check and set initial button state

This approach ensures we build the infrastructure before adding UI components, and test the UI before implementing the initialization check.

**Note**: Phase 1 is simplified because the recent refactoring (see `thoughts/shared/plans/2026-02-12-refactor-execute-to-generic.md`) already provides a generic `execute()` method in CommandExecutor that can run any subprocess command. We leverage this existing infrastructure instead of creating duplicate code.

---

## Phase 1: Add Authentication Methods to TerminalController

### Overview
Add authentication helper methods to TerminalController. The generic `execute()` method already exists in CommandExecutor (from recent refactoring), so we only need to add the TerminalController methods that use it for login/logout operations.

### Changes Required:

#### 1. TerminalController - Add Authentication Methods
**File**: `thonnycontrib/smart_rover/console/terminal_controller.py`
**Changes**: Add methods for authentication checking and execution

Add new property after line 44:

```python
@property
def is_logged_in(self) -> bool:
    """Check if user is logged in to kiro-cli."""
    return self._is_logged_in

@property
def auth_button_enabled(self) -> bool:
    """Check if auth button should be enabled."""
    return not self._executor.is_executing
```

Add instance variables in `__init__` after line 34:

```python
self._is_logged_in = False
self._auth_state_callback = None
```

Add new methods after line 125:

```python
def set_auth_state_callback(self, callback: Callable[[bool], None]) -> None:
    """Set callback for authentication state changes."""
    self._auth_state_callback = callback

def check_login_status(self, callback: Callable[[bool], None]) -> None:
    """Check if user is logged in by running kiro-cli login."""
    def handle_result(result: CommandResult):
        # If output contains "error", user is already logged in
        is_logged_in = "error" in result.stdout.lower() or "error" in result.stderr.lower()
        self._is_logged_in = is_logged_in
        callback(is_logged_in)

    # Use execute() with a Command object for raw kiro-cli login command
    login_command = Command(
        text="kiro-cli login",
        working_directory=self._cwd
    )
    self._executor.execute(login_command, handle_result)

def login(self) -> None:
    """Execute kiro-cli login command."""
    def handle_result(result: CommandResult):
        # After login attempt, update state
        # If no error, login was successful or already logged in
        is_logged_in = "error" not in result.stdout.lower() and "error" not in result.stderr.lower()
        self._is_logged_in = is_logged_in
        if self._auth_state_callback:
            self._auth_state_callback(is_logged_in)

    # Use execute() with a Command object for raw kiro-cli login command
    login_command = Command(
        text="kiro-cli login",
        working_directory=self._cwd
    )
    self._executor.execute(login_command, handle_result)

def logout(self) -> None:
    """Execute kiro-cli logout command."""
    def handle_result(result: CommandResult):
        # After logout, user should not be logged in
        self._is_logged_in = False
        if self._auth_state_callback:
            self._auth_state_callback(False)

    # Use execute() with a Command object for raw kiro-cli logout command
    logout_command = Command(
        text="kiro-cli logout",
        working_directory=self._cwd
    )
    self._executor.execute(logout_command, handle_result)
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/terminal_controller.py`
- [x] No import errors when loading module: `python -c "from thonnycontrib.smart_rover.console.terminal_controller import TerminalController; print('Success')"`

#### Manual Verification:
- [ ] Login/logout methods can be called successfully
- [ ] Commands execute without displaying output in terminal (silent execution)
- [ ] State tracking correctly updates after commands
- [ ] Auth callbacks fire correctly when state changes

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Add Authentication Button to GUI

### Overview
Add the login/logout button to the GUI with state management and event handling.

### Changes Required:

#### 1. KiroDockView - Add Authentication Button
**File**: `thonnycontrib/smart_rover/gui/dock_view.py`
**Changes**: Add auth button to button frame and implement state management

After line 40 (after button_frame.pack), add auth button creation:

```python
# Authentication button
self.auth_button = ttk.Button(
    button_frame,
    text="Login",
    command=self._on_auth_button_clicked,
    state="disabled"  # Disabled until initial check completes
)
self.auth_button.pack(side="left")
```

Update `_initialize_controller` method (after line 77):

```python
def _initialize_controller(self):
    """Initialize the terminal controller."""
    self.controller = TerminalController(
        output_callback=self.terminal_widget.write_output,
        clear_callback=self.terminal_widget.clear,
        prompt_callback=self.terminal_widget.show_prompt,
        animation_start_callback=self.terminal_widget.start_animation,
        animation_stop_callback=self.terminal_widget.stop_animation,
        schedule_callback=self.terminal_widget.schedule_callback
    )
    # Set auth state callback for button updates
    self.controller.set_auth_state_callback(self._on_auth_state_changed)
```

Add new methods after line 102:

```python
def _on_auth_button_clicked(self):
    """Handle authentication button click."""
    if self.controller.is_logged_in:
        # Currently logged in, so logout
        self._update_auth_button_state(enabled=False)
        self.controller.logout()
    else:
        # Currently logged out, so login
        self._update_auth_button_state(enabled=False)
        self.controller.login()

def _on_auth_state_changed(self, is_logged_in: bool):
    """Handle authentication state change from controller."""
    self._update_auth_button_state(enabled=True, is_logged_in=is_logged_in)

def _update_auth_button_state(self, enabled: bool, is_logged_in: bool = None):
    """Update auth button text and enabled state."""
    if is_logged_in is not None:
        button_text = "Logout" if is_logged_in else "Login"
        self.auth_button.config(text=button_text)

    button_state = "normal" if enabled else "disabled"
    self.auth_button.config(state=button_state)
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/gui/dock_view.py`
- [x] No import errors when loading plugin in Thonny

#### Manual Verification:
- [ ] Auth button appears on bottom left of GUI
- [ ] Button is positioned opposite the Reset button (left vs right)
- [ ] Button starts as disabled with "Login" text
- [ ] Clicking button disables it during execution
- [ ] Button text changes between "Login" and "Logout" based on state
- [ ] Button re-enables after command completes

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Initialize Authentication State on Startup

### Overview
Check authentication status when the plugin initializes and set the button state accordingly.

### Changes Required:

#### 1. KiroDockView - Add Initialization Check
**File**: `thonnycontrib/smart_rover/gui/dock_view.py`
**Changes**: Add login status check during welcome message display

Update `_show_welcome_message` method (replace lines 79-84):

```python
def _show_welcome_message(self):
    """Display the welcome message."""
    self.terminal_widget.write_output("Kiro Interactive CLI\n")
    self.terminal_widget.write_output(f"Working Directory: {self.controller.working_directory}\n")
    self.terminal_widget.write_output(UIConfig.SEPARATOR_LINE + "\n\n")
    self.terminal_widget.show_prompt()

    # Check authentication status and update button
    self._check_initial_auth_state()

def _check_initial_auth_state(self):
    """Check initial authentication state and update button."""
    def handle_initial_state(is_logged_in: bool):
        self._update_auth_button_state(enabled=True, is_logged_in=is_logged_in)

    self.controller.check_login_status(handle_initial_state)
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/gui/dock_view.py`
- [x] Plugin loads in Thonny without errors
- [x] No exceptions during initialization

#### Manual Verification:
- [ ] On first load when logged out, button shows "Login" and is enabled
- [ ] On first load when logged in, button shows "Logout" and is enabled
- [ ] Button state correctly reflects actual kiro-cli authentication status
- [ ] No terminal output displayed during initial check
- [ ] Welcome message displays normally without delay
- [ ] Button becomes enabled shortly after plugin loads

**Implementation Note**: After completing this phase, the feature is complete. Verify all functionality end-to-end.

---

## Testing Strategy

### Unit Tests
Not applicable for this feature - primarily GUI and integration work that requires manual testing with actual kiro-cli installation.

### Integration Tests
Not applicable - would require mocking kiro-cli commands, which is beyond the scope of this feature.

### Manual Testing Steps

#### Initial State Testing:
1. **When logged out**:
   - Fresh install or after `kiro-cli logout` in terminal
   - Open Thonny with Kiro plugin
   - Verify button shows "Login" and is enabled after 1-2 seconds

2. **When logged in**:
   - Run `kiro-cli login` in external terminal and complete authentication
   - Open Thonny with Kiro plugin
   - Verify button shows "Logout" and is enabled after 1-2 seconds

#### Login Flow Testing:
3. **Login from logged out state**:
   - Start with "Login" button visible
   - Click "Login" button
   - Verify button becomes disabled immediately
   - Complete kiro-cli authentication in browser (if prompted)
   - Verify button changes to "Logout" and becomes enabled
   - Verify no output appears in terminal

4. **Login when already logged in**:
   - Start with "Logout" button visible (already logged in)
   - Manually run `kiro-cli logout` in terminal
   - Click "Login" button in plugin
   - Verify button disables during execution
   - Verify button changes to "Logout" and becomes enabled
   - Verify authentication works for subsequent kiro-cli commands

#### Logout Flow Testing:
5. **Logout from logged in state**:
   - Start with "Logout" button visible
   - Click "Logout" button
   - Verify button becomes disabled immediately
   - Verify button changes to "Login" and becomes enabled
   - Verify subsequent kiro-cli commands fail with authentication error
   - Verify no output appears in terminal from logout command

#### Edge Cases:
6. **Rapid clicking**:
   - Click auth button twice rapidly
   - Verify only one command executes
   - Verify button state updates correctly after completion

7. **Concurrent with other commands**:
   - Type a command in terminal (e.g., "help")
   - While command is executing (animation showing), click auth button
   - Verify auth command waits until first command completes
   - Verify both commands execute successfully

8. **Reset button interaction**:
   - Log in via auth button
   - Click Reset button
   - Verify auth button maintains "Logout" state (doesn't reset)
   - Verify authentication persists after reset

## Performance Considerations

### Initial Check Performance:
- Authentication check runs asynchronously during initialization
- Button starts disabled and enables after check completes (typically 1-2 seconds)
- Does not block Thonny startup or plugin loading
- Welcome message displays immediately while check runs in background

### Command Execution Performance:
- Login command may take several seconds (browser authentication flow)
- Logout command is typically fast (< 1 second)
- Both execute in background threads without blocking GUI
- Button disable/enable provides visual feedback of execution state

### Concurrency:
- Uses existing `_is_executing` flag to prevent concurrent command execution
- Safe to call login/logout while other commands are queued
- State changes scheduled on main thread for thread safety

## Migration Notes

Not applicable - this is a new feature with no existing state to migrate.

## References

- Reset button implementation: `thonnycontrib/smart_rover/gui/dock_view.py:42-47`
- Generic command execution: `thonnycontrib/smart_rover/console/command_executor.py:22-75` (execute method)
- Chat command wrapper: `thonnycontrib/smart_rover/console/command_executor.py:77-99` (execute_chat method)
- State management: `thonnycontrib/smart_rover/console/terminal_controller.py:41-44`
- Kiro CLI authentication: https://kiro.dev/docs/cli/authentication
- Research findings: Web search agents identified credential storage at `~/.local/share/kiro-cli/data.sqlite3`
- Related refactoring: `thoughts/shared/plans/2026-02-12-refactor-execute-to-generic.md` (completed)
