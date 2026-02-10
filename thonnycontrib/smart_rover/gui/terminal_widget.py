"""Terminal widget for text display and input handling."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from thonnycontrib.smart_rover.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.smart_rover.utils.loading_animation import LoadingAnimation
from thonnycontrib.smart_rover.config.settings import TerminalConfig, AnsiColorConfig


class TerminalWidget(ttk.Frame):
    """Terminal display widget with input handling."""

    def __init__(self, master,
                 on_command_callback: Callable[[str], None],
                 on_history_up_callback: Callable[[], Optional[str]],
                 on_history_down_callback: Callable[[], Optional[str]],
                 is_executing_callback: Callable[[], bool],
                 **kwargs):
        """Initialize the terminal widget."""
        super().__init__(master, **kwargs)

        self._on_command = on_command_callback
        self._on_history_up = on_history_up_callback
        self._on_history_down = on_history_down_callback
        self._is_executing = is_executing_callback

        self._setup_ui()
        self._setup_handlers()
        self._bind_events()

    def _setup_ui(self):
        """Setup the terminal UI components."""
        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        self.terminal = tk.Text(
            self,
            wrap=TerminalConfig.WRAP,
            bg=TerminalConfig.BG_COLOR,
            fg=TerminalConfig.FG_COLOR,
            font=TerminalConfig.FONT,
            insertbackground=TerminalConfig.INSERT_BG_COLOR,
            yscrollcommand=self.scrollbar.set,
            height=TerminalConfig.HEIGHT,
            relief=TerminalConfig.RELIEF,
            borderwidth=TerminalConfig.BORDER_WIDTH
        )
        self.terminal.pack(side="left", fill="both", expand=True)

        self.scrollbar.config(command=self.terminal.yview)

    def _setup_handlers(self):
        """Setup ANSI handler and loading animation."""
        self.ansi_handler = AnsiColorHandler(self.terminal)
        self.loading_animation = LoadingAnimation(
            self.terminal,
            self.write_output,
            self.get_prompt_symbol
        )

    def _bind_events(self):
        """Bind keyboard events."""
        self.terminal.bind("<Return>", self._on_enter_key)
        self.terminal.bind("<Up>", self._on_up_key)
        self.terminal.bind("<Down>", self._on_down_key)
        self.terminal.bind("<KeyPress>", self._on_key_press)

    def get_prompt_symbol(self) -> str:
        """Get the colored prompt symbol."""
        color_code = AnsiColorConfig.PROMPT_COLOR_CODE
        return f"\x1B[38;5;{color_code}m>\x1B[0m "

    def show_prompt(self):
        """Display a new command prompt."""
        prompt = self.get_prompt_symbol()
        self.terminal.mark_set("prompt_start", "end-1c")
        self.write_output(prompt)
        self.terminal.mark_set("prompt_end", "end-1c")
        self.terminal.mark_gravity("prompt_start", "left")
        self.terminal.mark_gravity("prompt_end", "left")
        self.terminal.see("end")
        self.terminal.focus_set()

    def write_output(self, text: str):
        """Write text to the terminal with ANSI color support."""
        self.ansi_handler.write_text(text)
        self.terminal.see("end")

    def clear(self):
        """Clear the terminal display."""
        self.terminal.delete("1.0", "end")

    def get_current_command(self) -> str:
        """Get the command text from the current prompt line."""
        try:
            return self.terminal.get("prompt_end", "end-1c")
        except:
            return ""

    def clear_current_command(self):
        """Clear the current command input."""
        try:
            self.terminal.delete("prompt_end", "end")
        except:
            pass

    def start_animation(self):
        """Start the loading animation."""
        self.loading_animation.start()

    def stop_animation(self):
        """Stop the loading animation."""
        self.loading_animation.stop()

    def schedule_callback(self, callback: Callable):
        """Schedule a callback on the main thread."""
        self.terminal.after(0, callback)

    def _on_key_press(self, event):
        """Prevent editing of output."""
        if self._is_executing():
            return "break"

        if event.keysym in ["Up", "Down", "Left", "Right", "Home", "End", "Control_L", "Control_R"]:
            return None

        insert_pos = self.terminal.index("insert")

        try:
            prompt_end_pos = self.terminal.index("prompt_end")

            if event.keysym == "BackSpace":
                if self.terminal.compare(insert_pos, "<=", prompt_end_pos):
                    return "break"
                return None

            if event.keysym == "Delete":
                return None

            if self.terminal.compare(insert_pos, "<", prompt_end_pos):
                if event.char and event.char.isprintable():
                    self.terminal.mark_set("insert", "end")
                    return None
                return "break"
        except:
            pass

        return None

    def _on_enter_key(self, event):
        """Handle Enter key press."""
        if self._is_executing():
            return "break"

        command = self.get_current_command().strip()
        self.write_output("\n")
        self._on_command(command)

        return "break"

    def _on_up_key(self, event):
        """Navigate to previous command."""
        if self._is_executing():
            return "break"

        prev_command = self._on_history_up()
        if prev_command is not None:
            self.clear_current_command()
            self.write_output(prev_command)

        return "break"

    def _on_down_key(self, event):
        """Navigate to next command."""
        if self._is_executing():
            return "break"

        next_command = self._on_history_down()
        if next_command is not None:
            self.clear_current_command()
            self.write_output(next_command)
        else:
            self.clear_current_command()

        return "break"
