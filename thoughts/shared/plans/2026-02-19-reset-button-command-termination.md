# Reset Button Command Termination Implementation Plan

## Overview

Fix the reset button to properly terminate running commands when clicked. Currently, reset only stops animations and clears the terminal, but any running subprocess continues in the background.

## Current State Analysis

The current implementation has several limitations:
- **No subprocess tracking**: `subprocess.run()` is used without keeping a reference (`command_executor.py:43-51`)
- **Fire-and-forget threading**: Thread object not stored after creation (`command_executor.py:75`)
- **Reset doesn't stop commands**: Reset only clears UI and stops animation (`terminal_controller.py:127-130`)
- **Daemon threads**: Threads marked as daemon but not cancellable (`command_executor.py:75`)

When reset is clicked:
1. Terminal state is reset (`_is_first_command = True`)
2. Animation is stopped
3. Terminal display is cleared
4. **BUT**: Any running subprocess continues until completion or timeout

### Key Discoveries:
- `subprocess.run()` blocks until completion - no way to interrupt it (`command_executor.py:43-51`)
- No PID tracking or subprocess reference stored
- `_is_executing` flag remains `True` until command completes naturally
- 30-second timeout is the only way commands currently terminate

## Desired End State

After implementation:
- Reset button immediately terminates any running subprocess
- Properly cleans up threads and resources
- Resets `_is_executing` flag so new commands can run
- Prevents zombie processes or orphaned subprocesses
- Maintains backward compatibility with existing callback patterns

### Verification
- Click reset while a long-running command executes → command stops immediately
- Terminal becomes responsive to new commands after reset
- No orphaned processes left running
- Animation stops and terminal clears as before

## What We're NOT Doing

- NOT implementing command queuing or multiple concurrent commands
- NOT adding complex thread pooling or async/await patterns
- NOT changing the callback-based architecture
- NOT adding pause/resume functionality
- NOT implementing graceful shutdown with SIGTERM (will use SIGKILL for immediate termination)
- NOT adding command history persistence across resets

## Implementation Approach

Replace `subprocess.run()` with `subprocess.Popen()` to gain control over the running process. Store references to both the subprocess and thread objects so they can be terminated on reset.

## Phase 1: Refactor CommandExecutor to Use Popen

### Overview
Replace `subprocess.run()` with `Popen()` for better process control and add tracking of running subprocess.

### Changes Required:

#### 1. CommandExecutor - Switch to Popen and Add Tracking
**File**: `thonnycontrib/smart_rover/console/command_executor.py`
**Changes**: Replace subprocess.run with Popen and add process tracking

Replace the entire class (lines 10-100) with:

```python
class CommandExecutor:
    """Executes commands using subprocess in a separate thread."""

    def __init__(self):
        """Initialize the command executor."""
        self._is_executing = False
        self._current_process = None
        self._current_thread = None

    @property
    def is_executing(self) -> bool:
        """Check if a command is currently executing."""
        return self._is_executing

    def execute(self, command: Command, callback: Callable[[CommandResult], None]) -> None:
        """Execute a raw command asynchronously.

        This is the generic subprocess executor that can run any command.
        Use execute_chat() for commands that should go through kiro-cli chat.

        Args:
            command: Command object with text and working_directory
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
                # Use Popen instead of run for better control
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
                    self._current_process.communicate()  # Clean up
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
                self._current_thread = None
                self._is_executing = False

        self._current_thread = threading.Thread(target=run_command, daemon=True)
        self._current_thread.start()

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

        # Create a new Command object with the wrapped kiro-cli command
        wrapped_command = Command(
            text=kiro_command,
            working_directory=command.working_directory
        )

        # Delegate to generic execute() method
        self.execute(wrapped_command, callback)

    def terminate_current(self) -> None:
        """Terminate the currently running command if any."""
        if self._current_process and self._current_process.poll() is None:
            # Process is still running, terminate it
            try:
                self._current_process.terminate()
                # Give it a moment to terminate gracefully
                try:
                    self._current_process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    # Force kill if terminate didn't work
                    self._current_process.kill()
                    self._current_process.wait()
            except:
                pass  # Process may have already terminated
            finally:
                self._current_process = None

        # Reset the execution flag
        self._is_executing = False
        self._current_thread = None
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/command_executor.py`
- [x] No import errors: `python -c "from thonnycontrib.smart_rover.console.command_executor import CommandExecutor; print('Success')"`

#### Manual Verification:
- [ ] Commands still execute normally
- [ ] Output is captured correctly
- [ ] Timeout still works (test with `sleep 35`)
- [ ] Error handling works for invalid commands

**Implementation Note**: After completing this phase and verifying existing functionality still works, proceed to Phase 2.

---

## Phase 2: Update TerminalController Reset Method

### Overview
Modify the reset method to call the new termination functionality.

### Changes Required:

#### 1. TerminalController - Update reset() Method
**File**: `thonnycontrib/smart_rover/console/terminal_controller.py`
**Changes**: Modify reset method to terminate running commands

Replace the reset() method (lines 127-130) with:

```python
def reset(self) -> None:
    """Reset the terminal state and terminate any running command."""
    # Terminate any running command
    self._executor.terminate_current()

    # Reset terminal state
    self._is_first_command = True
    self._animation_stop()
```

### Success Criteria:

#### Automated Verification:
- [x] Python syntax is valid: `python -m py_compile thonnycontrib/smart_rover/console/terminal_controller.py`
- [x] Module loads correctly: `python -c "from thonnycontrib.smart_rover.console.terminal_controller import TerminalController; print('Success')"`

#### Manual Verification:
- [ ] Reset button stops running commands immediately
- [ ] Terminal becomes responsive after reset
- [ ] Animation stops as before
- [ ] Terminal clears properly

**Implementation Note**: After completing this phase, proceed to final testing.

---

## Testing Strategy

### Manual Testing Steps

1. **Test basic command termination**:
   - Run a long command: `sleep 20`
   - Click reset button while it's running
   - Verify command stops immediately
   - Verify terminal is ready for new commands

2. **Test with output-producing commands**:
   - Run: `for i in {1..100}; do echo $i; sleep 1; done`
   - Click reset after a few numbers appear
   - Verify output stops immediately
   - Verify no more numbers appear after reset

3. **Test with kiro-cli commands**:
   - Start a kiro-cli chat command
   - Click reset while waiting for response
   - Verify command is terminated
   - Verify can start new kiro-cli session

4. **Test rapid reset clicks**:
   - Start a command
   - Click reset multiple times rapidly
   - Verify no errors or crashes
   - Verify terminal remains functional

5. **Test login flow interruption**:
   - Click login button
   - Click reset while browser is opening
   - Verify login process is cancelled
   - Verify can retry login

6. **Test process cleanup**:
   - Run: `ps aux | grep sleep` to check for any sleep processes
   - Run a long sleep command in the terminal
   - Click reset
   - Run `ps aux | grep sleep` again
   - Verify no orphaned sleep processes remain

7. **Test edge cases**:
   - Reset with no command running (should work normally)
   - Start command, wait for natural completion, then reset
   - Reset during animation but no command

## Performance Considerations

### Process Management:
- `Popen` has similar performance to `subprocess.run`
- `communicate()` buffers all output in memory (same as current implementation)
- Termination is nearly instant with `terminate()` or `kill()`

### Thread Safety:
- Process reference cleared in finally block prevents race conditions
- `_is_executing` flag properly reset even if termination fails

### Resource Cleanup:
- `communicate()` called after kill to prevent zombie processes
- Daemon threads still terminate on program exit
- No resource leaks from interrupted commands

## Migration Notes

This change is backward compatible:
- Existing callback patterns unchanged
- Same CommandResult structure
- Same threading model (daemon threads)
- Only internal implementation changes

## References

- Current implementation: `thonnycontrib/smart_rover/console/command_executor.py:22-75`
- Reset button handler: `thonnycontrib/smart_rover/console/terminal_controller.py:127-130`
- Python subprocess documentation: https://docs.python.org/3/library/subprocess.html#subprocess.Popen
- Research findings: Agent analysis of current subprocess handling patterns