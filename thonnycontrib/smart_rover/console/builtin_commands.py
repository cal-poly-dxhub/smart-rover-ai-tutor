"""Built-in command handlers for the terminal."""

import os
from typing import Optional, Callable
from thonnycontrib.smart_rover.models.command import Command, CommandResult


class BuiltinCommandHandler:
    """Handles built-in terminal commands like cd and clear."""

    def __init__(self):
        """Initialize the built-in command handler."""
        self._commands = {
            'cd': self._handle_cd,
            'clear': self._handle_clear,
        }

    def is_builtin(self, command: Command) -> bool:
        """Check if a command is built-in."""
        command_name = command.text.strip().split()[0] if command.text.strip() else ""
        return command_name in self._commands

    def execute(self, command: Command, clear_terminal_callback: Optional[Callable] = None) -> CommandResult:
        """Execute a built-in command."""
        parts = command.text.strip().split(maxsplit=1)
        command_name = parts[0] if parts else ""

        handler = self._commands.get(command_name)
        if handler:
            return handler(command, parts, clear_terminal_callback)

        return CommandResult(
            success=False,
            error_message=f"Unknown built-in command: {command_name}"
        )

    def _handle_cd(self, command: Command, parts: list, clear_callback) -> CommandResult:
        """Handle the cd command."""
        if len(parts) < 2:
            return CommandResult(
                success=False,
                error_message="cd: missing directory argument"
            )

        new_dir = parts[1].strip()

        try:
            if new_dir.startswith("~"):
                new_dir = os.path.expanduser(new_dir)

            if not os.path.isabs(new_dir):
                new_dir = os.path.join(command.working_directory, new_dir)
            new_dir = os.path.normpath(new_dir)

            if not os.path.isdir(new_dir):
                return CommandResult(
                    success=False,
                    error_message=f"cd: directory not found: {new_dir}"
                )

            os.chdir(new_dir)

            return CommandResult(
                success=True,
                stdout=f"Changed directory to: {new_dir}\n"
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error_message=f"cd: error changing directory: {str(e)}"
            )

    def _handle_clear(self, command: Command, parts: list, clear_callback) -> CommandResult:
        """Handle the clear command."""
        if clear_callback:
            clear_callback()

        return CommandResult(success=True)
