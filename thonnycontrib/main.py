# thonnycontrib/my_dock.py
import tkinter as tk
from tkinter import ttk
import subprocess
import os
import threading

from thonny import get_workbench
from thonnycontrib.ansi_handler import AnsiColorHandler
from thonnycontrib.loading_animation import LoadingAnimation


class MyDockView(ttk.Frame):
    """
    Kiro Interactive CLI for Thonny.

    Provides a terminal-like interface to interact with the kiro-cli tool
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Store current working directory and command history
        self.cwd = os.getcwd()
        self.command_history = []
        self.history_index = -1
        self.is_first_kiro_command = True
        self.is_executing = False

        # Header
        header = ttk.Label(self, text="Kiro", font=("TkDefaultFont", 11, "bold"))
        header.pack(anchor="w", padx=10, pady=(10, 6))

        # Reset button at the bottom (pack first to ensure it's always visible)
        button_frame = ttk.Frame(self)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        
        reset_button = ttk.Button(button_frame, text="Reset", command=self._reset_conversation)
        reset_button.pack(side="right")

        # Terminal frame
        terminal_frame = ttk.Frame(self)
        terminal_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        # Configure scrollbar style for better visibility against dark background
        style = ttk.Style()
        # Use a style that works with dark backgrounds
        # Try to configure the scrollbar with lighter colors
        try:
            # Create a custom style for this scrollbar
            style.configure("Kiro.Vertical.TScrollbar",
                           troughcolor="#2b2b2b",  # Dark gray trough
                           background="#5a5a5a",    # Medium gray thumb
                           bordercolor="#3a3a3a",   # Slightly lighter border
                           arrowcolor="#ffffff")    # White arrows
            style.map("Kiro.Vertical.TScrollbar",
                     background=[("active", "#7a7a7a")])  # Lighter on hover
        except:
            # If styling fails, continue with default
            pass

        # Scrollbar (pack BEFORE terminal to ensure it gets space)
        self.scrollbar = ttk.Scrollbar(terminal_frame, orient="vertical", style="Kiro.Vertical.TScrollbar")
        self.scrollbar.pack(side="right", fill="y")

        # Terminal display/input
        self.terminal = tk.Text(terminal_frame, wrap="word",
                               bg="black", fg="white", font=("Consolas", 10),
                               insertbackground="white",
                               yscrollcommand=self.scrollbar.set,
                               height=20,  # Set explicit height to ensure scrollbar shows
                               relief="flat",  # Remove border for cleaner look
                               borderwidth=0)
        self.terminal.pack(side="left", fill="both", expand=True)

        # Link scrollbar to terminal
        self.scrollbar.config(command=self.terminal.yview)

        # Initialize ANSI color handler
        self.ansi_handler = AnsiColorHandler(self.terminal)

        # Initialize loading animation
        self.loading_animation = LoadingAnimation(
            self.terminal,
            self._write_output,
            self._get_prompt_symbol
        )

        # Bind key events
        self.terminal.bind("<Return>", self._on_enter_key)
        self.terminal.bind("<Up>", self._on_up_key)
        self.terminal.bind("<Down>", self._on_down_key)
        self.terminal.bind("<KeyPress>", self._on_key_press)
        
        # Display welcome message and first prompt
        self._write_output(f"Kiro Interactive CLI\n")
        self._write_output(f"Working Directory: {self.cwd}\n")
        self._write_output("=" * 60 + "\n\n")
        self._show_prompt()
    
    def _get_prompt_symbol(self):
        """Get the appropriate prompt symbol."""
        # Return purple arrow using ANSI color code
        # Color 141 is purple (#af87ff), \x1B[0m resets formatting
        return "\x1B[38;5;141m>\x1B[0m "

    def _show_prompt(self):
        """Display a new command prompt."""
        prompt = self._get_prompt_symbol()
        self.terminal.mark_set("prompt_start", "end-1c")
        self._write_output(prompt)
        self.terminal.mark_set("prompt_end", "end-1c")
        self.terminal.mark_gravity("prompt_start", "left")
        self.terminal.mark_gravity("prompt_end", "left")
        self.terminal.see("end")
        self.terminal.focus_set()
    
    def _write_output(self, text):
        """Write text to the terminal, interpreting ANSI color codes."""
        self.ansi_handler.write_text(text)
        self.terminal.see("end")
    
    def _reset_conversation(self):
        """Reset the conversation and clear the terminal."""
        # Stop any running animation and unblock input
        self.loading_animation.stop()
        self.is_executing = False
        
        self.is_first_kiro_command = True
        self.terminal.delete("1.0", "end")
        self._write_output(f"Kiro Interactive CLI\n")
        self._write_output(f"Working Directory: {self.cwd}\n")
        self._write_output("=" * 60 + "\n\n")
        self._show_prompt()
    
    def _get_current_command(self):
        """Get the command text from the current prompt line."""
        try:
            return self.terminal.get("prompt_end", "end-1c")
        except:
            return ""
    
    def _clear_current_command(self):
        """Clear the current command input."""
        try:
            self.terminal.delete("prompt_end", "end")
        except:
            pass
    
    def _on_key_press(self, event):
        """Prevent editing of output (only allow editing after prompt)."""
        # Block all input while executing command
        if self.is_executing:
            return "break"
        
        # Allow navigation keys
        if event.keysym in ["Up", "Down", "Left", "Right", "Home", "End", "Control_L", "Control_R"]:
            return None
        
        # Get current cursor position
        insert_pos = self.terminal.index("insert")
        
        # Check if cursor is before the prompt
        try:
            prompt_end_pos = self.terminal.index("prompt_end")
            
            # Handle backspace - prevent deleting the prompt
            if event.keysym == "BackSpace":
                if self.terminal.compare(insert_pos, "<=", prompt_end_pos):
                    return "break"
                return None
            
            # Handle delete key
            if event.keysym == "Delete":
                return None
            
            # For regular characters, move cursor to end if before prompt
            if self.terminal.compare(insert_pos, "<", prompt_end_pos):
                if event.char and event.char.isprintable():
                    self.terminal.mark_set("insert", "end")
                    return None
                return "break"
        except:
            pass
        
        return None

    def _on_enter_key(self, event):
        """Handle Enter key press to execute command."""
        # Block if already executing
        if self.is_executing:
            return "break"
        
        # Get the command
        command = self._get_current_command().strip()
        
        # Move to new line
        self._write_output("\n")
        
        if command:
            # Add to history
            self.command_history.append(command)
            self.history_index = len(self.command_history)
            
            # Execute command
            self._execute_command(command)
        else:
            # Show new prompt for empty command
            self._show_prompt()
        
        return "break"
    
    def _on_up_key(self, event):
        """Navigate to previous command in history."""
        if self.is_executing:
            return "break"
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self._clear_current_command()
            self._write_output(self.command_history[self.history_index])
        return "break"
    
    def _on_down_key(self, event):
        """Navigate to next command in history."""
        if self.is_executing:
            return "break"
        if self.command_history:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self._clear_current_command()
                self._write_output(self.command_history[self.history_index])
            elif self.history_index == len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self._clear_current_command()
        return "break"

    
    def _execute_command(self, command):
        """Execute a command and display the output."""
        try:
            # Handle cd command specially to change working directory
            if command.startswith("cd "):
                new_dir = command[3:].strip()
                try:
                    if new_dir.startswith("~"):
                        new_dir = os.path.expanduser(new_dir)
                    
                    if not os.path.isabs(new_dir):
                        new_dir = os.path.join(self.cwd, new_dir)
                    new_dir = os.path.normpath(new_dir)
                    
                    if os.path.isdir(new_dir):
                        self.cwd = new_dir
                        os.chdir(self.cwd)
                    else:
                        self._write_output(f"Error: Directory not found: {new_dir}\n")
                except Exception as e:
                    self._write_output(f"Error changing directory: {str(e)}\n")
                self._show_prompt()
                return
            
            # Handle clear command
            if command.lower() == "clear":
                self.terminal.delete("1.0", "end")
                self._write_output("Kiro Interactive CLI\n")
                self._write_output(f"Working Directory: {self.cwd}\n")
                self._write_output("=" * 60 + "\n\n")
                self._show_prompt()
                return
            
            # Wrap user input with kiro-cli command
            if self.is_first_kiro_command:
                kiro_command = f'kiro-cli chat --no-interactive "{command}"'
                self.is_first_kiro_command = False
            else:
                kiro_command = f'kiro-cli chat --no-interactive --resume "{command}"'
            
            # Start loading animation and block input
            self.is_executing = True
            self.loading_animation.start()
            
            # Execute kiro-cli command in a separate thread
            def run_command():
                try:
                    result = subprocess.run(
                        kiro_command,
                        shell=True,
                        executable="/bin/bash",
                        capture_output=True,
                        text=True,
                        cwd=self.cwd,
                        timeout=30
                    )
                    # If reset button was pressed during execution, skip output
                    if self.is_first_kiro_command and not self.is_executing:
                        return
                    # Schedule UI updates on main thread
                    self.terminal.after(0, lambda: self._handle_command_result(result))
                except subprocess.TimeoutExpired:
                    self.terminal.after(0, lambda: self._handle_command_timeout())
                except Exception as e:
                    self.terminal.after(0, lambda: self._handle_command_error(e))
            
            threading.Thread(target=run_command, daemon=True).start()
                
        except Exception as e:
            self.loading_animation.stop()
            self._write_output(f"Error executing command: {str(e)}\n")
            self._show_prompt()
    
    def _handle_command_result(self, result):
        """Handle the result of a command execution."""
        # Stop loading animation and re-enable input
        self.is_executing = False
        self.loading_animation.stop()
        
        # Display output with line break before AI response
        if result.stdout:
            self._write_output("\n")
            self._write_output(result.stdout)
        if result.stderr:
            self._write_output("\n")
            self._write_output(result.stderr)
        if result.returncode != 0 and not result.stderr and not result.stdout:
            self._write_output(f"\nCommand exited with code {result.returncode}\n")
        
        self._show_prompt()
    
    def _handle_command_timeout(self):
        """Handle command timeout."""
        self.is_executing = False
        self.loading_animation.stop()
        self._write_output("Error: Command timed out (30 seconds)\n")
        self._show_prompt()
    
    def _handle_command_error(self, error):
        """Handle command execution error."""
        self.is_executing = False
        self.loading_animation.stop()
        self._write_output(f"Error executing command: {str(error)}\n")
        self._show_prompt()


def load_plugin():
    """
    Called by Thonny at startup for each discovered plugin module.
    """
    wb = get_workbench()

    # Register a dockable view. Signature (per Thonny docs/indices):
    # add_view(self, view_class, title, location, visible_by_default=False, default_position_key=None, **view_args)
    wb.add_view(
        MyDockView,
        "Kiro",
        "se",
        visible_by_default=True,
    )
