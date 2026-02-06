"""Command execution with subprocess and threading."""

import subprocess
import threading
from typing import Callable
from thonnycontrib.models.command import Command, CommandResult
from thonnycontrib.config.settings import ExecutionConfig


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
        """Execute a command asynchronously."""
        if self._is_executing:
            callback(CommandResult(
                success=False,
                error_message="A command is already executing"
            ))
            return

        self._is_executing = True

        if command.is_first:
            kiro_command = f'kiro-cli chat --no-interactive "{command.text}"'
        else:
            kiro_command = f'kiro-cli chat --no-interactive --resume "{command.text}"'

        def run_command():
            try:
                result = subprocess.run(
                    kiro_command,
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
