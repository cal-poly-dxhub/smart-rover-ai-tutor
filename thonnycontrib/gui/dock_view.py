"""Main dock view for the Kiro plugin."""

from tkinter import ttk
from thonnycontrib.gui.terminal_widget import TerminalWidget
from thonnycontrib.console.terminal_controller import TerminalController
from thonnycontrib.config.settings import UIConfig


class KiroDockView(ttk.Frame):
    """Kiro Interactive CLI for Thonny."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.terminal_widget = None
        self.controller = None

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

        # Reset button
        button_frame = ttk.Frame(self)
        button_frame.pack(
            side="bottom",
            fill="x",
            padx=UIConfig.BUTTON_PADDING_X,
            pady=UIConfig.BUTTON_PADDING_Y
        )

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

    def _show_welcome_message(self):
        """Display the welcome message."""
        self.terminal_widget.write_output("Kiro Interactive CLI\n")
        self.terminal_widget.write_output(f"Working Directory: {self.controller.working_directory}\n")
        self.terminal_widget.write_output(UIConfig.SEPARATOR_LINE + "\n\n")
        self.terminal_widget.show_prompt()

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
