"""Terminal controller coordinating console operations."""

import os
from typing import Callable, Optional
import webbrowser
from thonnycontrib.smart_rover.models.command import Command, CommandResult
from thonnycontrib.smart_rover.console.command_executor import CommandExecutor
from thonnycontrib.smart_rover.console.command_history import CommandHistory
from thonnycontrib.smart_rover.console.builtin_commands import BuiltinCommandHandler


class TerminalController:
    """Coordinates terminal operations."""

    def __init__(self,
                 output_callback: Callable[[str], None],
                 clear_callback: Callable[[], None],
                 prompt_callback: Callable[[], None],
                 animation_start_callback: Callable[[], None],
                 animation_stop_callback: Callable[[], None],
                 schedule_callback: Callable[[Callable], None]):
        """Initialize the terminal controller."""
        self.history = CommandHistory()
        self._executor = CommandExecutor()
        self._builtin_handler = BuiltinCommandHandler()

        self._output = output_callback
        self._clear = clear_callback
        self._prompt = prompt_callback
        self._animation_start = animation_start_callback
        self._animation_stop = animation_stop_callback
        self._schedule = schedule_callback

        self._cwd = os.getcwd()
        self._is_first_command = True
        self._is_logged_in = False
        self._auth_state_callback = None

    @property
    def working_directory(self) -> str:
        """Get the current working directory."""
        return self._cwd

    @property
    def is_executing(self) -> bool:
        """Check if a command is currently executing."""
        return self._executor.is_executing

    @property
    def is_logged_in(self) -> bool:
        """Check if user is logged in to kiro-cli."""
        return self._is_logged_in

    @property
    def auth_button_enabled(self) -> bool:
        """Check if auth button should be enabled."""
        return not self._executor.is_executing

    def execute_command(self, command_text: str) -> None:
        """Execute a command."""
        if not command_text.strip():
            self._prompt()
            return

        self.history.add(command_text)

        command = Command(
            text=command_text,
            is_first=self._is_first_command,
            working_directory=self._cwd
        )

        if self._builtin_handler.is_builtin(command):
            result = self._builtin_handler.execute(
                command,
                clear_terminal_callback=self._handle_clear_command
            )
            self._handle_builtin_result(result)

            if command_text.strip().startswith("cd ") and result.success:
                self._cwd = os.getcwd()

            return

        self._is_first_command = False
        self._animation_start()
        self._executor.execute_chat(command, self._handle_external_result)

    def _handle_clear_command(self) -> None:
        """Handle the clear command."""
        self._clear()
        self._output(f"Working Directory: {self._cwd}\n")
        self._output("=" * 60 + "\n\n")
        self._prompt()

    def _handle_builtin_result(self, result: CommandResult) -> None:
        """Handle built-in command result."""
        if result.stdout:
            self._output(result.stdout)
        if result.stderr:
            self._output(result.stderr)
        if result.error_message:
            self._output(f"Error: {result.error_message}\n")

        self._prompt()

    def _handle_external_result(self, result: CommandResult) -> None:
        """Handle external command result."""
        def update_ui():
            self._animation_stop()

            if result.stdout:
                self._output("\n")
                self._output(result.stdout)
            if result.stderr:
                self._output("\n")
                self._output(result.stderr)
            if result.error_message:
                self._output(f"\nError: {result.error_message}\n")
            elif result.return_code != 0 and not result.stderr and not result.stdout:
                self._output(f"\nCommand exited with code {result.return_code}\n")

            self._prompt()

        self._schedule(update_ui)

    def reset(self) -> None:
        """Reset the terminal state."""
        self._is_first_command = True
        self._animation_stop()

    def get_previous_command(self) -> Optional[str]:
        """Get the previous command from history."""
        return self.history.get_previous()

    def get_next_command(self) -> Optional[str]:
        """Get the next command from history."""
        return self.history.get_next()

    def set_auth_state_callback(self, callback: Callable[[bool], None]) -> None:
        """Set callback for authentication state changes."""
        self._auth_state_callback = callback


    def login(self) -> None:
        """Execute kiro-cli login command."""
        def handle_result(result: CommandResult):
            # After login attempt, update state
            # If no error, login was successful or already logged in
            is_logged_in = "error" not in result.stdout.lower() and "error" not in result.stderr.lower()
            self._is_logged_in = is_logged_in
            if self._auth_state_callback:
                self._auth_state_callback(is_logged_in)

        # REMOVE when the bug for kiro-cli is fixed for this version of linux.
        # Kiro fails the login process when "kiro-cli login" opens a new browser window.
        # Therefore open a new window beforehand and wait for it to complete.
        webbrowser.open("https://www.google.com")

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
