# Object-Oriented Refactoring Implementation Plan

## Overview

Refactor the Smart Rover AI Tutor Thonny plugin to follow object-oriented design principles with proper separation of concerns. The current monolithic `MyDockView` class (341 lines) handles GUI, command execution, terminal I/O, and state management. This refactoring will split responsibilities into focused classes organized in logical folders: `gui/`, `console/`, `models/`, `utils/`, and `config/`.

## Current State Analysis

**Existing Structure:**
```
thonnycontrib/
├── main.py (341 lines)           # Monolithic: GUI + commands + terminal I/O
├── ansi_handler.py (151 lines)   # ANSI color processing
└── loading_animation.py (93 lines) # Loading animation
```

**Problems:**
1. **Violation of Single Responsibility Principle**: `MyDockView` handles 7+ different concerns
2. **Tight Coupling**: Command execution directly manipulates GUI widgets
3. **No Abstraction**: Terminal display logic mixed with business logic
4. **Limited Extensibility**: Cannot add new commands without modifying GUI class
5. **Hardcoded Configuration**: Colors, fonts, timeouts embedded in code

**Key Discoveries:**
- Plugin entry point: `thonnycontrib/main.py:327-341` (`load_plugin()` function)
- Main GUI class: `MyDockView` extends `ttk.Frame` (thonnycontrib/main.py:13-325)
- Command execution: `_execute_command()` at main.py:221-293
- Built-in commands: `cd` and `clear` hardcoded in execution logic
- Threading model: Separate thread for subprocess execution with UI updates via `terminal.after()`

## Desired End State

**Target Structure:**
```
thonnycontrib/
├── __init__.py
├── main.py                        # Plugin entry point only (~30 lines)
├── gui/
│   ├── __init__.py
│   ├── dock_view.py              # Main container, delegates to terminal widget
│   └── terminal_widget.py        # Terminal display and input handling
├── console/
│   ├── __init__.py
│   ├── command_executor.py       # Subprocess execution with threading
│   ├── command_history.py        # History management (up/down navigation)
│   ├── builtin_commands.py       # cd, clear, and extensible command registry
│   └── terminal_controller.py    # Coordinates terminal operations
├── models/
│   ├── __init__.py
│   └── command.py                # Command data model
├── utils/
│   ├── __init__.py
│   ├── ansi_handler.py          # ANSI color processing (moved from root)
│   └── loading_animation.py      # Loading animation (moved from root)
└── config/
    ├── __init__.py
    └── settings.py               # Configuration constants
```

**Verification:**
- All functionality works identically to before
- Plugin loads in Thonny without errors
- Terminal interaction (input, output, colors) works correctly
- Commands execute with proper threading
- History navigation (up/down arrows) functions
- cd and clear commands work
- Reset button clears terminal

## What We're NOT Doing

- Not adding new features (keeping exact same functionality)
- Not changing the user interface or visual appearance
- Not implementing full MVC pattern (avoiding over-engineering)
- Not adding external configuration files (keeping config in code for simplicity)
- Not adding unit tests (can be done in future iteration)
- Not modifying the external `kiro-cli` tool integration
- Not changing Thonny plugin registration mechanism

## Implementation Approach

Use **incremental refactoring** to minimize risk:
1. Create new structure alongside existing code
2. Extract one responsibility at a time
3. Test after each phase
4. Keep backward compatibility throughout

**Design Patterns:**
- **Composition**: GUI composes console components
- **Delegation**: Clear responsibility delegation between layers
- **Dependency Injection**: Pass dependencies to constructors
- **Strategy Pattern**: Pluggable command handlers

## Phase 1: Setup Infrastructure

### Overview
Create folder structure, configuration module, and move utility files. This establishes the foundation for separation.

### Changes Required:

#### 1. Create Directory Structure
**Action**: Create new directories for organized structure

```bash
mkdir thonnycontrib/gui
mkdir thonnycontrib/console
mkdir thonnycontrib/models
mkdir thonnycontrib/utils
mkdir thonnycontrib/config
```

#### 2. Create Configuration Module
**File**: `thonnycontrib/config/__init__.py`
**Changes**: Create empty file for package initialization

```python
"""Configuration for the Kiro plugin."""
```

**File**: `thonnycontrib/config/settings.py`
**Changes**: Extract hardcoded configuration values

```python
"""Configuration settings for the Kiro plugin."""

class TerminalConfig:
    """Terminal widget configuration."""
    FONT = ("Consolas", 10)
    BG_COLOR = "black"
    FG_COLOR = "white"
    INSERT_BG_COLOR = "white"
    HEIGHT = 20
    WRAP = "word"
    RELIEF = "flat"
    BORDER_WIDTH = 0


class AnimationConfig:
    """Loading animation configuration."""
    FRAME_DELAY_MS = 500
    MAX_DOTS = 3


class ExecutionConfig:
    """Command execution configuration."""
    TIMEOUT_SECONDS = 30
    SHELL = "/bin/bash"
    SHELL_EXECUTABLE = "/bin/bash"


class UIConfig:
    """UI element configuration."""
    HEADER_TEXT = "Kiro"
    HEADER_FONT = ("TkDefaultFont", 11, "bold")
    HEADER_PADDING_X = 10
    HEADER_PADDING_Y = (10, 6)
    BUTTON_PADDING_X = 10
    BUTTON_PADDING_Y = (0, 10)
    TERMINAL_PADDING_X = 10
    TERMINAL_PADDING_Y = (0, 10)
    SEPARATOR_LINE = "=" * 60


class AnsiColorConfig:
    """ANSI color palette configuration."""
    # Standard 16 colors
    STANDARD_COLORS = {
        0: "#000000", 1: "#800000", 2: "#008000", 3: "#808000",
        4: "#000080", 5: "#800080", 6: "#008080", 7: "#c0c0c0",
        8: "#808080", 9: "#ff0000", 10: "#00ff00", 11: "#ffff00",
        12: "#0000ff", 13: "#ff00ff", 14: "#00ffff", 15: "#ffffff",
    }

    # Extended colors
    EXTENDED_COLORS = {
        141: "#af87ff",  # Purple/magenta (used for prompt)
        244: "#808080",  # Gray
        252: "#d0d0d0",  # Light gray
    }

    PROMPT_COLOR_CODE = 141
```

#### 3. Move Utility Files
**File**: `thonnycontrib/utils/__init__.py`
**Changes**: Create package initialization file

```python
"""Utility components for the Kiro plugin."""
```

**File**: `thonnycontrib/utils/ansi_handler.py`
**Changes**: Copy from `thonnycontrib/ansi_handler.py` and update imports

```python
"""ANSI color code handler for terminal display."""

import re
from thonnycontrib.config.settings import AnsiColorConfig


class AnsiColorHandler:
    """Handles ANSI color codes and formatting for terminal display."""

    def __init__(self, text_widget):
        """
        Initialize the ANSI color handler.

        Args:
            text_widget: tkinter Text widget to apply formatting to
        """
        self.text_widget = text_widget
        self.ansi_colors = self._create_color_palette()
        self._setup_color_tags()

    def _create_color_palette(self):
        """Create the ANSI 256-color palette from configuration."""
        colors = {}
        colors.update(AnsiColorConfig.STANDARD_COLORS)
        colors.update(AnsiColorConfig.EXTENDED_COLORS)
        return colors

    def _setup_color_tags(self):
        """Setup text tags for ANSI colors in the text widget."""
        for code, color in self.ansi_colors.items():
            self.text_widget.tag_config(f"fg{code}", foreground=color)
            self.text_widget.tag_config(f"bg{code}", background=color)

    def write_text(self, text):
        """
        Write text to the widget, interpreting ANSI color codes.

        Args:
            text: Text with ANSI escape sequences
        """
        # Pattern to match ANSI color escape sequences
        ansi_pattern = re.compile(r'\x1B\[([0-9;]+)m')

        # Track current formatting state
        current_fg = None
        current_bg = None

        last_end = 0
        for match in ansi_pattern.finditer(text):
            # Write any text before this escape code
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                plain_text = self._clean_control_codes(plain_text)

                if plain_text:
                    self._insert_text(plain_text, current_fg, current_bg)

            # Parse and update formatting state
            current_fg, current_bg = self._parse_ansi_code(
                match.group(1), current_fg, current_bg
            )

            last_end = match.end()

        # Write remaining text after last escape code
        if last_end < len(text):
            plain_text = text[last_end:]
            plain_text = self._clean_control_codes(plain_text)

            if plain_text:
                self._insert_text(plain_text, current_fg, current_bg)

    def _clean_control_codes(self, text):
        """Remove cursor control codes but keep printable characters."""
        # Remove cursor movement and control sequences (but not color codes)
        text = re.sub(r'\x1B\[[^m]*[A-Za-z]', '', text)
        # Remove other control characters except newline, tab, carriage return
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        return text

    def _parse_ansi_code(self, code_str, current_fg, current_bg):
        """
        Parse ANSI color code and return updated foreground/background colors.

        Args:
            code_str: String containing semicolon-separated ANSI codes
            current_fg: Current foreground color code
            current_bg: Current background color code

        Returns:
            Tuple of (new_fg, new_bg)
        """
        codes = code_str.split(';')
        i = 0

        while i < len(codes):
            code = codes[i]

            if code == '0':  # Reset all formatting
                current_fg = None
                current_bg = None
            elif code == '38' and i + 2 < len(codes) and codes[i + 1] == '5':
                # 256-color foreground: ESC[38;5;Nm
                current_fg = int(codes[i + 2])
                i += 2
            elif code == '48' and i + 2 < len(codes) and codes[i + 1] == '5':
                # 256-color background: ESC[48;5;Nm
                current_bg = int(codes[i + 2])
                i += 2
            elif code.isdigit():
                code_int = int(code)
                if 30 <= code_int <= 37:  # Standard foreground color
                    current_fg = code_int - 30
                elif 40 <= code_int <= 47:  # Standard background color
                    current_bg = code_int - 40
                elif 90 <= code_int <= 97:  # Bright foreground color
                    current_fg = code_int - 90 + 8
                elif 100 <= code_int <= 107:  # Bright background color
                    current_bg = code_int - 100 + 8

            i += 1

        return current_fg, current_bg

    def _insert_text(self, text, fg_color, bg_color):
        """
        Insert text with specified colors.

        Args:
            text: Text to insert
            fg_color: Foreground color code (or None)
            bg_color: Background color code (or None)
        """
        tags = []
        if fg_color is not None and fg_color in self.ansi_colors:
            tags.append(f"fg{fg_color}")
        if bg_color is not None and bg_color in self.ansi_colors:
            tags.append(f"bg{bg_color}")

        if tags:
            self.text_widget.insert("end", text, tuple(tags))
        else:
            self.text_widget.insert("end", text)
```

**File**: `thonnycontrib/utils/loading_animation.py`
**Changes**: Copy from `thonnycontrib/loading_animation.py` and update imports

```python
"""Loading animation for displaying while waiting for AI response."""

from thonnycontrib.config.settings import AnimationConfig


class LoadingAnimation:
    """
    Manages a loading animation that cycles through dots: ".", "..", "..."
    with a colored arrow prefix.
    """

    def __init__(self, terminal_widget, write_callback, get_prompt_symbol_callback):
        """
        Initialize the loading animation.

        Args:
            terminal_widget: The tkinter Text widget used for terminal display
            write_callback: Callback function to write output to terminal
            get_prompt_symbol_callback: Callback to get the prompt symbol (arrow)
        """
        self.terminal = terminal_widget
        self.write_output = write_callback
        self.get_prompt_symbol = get_prompt_symbol_callback

        self.is_animating = False
        self.animation_id = None
        self.dot_count = 0
        self.animation_mark = None

    def start(self):
        """Start the loading animation."""
        if self.is_animating:
            return

        self.is_animating = True
        self.dot_count = 0

        # Write the arrow
        self.write_output("\n")
        arrow = self.get_prompt_symbol()
        self.write_output(arrow)

        # Mark the position where animation starts
        self.animation_mark = self.terminal.index("end-1c")

        # Start the animation loop
        self._animate()

    def _animate(self):
        """Internal method to handle animation frames."""
        if not self.is_animating:
            return

        # Cycle through 1, 2, 3 dots using configuration
        self.dot_count = (self.dot_count % AnimationConfig.MAX_DOTS) + 1
        dots = "." * self.dot_count

        # Clear previous dots and write new ones
        if self.animation_mark:
            try:
                self.terminal.delete(self.animation_mark, "end")
                self.write_output(dots)
            except:
                pass

        # Schedule next frame using configured delay
        self.animation_id = self.terminal.after(AnimationConfig.FRAME_DELAY_MS, self._animate)

    def stop(self):
        """Stop the loading animation and clean up."""
        if not self.is_animating:
            return

        self.is_animating = False

        # Cancel scheduled animation
        if self.animation_id:
            try:
                self.terminal.after_cancel(self.animation_id)
            except:
                pass
            self.animation_id = None

        # Clear the animation line
        if self.animation_mark:
            try:
                # Delete from the line start (including arrow) to end
                line_start = self.terminal.index(f"{self.animation_mark} linestart")
                self.terminal.delete(line_start, "end")
            except:
                pass
            self.animation_mark = None
```

#### 4. Delete Old Files
**Action**: Remove the old utility files from root

```bash
rm thonnycontrib/ansi_handler.py
rm thonnycontrib/loading_animation.py
```

### Success Criteria:

#### Automated Verification:
- [x] All new directories exist
- [x] Configuration imports: `python -c "from thonnycontrib.config.settings import TerminalConfig"`
- [x] Utils import: `python -c "from thonnycontrib.utils.ansi_handler import AnsiColorHandler"`
- [x] Utils import: `python -c "from thonnycontrib.utils.loading_animation import LoadingAnimation"`
- [x] Old files deleted

#### Manual Verification:
- [ ] Directory structure matches plan
- [ ] All __init__.py files created
- [ ] Configuration values match original code

**Implementation Note**: After completing this phase and all automated verification passes, proceed to Phase 2.

---

## Phase 2: Extract Models and History

### Overview
Create data models and command history management. This establishes clean abstractions for command data.

### Changes Required:

#### 1. Create Command Models
**File**: `thonnycontrib/models/__init__.py`
**Changes**: Create package file

```python
"""Data models for the Kiro plugin."""
```

**File**: `thonnycontrib/models/command.py`
**Changes**: Define Command and CommandResult models

```python
"""Command data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Command:
    """Represents a command to be executed."""

    text: str
    """The command text as entered by the user."""

    is_first: bool = False
    """Whether this is the first command in a conversation."""

    working_directory: str = ""
    """The working directory where the command should execute."""

    def __str__(self):
        return self.text


@dataclass
class CommandResult:
    """Represents the result of a command execution."""

    stdout: str = ""
    """Standard output from the command."""

    stderr: str = ""
    """Standard error from the command."""

    return_code: int = 0
    """The command's exit code."""

    success: bool = True
    """Whether the command executed successfully."""

    error_message: Optional[str] = None
    """Error message if execution failed."""
```

#### 2. Create Command History
**File**: `thonnycontrib/console/__init__.py`
**Changes**: Create package file

```python
"""Console components for command execution and terminal control."""
```

**File**: `thonnycontrib/console/command_history.py`
**Changes**: Extract history management

```python
"""Command history management for terminal."""

from typing import List, Optional


class CommandHistory:
    """Manages command history with navigation support."""

    def __init__(self):
        """Initialize command history."""
        self._history: List[str] = []
        self._index: int = -1

    def add(self, command: str) -> None:
        """
        Add a command to history.

        Args:
            command: The command text to add
        """
        if command:  # Only add non-empty commands
            self._history.append(command)
            self._index = len(self._history)

    def get_previous(self) -> Optional[str]:
        """
        Get the previous command in history.

        Returns:
            The previous command, or None if at the beginning
        """
        if self._history and self._index > 0:
            self._index -= 1
            return self._history[self._index]
        return None

    def get_next(self) -> Optional[str]:
        """
        Get the next command in history.

        Returns:
            The next command, or None if at the end
        """
        if self._history:
            if self._index < len(self._history) - 1:
                self._index += 1
                return self._history[self._index]
            elif self._index == len(self._history) - 1:
                self._index = len(self._history)
        return None

    def is_at_end(self) -> bool:
        """Check if at the end of history."""
        return self._index >= len(self._history)

    def reset_index(self) -> None:
        """Reset the history index to the end."""
        self._index = len(self._history)

    def clear(self) -> None:
        """Clear all history."""
        self._history.clear()
        self._index = -1

    def __len__(self) -> int:
        """Return the number of commands in history."""
        return len(self._history)
```

### Success Criteria:

#### Automated Verification:
- [x] Models import: `python -c "from thonnycontrib.models.command import Command, CommandResult"`
- [x] History imports: `python -c "from thonnycontrib.console.command_history import CommandHistory"`
- [x] No syntax errors

#### Manual Verification:
- [ ] Command model has correct fields
- [ ] CommandHistory manages state properly

**Implementation Note**: After completing this phase, proceed to Phase 3.

---

## Phase 3: Extract Console Logic

### Overview
Extract command execution, built-in commands, and terminal controller.

### Changes Required:

#### 1. Create Built-in Commands
**File**: `thonnycontrib/console/builtin_commands.py`
**Changes**: Extract cd and clear logic

```python
"""Built-in command handlers for the terminal."""

import os
from typing import Optional, Callable
from thonnycontrib.models.command import Command, CommandResult


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
```

#### 2. Create Command Executor
**File**: `thonnycontrib/console/command_executor.py`
**Changes**: Extract subprocess execution

```python
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
```

#### 3. Create Terminal Controller
**File**: `thonnycontrib/console/terminal_controller.py`
**Changes**: Coordinate terminal operations

```python
"""Terminal controller coordinating console operations."""

import os
from typing import Callable, Optional
from thonnycontrib.models.command import Command, CommandResult
from thonnycontrib.console.command_executor import CommandExecutor
from thonnycontrib.console.command_history import CommandHistory
from thonnycontrib.console.builtin_commands import BuiltinCommandHandler


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

    @property
    def working_directory(self) -> str:
        """Get the current working directory."""
        return self._cwd

    @property
    def is_executing(self) -> bool:
        """Check if a command is currently executing."""
        return self._executor.is_executing

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
        self._executor.execute(command, self._handle_external_result)

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
```

### Success Criteria:

#### Automated Verification:
- [x] All console modules import
- [x] No syntax errors in console layer

#### Manual Verification:
- [ ] Console layer has no GUI dependencies
- [ ] Logic properly separated

**Implementation Note**: Proceed to Phase 4 after verification.

---

## Phase 4: Refactor GUI Layer

### Overview
Create terminal widget and simplified dock view that delegate to console layer.

### Changes Required:

#### 1. Create GUI Package
**File**: `thonnycontrib/gui/__init__.py`
**Changes**: Create package file

```python
"""GUI components for the Kiro plugin."""
```

#### 2. Create Terminal Widget
**File**: `thonnycontrib/gui/terminal_widget.py`
**Changes**: Extract terminal display and input

```python
"""Terminal widget for text display and input handling."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from thonnycontrib.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.utils.loading_animation import LoadingAnimation
from thonnycontrib.config.settings import TerminalConfig, AnsiColorConfig


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
```

#### 3. Create Dock View
**File**: `thonnycontrib/gui/dock_view.py`
**Changes**: Simplified GUI container

```python
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
```

#### 4. Update Main Plugin
**File**: `thonnycontrib/main.py`
**Changes**: Simplify to plugin registration only

```python
"""Kiro plugin for Thonny IDE."""

from thonny import get_workbench
from thonnycontrib.gui.dock_view import KiroDockView


def load_plugin():
    """
    Called by Thonny at startup.
    Registers the Kiro dockable view with Thonny workbench.
    """
    wb = get_workbench()
    wb.add_view(
        KiroDockView,
        "Kiro",
        "se",
        visible_by_default=True,
    )
```

### Success Criteria:

#### Automated Verification:
- [x] GUI modules import successfully
- [x] No syntax errors
- [x] Main module imports

#### Manual Verification:
- [ ] Plugin loads in Thonny
- [ ] Terminal displays correctly
- [ ] Command input works
- [ ] Loading animation appears
- [ ] Command output displays with colors
- [ ] History navigation works
- [ ] Built-in commands work (cd, clear)
- [ ] Reset button works
- [ ] Scrollbar functions
- [ ] No visual regressions

**Implementation Note**: This is the critical integration phase. Test thoroughly before proceeding.

---

## Phase 5: Cleanup and Package Exports

### Overview
Add package exports and perform final verification.

### Changes Required:

#### 1. Update Package Exports
**File**: `thonnycontrib/__init__.py`
**Changes**: Add version info

```python
"""Smart Rover AI Tutor plugin for Thonny."""

__version__ = "0.1.0"
```

**File**: `thonnycontrib/gui/__init__.py`
**Changes**: Export classes

```python
"""GUI components for the Kiro plugin."""

from thonnycontrib.gui.dock_view import KiroDockView
from thonnycontrib.gui.terminal_widget import TerminalWidget

__all__ = ["KiroDockView", "TerminalWidget"]
```

**File**: `thonnycontrib/console/__init__.py`
**Changes**: Export classes

```python
"""Console components for command execution and terminal control."""

from thonnycontrib.console.terminal_controller import TerminalController
from thonnycontrib.console.command_executor import CommandExecutor
from thonnycontrib.console.command_history import CommandHistory
from thonnycontrib.console.builtin_commands import BuiltinCommandHandler

__all__ = [
    "TerminalController",
    "CommandExecutor",
    "CommandHistory",
    "BuiltinCommandHandler"
]
```

**File**: `thonnycontrib/models/__init__.py`
**Changes**: Export models

```python
"""Data models for the Kiro plugin."""

from thonnycontrib.models.command import Command, CommandResult

__all__ = ["Command", "CommandResult"]
```

**File**: `thonnycontrib/utils/__init__.py`
**Changes**: Export utilities

```python
"""Utility components for the Kiro plugin."""

from thonnycontrib.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.utils.loading_animation import LoadingAnimation

__all__ = ["AnsiColorHandler", "LoadingAnimation"]
```

**File**: `thonnycontrib/config/__init__.py`
**Changes**: Export config

```python
"""Configuration for the Kiro plugin."""

from thonnycontrib.config.settings import (
    TerminalConfig,
    AnimationConfig,
    ExecutionConfig,
    UIConfig,
    AnsiColorConfig
)

__all__ = [
    "TerminalConfig",
    "AnimationConfig",
    "ExecutionConfig",
    "UIConfig",
    "AnsiColorConfig"
]
```

### Success Criteria:

#### Automated Verification:
- [x] All __init__.py files have exports
- [x] Package imports work
- [x] No syntax errors
- [x] Old files deleted

#### Manual Verification:
- [ ] Plugin loads in Thonny
- [ ] Welcome message displays
- [ ] Can type and submit commands
- [ ] Command output appears
- [ ] ANSI colors render
- [ ] Loading animation works
- [ ] History navigation works
- [ ] cd command works
- [ ] clear command works
- [ ] Reset button works
- [ ] Scrollbar works
- [ ] No visual differences
- [ ] No console errors
- [ ] kiro-cli integration works
- [ ] First command uses --no-interactive
- [ ] Subsequent commands use --resume
- [ ] 30-second timeout applies
- [ ] Error messages display
- [ ] Can interact after reset

**Implementation Note**: Final comprehensive testing phase. All functionality must work identically to the original.

---

## Testing Strategy

### Manual Testing Checklist

1. **Basic Functionality:**
   - [ ] Plugin loads in Thonny
   - [ ] Terminal displays correctly
   - [ ] Can execute commands
   - [ ] Responses appear correctly

2. **Command History:**
   - [ ] Execute multiple commands
   - [ ] Up arrow shows previous commands
   - [ ] Down arrow shows next commands
   - [ ] History navigation works correctly

3. **Built-in Commands:**
   - [ ] cd changes directory
   - [ ] cd with ~ expands home
   - [ ] cd to invalid directory shows error
   - [ ] clear clears terminal

4. **Reset:**
   - [ ] Reset button clears terminal
   - [ ] Reset resets conversation
   - [ ] Can continue after reset

5. **Visual:**
   - [ ] Colors render correctly
   - [ ] Font is correct
   - [ ] Scrollbar appears and works
   - [ ] Prompt symbol is purple
   - [ ] Animation displays during execution

## Migration Notes

**Fully backward compatible:**
- No changes to user interface
- No changes to command syntax
- No changes to plugin registration

**For developers:**
- `MyDockView` replaced by `KiroDockView`
- Imports use new package structure
- Configuration in `config.settings`

## References

- Original: `thonnycontrib/main.py` (341 lines)
- Thonny plugins: https://github.com/thonny/thonny/wiki/Plugins
