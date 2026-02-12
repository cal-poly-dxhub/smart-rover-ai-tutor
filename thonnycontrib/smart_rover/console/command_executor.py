"""Command execution with subprocess and threading."""

import subprocess
import threading
from typing import Callable
from thonnycontrib.smart_rover.models.command import Command, CommandResult
from thonnycontrib.smart_rover.config.settings import ExecutionConfig


class CommandExecutor:
    """Executes commands using subprocess in a separate thread."""

    def __init__(self):
        """Initialize the command executor."""
        self._is_executing = False

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
                result = subprocess.run(
                    command.text,
                    shell=True,
                    executable=ExecutionConfig.SHELL_EXECUTABLE,
                    capture_output=True,
                    text=True,
                    cwd=command.working_directory,
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

        # Create a new Command object with the wrapped kiro-cli command
        wrapped_command = Command(
            text=kiro_command,
            working_directory=command.working_directory
        )

        # Delegate to generic execute() method
        self.execute(wrapped_command, callback)
