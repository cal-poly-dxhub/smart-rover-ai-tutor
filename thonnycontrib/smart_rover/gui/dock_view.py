"""Main dock view for the Kiro plugin."""

from tkinter import ttk
from typing import Union
from thonnycontrib.smart_rover.gui.terminal_widget import TerminalWidget
from thonnycontrib.smart_rover.console.terminal_controller import TerminalController
from thonnycontrib.smart_rover.config.settings import UIConfig


class KiroDockView(ttk.Frame):
    """Kiro Interactive CLI for Thonny."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._setup_ui()
        self._initialize_controller()
        self._show_welcome_message()

    def _setup_ui(self):
        """Setup the UI components."""
        # Header
        header = ttk.Label(
            self,
            text=UIConfig.HEADER_TEXT,
            font=UIConfig.HEADER_FONT
        )
        header.pack(
            anchor="w",
            padx=UIConfig.HEADER_PADDING_X,
            pady=UIConfig.HEADER_PADDING_Y
        )

        # Button frame for reset and auth buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(
            side="bottom",
            fill="x",
            padx=UIConfig.BUTTON_PADDING_X,
            pady=UIConfig.BUTTON_PADDING_Y
        )

        # Authentication button
        self.auth_button = ttk.Button(
            button_frame,
            text="Login",
            command=self._on_auth_button_clicked,
            state="disabled"  # Disabled until initial check completes
        )
        self.auth_button.pack(side="left")

        # Reset button
        reset_button = ttk.Button(
            button_frame,
            text="Reset",
            command=self._reset_conversation
        )
        reset_button.pack(side="right")

        # Terminal widget
        terminal_frame = ttk.Frame(self)
        terminal_frame.pack(
            side="top",
            fill="both",
            expand=True,
            padx=UIConfig.TERMINAL_PADDING_X,
            pady=UIConfig.TERMINAL_PADDING_Y
        )

        self.terminal_widget = TerminalWidget(
            terminal_frame,
            on_command_callback=self._on_command_entered,
            on_history_up_callback=self._on_history_up,
            on_history_down_callback=self._on_history_down,
            is_executing_callback=lambda: self.controller.is_executing if self.controller else False
        )
        self.terminal_widget.pack(fill="both", expand=True)

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

    def _show_welcome_message(self):
        """Display the welcome message."""
        self.terminal_widget.write_output("Kiro Interactive CLI\n")
        self.terminal_widget.write_output(f"Working Directory: {self.controller.working_directory}\n")
        self.terminal_widget.write_output(UIConfig.SEPARATOR_LINE + "\n\n")
        self.terminal_widget.show_prompt()

        # Check authentication status and update button
        self._check_initial_auth_state()

    def _on_command_entered(self, command: str):
        """Handle command entered by user."""
        self.controller.execute_command(command)

    def _on_history_up(self):
        """Handle up arrow for history navigation."""
        return self.controller.get_previous_command()

    def _on_history_down(self):
        """Handle down arrow for history navigation."""
        return self.controller.get_next_command()

    def _reset_conversation(self):
        """Reset the conversation and clear the terminal."""
        self.controller.reset()
        self.terminal_widget.clear()
        self._show_welcome_message()

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

    def _update_auth_button_state(self, enabled: bool, is_logged_in: Union[bool, None] = None):
        """Update auth button text and enabled state."""
        if is_logged_in is not None:
            button_text = "Logout" if is_logged_in else "Login"
            self.auth_button.config(text=button_text)

        button_state = "normal" if enabled else "disabled"
        self.auth_button.config(state=button_state)

    def _check_initial_auth_state(self):
        """Check initial authentication state and update button."""
        def handle_initial_state(is_logged_in: bool):
            self._update_auth_button_state(enabled=True, is_logged_in=is_logged_in)

        self.controller.check_login_status(handle_initial_state)
