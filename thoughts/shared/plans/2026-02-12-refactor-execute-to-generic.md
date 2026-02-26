# Refactor execute() to Handle All Commands with Chat Wrapper

## Overview

Refactor `CommandExecutor` to separate generic subprocess execution from kiro-cli-specific chat wrapping. The base `execute()` method will become a general-purpose command executor, while a new `execute_chat()` method will handle the specific "kiro-cli chat --no-interactive" wrapping behavior. This creates a cleaner architecture where specialized command types (chat, login, logout) are wrappers over generic subprocess execution.

## Current State Analysis

The current implementation tightly couples kiro-cli chat wrapping with subprocess execution in a single `execute()` method.

### CommandExecutor (thonnycontrib/smart_rover/console/command_executor.py)

**Current execute() method** (lines 22-72):
- Takes `Command` object with `is_first` flag and `working_directory`
- Hardcodes kiro-cli chat wrapping logic (lines 33-36)
- Handles threading, locking, subprocess execution, and error handling
- No way to execute raw commands without chat wrapping

**Key Implementation Details:**
- Line 15: `_is_executing` flag prevents concurrent command execution
- Lines 24-29: Lock check returns error if already executing
- Lines 33-34: First command wrapped as `kiro-cli chat --no-interactive "{command.text}"`
- Lines 35-36: Subsequent commands add `--resume` flag
- Lines 38-72: Thread spawns to run subprocess with timeout and error handling
- Line 70: `_is_executing` reset in finally block for cleanup

### TerminalController (thonnycontrib/smart_rover/console/terminal_controller.py)

**Usage of execute()** (line 74):
- Creates `Command` object with user input (lines 54-58)
- Calls `self._executor.execute(command, self._handle_external_result)`
- Handles result via callback with UI updates

### Command Model (thonnycontrib/smart_rover/models/command.py)

**Command dataclass** (lines 7-21):
- `text: str` - User's command text
- `is_first: bool` - Flag for conversation state (determines --resume usage)
- `working_directory: str` - Execution directory

### Key Discoveries:
- All external commands are forced through kiro-cli chat wrapping (command_executor.py:33-36)
- No mechanism exists for raw command execution (needed for login/logout features)
- Threading and locking logic is embedded with chat-specific logic
- The `is_first` flag is only used for chat session management (determining --resume)

## Desired End State

### Architecture

**CommandExecutor** with two methods:
1. `execute(command_text: str, working_directory: str, callback)` - Generic subprocess runner
   - Takes raw command string (no Command object needed)
   - Handles threading, locking, subprocess execution
   - Reusable for any command type

2. `execute_chat(command: Command, callback)` - Chat-specific wrapper
   - Takes Command object (needs is_first flag)
   - Constructs kiro-cli chat command string
   - Delegates to execute() for actual execution

**TerminalController** updated to call execute_chat():
- Line 74 changes from `execute(command, callback)` to `execute_chat(command, callback)`
- All other logic remains identical

### Verification

After refactoring:
- Existing chat commands work identically (no user-visible changes)
- execute() can be used for future features (login/logout) without modification
- Code is more maintainable with separation of concerns
- Threading and locking behavior unchanged

## What We're NOT Doing

- NOT changing the Command or CommandResult data models
- NOT modifying built-in command handling (cd, clear remain unchanged)
- NOT implementing login/logout features (this refactor just enables them)
- NOT changing the user interface or terminal output behavior
- NOT modifying error handling or timeout logic
- NOT adding new configuration options
- NOT changing how callbacks work or result handling
- NOT modifying the threading implementation

## Implementation Approach

**Two-phase refactoring with backwards compatibility:**

1. **Phase 1: Refactor CommandExecutor**
   - Rename current execute() logic to extract core subprocess execution
   - Create new generic execute() that takes raw command string
   - Create execute_chat() wrapper that constructs kiro-cli command and delegates
   - All existing functionality preserved

2. **Phase 2: Update TerminalController**
   - Change single line: execute() call to execute_chat()
   - Verify all commands work as before

This approach minimizes risk - Phase 1 adds new methods without removing anything, Phase 2 is a single line change.

---

## Phase 1: Refactor CommandExecutor

### Overview
Extract generic subprocess execution logic into execute() and create execute_chat() wrapper for kiro-cli-specific behavior.

### Changes Required:

#### 1. CommandExecutor - Refactor execute() and Add execute_chat()
**File**: `thonnycontrib/smart_rover/console/command_executor.py`

**Step 1**: Add import for `os` module (needed for working directory in execute)

After line 4 (after `import threading`), add:
```python
import os
```

**Step 2**: Replace execute() method (lines 22-72) with two methods:

Delete lines 22-72 and replace with:

```python
    def execute(self, command_text: str, working_directory: str, callback: Callable[[CommandResult], None]) -> None:
        """Execute a raw command string asynchronously.

        This is the generic subprocess executor that can run any command.
        Use execute_chat() for commands that should go through kiro-cli chat.

        Args:
            command_text: The raw command string to execute
            working_directory: Directory where command should execute
            callback: Function to call with CommandResult when complete
        """
        if self._is_executing:
            callback(CommandResult(
                success=False,
                error_message="A command is already executing"
            ))
            return

        self._is_executing = True

        def run_command():
            try:
                result = subprocess.run(
                    command_text,
                    shell=True,
                    executable=ExecutionConfig.SHELL_EXECUTABLE,
                    capture_output=True,
                    text=True,
                    cwd=working_directory,
                    timeout=ExecutionConfig.TIMEOUT_SECONDS
                )

                command_result = CommandResult(
                    stdout=result.stdout,
                    stderr=result.stderr,
                    return_code=result.returncode,
                    success=(result.returncode == 0)
                )

                callback(command_result)

            except subprocess.TimeoutExpired:
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
                self._is_executing = False

        threading.Thread(target=run_command, daemon=True).start()

    def execute_chat(self, command: Command, callback: Callable[[CommandResult], None]) -> None:
        """Execute a command through kiro-cli chat interface.

        Wraps the user's command in 'kiro-cli chat --no-interactive' and
        optionally adds --resume for subsequent commands in a conversation.

        Args:
            command: Command object with text, is_first flag, and working_directory
            callback: Function to call with CommandResult when complete
        """
        if command.is_first:
            kiro_command = f'kiro-cli chat --no-interactive "{command.text}"'
        else:
            kiro_command = f'kiro-cli chat --no-interactive --resume "{command.text}"'

        # Delegate to generic execute() method
        self.execute(kiro_command, command.working_directory, callback)
```

**Changes Summary:**
- Old execute() behavior split into two methods
- New execute() is generic: takes string command + working_dir, no Command object
- New execute_chat() handles kiro-cli wrapping, delegates to execute()
- All threading, locking, error handling remains in execute()
- Line count similar (~75 lines total vs 51 lines original)

### Success Criteria:

#### Automated Verification:
- [ ] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/command_executor.py`
- [ ] No import errors when loading module: `python -c "from thonnycontrib.smart_rover.console.command_executor import CommandExecutor; print('Import successful')"`
- [ ] Class instantiates without errors: `python -c "from thonnycontrib.smart_rover.console.command_executor import CommandExecutor; e = CommandExecutor(); print('Instantiation successful')"`

#### Manual Verification:
- [ ] execute() method exists and has correct signature
- [ ] execute_chat() method exists and has correct signature
- [ ] Both methods have proper docstrings
- [ ] No syntax or linting errors in the file

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation before proceeding to Phase 2. At this point, the old execute() still works because execute_chat() delegates to the new execute().

---

## Phase 2: Update TerminalController to Use execute_chat()

### Overview
Update TerminalController to call execute_chat() instead of execute() for external commands.

### Changes Required:

#### 1. TerminalController - Update execute() Call
**File**: `thonnycontrib/smart_rover/console/terminal_controller.py`

**Change line 74** from:
```python
        self._executor.execute(command, self._handle_external_result)
```

to:
```python
        self._executor.execute_chat(command, self._handle_external_result)
```

**That's it!** Single line change.

### Success Criteria:

#### Automated Verification:
- [ ] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/terminal_controller.py`
- [ ] No import errors when loading module: `python -c "from thonnycontrib.smart_rover.console.terminal_controller import TerminalController; print('Import successful')"`
- [ ] Plugin loads in Thonny without errors

#### Manual Verification:
- [ ] Terminal commands execute normally (test with simple commands like "help")
- [ ] First command creates new kiro-cli chat session
- [ ] Subsequent commands use --resume flag (verify via kiro-cli session continuity)
- [ ] Command history works correctly
- [ ] Built-in commands (cd, clear) still work
- [ ] Reset button still functions correctly
- [ ] Concurrent execution prevention still works (try rapid command entry)
- [ ] Timeouts still trigger after 30 seconds
- [ ] Error messages display correctly for failed commands
- [ ] Terminal animation starts/stops correctly during command execution

**Implementation Note**: After completing this phase, the refactoring is complete. All existing functionality should work identically to before, but the codebase now has a clean separation between generic command execution and chat-specific wrapping.

---

## Testing Strategy

### Unit Tests
Not implemented in this codebase currently. Future work could add:
- Test execute() with mock subprocess
- Test execute_chat() calls execute() with correct command string
- Test _is_executing lock prevents concurrent execution
- Test timeout handling
- Test error handling for various subprocess exceptions

### Integration Tests
Manual testing required as the plugin integrates with Thonny IDE and kiro-cli.

### Manual Testing Steps

#### Basic Command Execution:
1. **Simple chat command**:
   - Open Thonny with Kiro plugin
   - Enter command: "What is Python?"
   - Verify: Command executes, kiro-cli responds, output appears in terminal
   - Verify: Animation shows during execution

2. **Follow-up command (resume test)**:
   - After first command completes, enter: "Tell me more"
   - Verify: Command uses same kiro-cli session (context maintained)
   - Verify: Response relates to previous question

3. **Built-in command**:
   - Enter: "cd .."
   - Verify: Directory changes, no kiro-cli invocation
   - Enter: "clear"
   - Verify: Terminal clears, working directory shown

#### Concurrency and State:
4. **Concurrent execution prevention**:
   - Enter a long-running command
   - Immediately enter another command
   - Verify: Second command queued or rejected (no concurrent execution)

5. **Reset button**:
   - Enter a command
   - Click Reset button
   - Enter new command
   - Verify: New session created (is_first=True), no context from before reset

#### Error Handling:
6. **Invalid command**:
   - Enter: "this is not a valid kiro command"
   - Verify: Error message displayed clearly
   - Verify: Terminal remains functional

7. **Timeout test** (optional, takes 30+ seconds):
   - Enter a command that hangs: "sleep 100"
   - Wait 30 seconds
   - Verify: Timeout error message appears
   - Verify: Terminal returns to prompt, ready for next command

#### State Verification:
8. **Session continuity**:
   - Enter: "My name is Alice"
   - Enter: "What is my name?"
   - Verify: kiro-cli responds with "Alice" (context maintained)
   - Click Reset
   - Enter: "What is my name?"
   - Verify: kiro-cli doesn't know (session reset worked)

## Performance Considerations

### No Performance Changes Expected:
- Same threading model (daemon threads)
- Same locking mechanism (_is_executing flag)
- Same subprocess execution with shell=True
- Same timeout handling (30 seconds default)
- Method call overhead negligible (execute_chat() just constructs string and delegates)

### Code Maintainability Improvements:
- Separation of concerns: generic execution vs chat wrapping
- execute() now reusable for login/logout and other raw commands
- Easier to test (can test execute() independently of chat logic)
- Clearer intent in code (execute() vs execute_chat() names are explicit)

### Memory and Threading:
- No change to threading behavior (still one daemon thread per command)
- No additional memory overhead
- Lock prevents thread contention (unchanged)

## Migration Notes

### Backwards Compatibility:
This refactoring maintains complete backwards compatibility:
- All external callers still work (TerminalController.execute_command unchanged)
- Command and CommandResult models unchanged
- Terminal UI behavior unchanged
- Configuration unchanged

### Future Extensibility:
This refactoring enables:
1. **Login/Logout commands**: Can call execute("kiro-cli login", os.getcwd(), callback)
2. **Raw command execution**: Can expose execute() for commands that shouldn't use chat wrapper
3. **Other kiro-cli subcommands**: Could add execute_version(), execute_config(), etc.
4. **Testing**: Can mock execute() to test chat wrapping logic independently

### No Database/State Migration:
No persistent state changes, no config file updates needed.

## References

- Current implementation: `thonnycontrib/smart_rover/console/command_executor.py:22-72`
- Usage in controller: `thonnycontrib/smart_rover/console/terminal_controller.py:74`
- Command model: `thonnycontrib/smart_rover/models/command.py:7-21`
- Login/logout plan (future work): `thoughts/shared/plans/2026-02-10-login-logout-button.md`
- Original refactoring plan: `thoughts/shared/plans/2026-02-05-refactor-oop-structure.md`
