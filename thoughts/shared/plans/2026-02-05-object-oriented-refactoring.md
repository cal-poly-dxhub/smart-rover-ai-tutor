# Object-Oriented Codebase Refactoring Implementation Plan

## Overview

Refactor the Smart Rover AI Tutor Thonny plugin codebase to follow object-oriented principles with clear separation of concerns. This involves reorganizing code into dedicated folders (gui/, console/, models/, utils/, config/) and extracting responsibilities from the monolithic MyDockView class into focused, reusable components.

## Current State Analysis

The codebase currently consists of 3 files in a flat structure:
- `thonnycontrib/main.py` (341 lines) - Contains everything: GUI, command execution, terminal I/O, history management
- `thonnycontrib/ansi_handler.py` (151 lines) - ANSI color processing (already well-separated)
- `thonnycontrib/loading_animation.py` (93 lines) - Loading animation (already well-separated)

### Key Problems:
1. **MyDockView violates Single Responsibility Principle** - handles 6+ distinct responsibilities:
   - GUI layout and widget management
   - Command execution and subprocess management
   - Terminal I/O operations
   - Command history tracking
   - Working directory state
   - Animation coordination

2. **Tight coupling** between layers:
   - Command execution directly manipulates tkinter widgets
   - No abstraction between terminal display and command processing
   - Built-in commands (cd, clear) hardcoded in GUI class (main.py:224-252)

3. **Limited extensibility**:
   - Cannot add command types without modifying MyDockView
   - Configuration values hardcoded throughout
   - No dependency injection

### Key Discoveries:
- Plugin entry point: `load_plugin()` in main.py:327-341
- Main GUI class: `MyDockView(ttk.Frame)` in main.py:13-325
- Command execution: `_execute_command()` in main.py:221-293
- Terminal I/O: Direct tk.Text widget manipulation throughout
- Already well-separated utilities: AnsiColorHandler, LoadingAnimation

## Desired End State

A well-structured, object-oriented codebase with clear separation of concerns:

```
thonnycontrib/
├── main.py                    # Plugin entry point only (~30 lines)
├── gui/
│   ├── __init__.py
│   ├── dock_view.py          # GUI container, layout only (~120 lines)
│   └── terminal_widget.py    # Terminal display component (~100 lines)
├── console/
│   ├── __init__.py
│   ├── command_executor.py   # Command execution logic (~120 lines)
│   ├── command_history.py    # History management (~60 lines)
│   ├── builtin_commands.py   # cd, clear, etc. (~80 lines)
│   └── terminal_controller.py # Coordinates terminal ops (~150 lines)
├── models/
│   ├── __init__.py
│   └── command.py            # Command data model (~40 lines)
├── utils/
│   ├── __init__.py
│   ├── ansi_handler.py      # ANSI color processing (moved)
│   └── loading_animation.py  # Loading animation (moved)
└── config/
    ├── __init__.py
    └── settings.py           # Configuration constants (~40 lines)
```

### Architecture Principles:
- **Single Responsibility**: Each class has one clear purpose
- **Dependency Injection**: Components receive dependencies via constructors
- **Composition over Inheritance**: Use delegation patterns
- **Open/Closed**: Easy to extend with new command types
- **Clear Interfaces**: Well-defined boundaries between layers

### Verification:
- Plugin loads successfully in Thonny
- All existing functionality works identically
- Code is more maintainable and testable
- New commands can be added without modifying existing classes

## What We're NOT Doing

To prevent scope creep:
- ❌ **NOT changing user-facing functionality** - UI behavior stays identical
- ❌ **NOT adding new features** - pure refactoring only
- ❌ **NOT adding unit tests** (can be done in future phase)
- ❌ **NOT changing external dependencies** - still uses tkinter, thonny, subprocess
- ❌ **NOT implementing a plugin system** for custom commands (future enhancement)
- ❌ **NOT adding configuration file support** - constants in code for now
- ❌ **NOT changing error handling behavior** - preserve existing error messages
- ❌ **NOT optimizing performance** - focus is on structure, not speed

## Implementation Approach

### Strategy:
1. **Bottom-up refactoring** - Start with utilities and models, move up to GUI
2. **Incremental migration** - Create new structure alongside old code
3. **Preserve behavior** - Ensure identical user experience throughout
4. **Test continuously** - Manual testing after each phase

### Key Design Patterns:
- **Dependency Injection**: Pass dependencies to constructors
- **Delegation**: Forward calls to specialized components
- **Observer/Callback**: Use callbacks for async operations
- **Command Pattern**: Represent commands as objects

### Migration Order:
1. Create folder structure and config
2. Move utilities (ansi_handler, loading_animation)
3. Extract models (Command)
4. Build console layer (executor, history, builtin commands)
5. Build GUI layer (terminal widget, dock view)
6. Update main.py to use new structure
7. Cleanup and verification

---

## Phase 1: Project Structure Setup

### Overview
Create the new folder structure and configuration module. This establishes the foundation for all subsequent phases.

### Changes Required:

#### 1. Create Directory Structure
**Action**: Create new directories

```bash
mkdir -p thonnycontrib/gui
mkdir -p thonnycontrib/console
mkdir -p thonnycontrib/models
mkdir -p thonnycontrib/utils
mkdir -p thonnycontrib/config
```

#### 2. Create __init__.py Files
**Files**:
- `thonnycontrib/gui/__init__.py`
- `thonnycontrib/console/__init__.py`
- `thonnycontrib/models/__init__.py`
- `thonnycontrib/utils/__init__.py`
- `thonnycontrib/config/__init__.py`

**Content**: Empty files (makes directories into Python packages)

#### 3. Create Configuration Module
**File**: `thonnycontrib/config/settings.py`

```python
"""Configuration settings for Kiro Interactive CLI."""

# Terminal display settings
TERMINAL_BG_COLOR = "black"
TERMINAL_FG_COLOR = "white"
TERMINAL_FONT = ("Consolas", 10)
TERMINAL_HEIGHT = 20

# Command execution settings
COMMAND_TIMEOUT_SECONDS = 30
SHELL_EXECUTABLE = "/bin/bash"

# Animation settings
LOADING_ANIMATION_INTERVAL_MS = 500

# ANSI color palette
ANSI_COLORS = {
    # Standard 16 colors
    0: "#000000", 1: "#800000", 2: "#008000", 3: "#808000",
    4: "#000080", 5: "#800080", 6: "#008080", 7: "#c0c0c0",
    8: "#808080", 9: "#ff0000", 10: "#00ff00", 11: "#ffff00",
    12: "#0000ff", 13: "#ff00ff", 14: "#00ffff", 15: "#ffffff",
    # Extended colors
    141: "#af87ff",  # Purple (prompt color)
    244: "#808080",  # Gray
    252: "#d0d0d0",  # Light gray
}

# UI text
WELCOME_MESSAGE = "Kiro Interactive CLI"
SEPARATOR_LINE = "=" * 60
```

### Success Criteria:

#### Automated Verification:
- [ ] All directories exist: `ls -la thonnycontrib/gui thonnycontrib/console thonnycontrib/models thonnycontrib/utils thonnycontrib/config`
- [ ] All __init__.py files exist and are readable
- [ ] settings.py can be imported: `python -c "from thonnycontrib.config import settings; print(settings.TERMINAL_BG_COLOR)"`
- [ ] No syntax errors: `python -m py_compile thonnycontrib/config/settings.py`

#### Manual Verification:
- [ ] Directory structure matches the plan
- [ ] Configuration values match existing hardcoded values

**Implementation Note**: This phase is foundational and low-risk. All automated checks should pass before proceeding.

---

## Phase 2: Move Utility Modules

### Overview
Migrate existing well-separated utility modules (ansi_handler.py, loading_animation.py) into the new utils/ folder and update imports to use the config module.

### Changes Required:

#### 1. Move AnsiColorHandler
**Action**: Move file and update imports

**Source**: `thonnycontrib/ansi_handler.py`
**Destination**: `thonnycontrib/utils/ansi_handler.py`

**Changes in ansi_handler.py**:
```python
"""ANSI color code handler for terminal display."""

import re
from thonnycontrib.config.settings import ANSI_COLORS


class AnsiColorHandler:
    """Handles ANSI color codes and formatting for terminal display."""

    def __init__(self, text_widget):
        """
        Initialize the ANSI color handler.

        Args:
            text_widget: tkinter Text widget to apply formatting to
        """
        self.text_widget = text_widget
        self.ansi_colors = ANSI_COLORS  # Use config instead of _create_color_palette()
        self._setup_color_tags()

    # Remove _create_color_palette() method (lines 20-33)

    def _setup_color_tags(self):
        """Setup text tags for ANSI colors in the text widget."""
        for code, color in self.ansi_colors.items():
            self.text_widget.tag_config(f"fg{code}", foreground=color)
            self.text_widget.tag_config(f"bg{code}", background=color)

    # ... rest of the methods remain unchanged ...
```

#### 2. Move LoadingAnimation
**Action**: Move file and update imports

**Source**: `thonnycontrib/loading_animation.py`
**Destination**: `thonnycontrib/utils/loading_animation.py`

**Changes in loading_animation.py**:
```python
"""Loading animation for displaying while waiting for AI response."""

from thonnycontrib.config.settings import LOADING_ANIMATION_INTERVAL_MS


class LoadingAnimation:
    """
    Manages a loading animation that cycles through dots: ".", "..", "..."
    with a colored arrow prefix.
    """

    def __init__(self, terminal_widget, write_callback, get_prompt_symbol_callback):
        # ... existing __init__ code unchanged ...

    def _animate(self):
        """Internal method to handle animation frames."""
        if not self.is_animating:
            return

        # Cycle through 1, 2, 3 dots
        self.dot_count = (self.dot_count % 3) + 1
        dots = "." * self.dot_count

        # Clear previous dots and write new ones
        if self.animation_mark:
            try:
                self.terminal.delete(self.animation_mark, "end")
                self.write_output(dots)
            except:
                pass

        # Use config constant instead of hardcoded 500
        self.animation_id = self.terminal.after(LOADING_ANIMATION_INTERVAL_MS, self._animate)

    # ... rest of the methods remain unchanged ...
```

#### 3. Update Imports in main.py
**File**: `thonnycontrib/main.py`

```python
# OLD (lines 9-10):
from thonnycontrib.ansi_handler import AnsiColorHandler
from thonnycontrib.loading_animation import LoadingAnimation

# NEW:
from thonnycontrib.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.utils.loading_animation import LoadingAnimation
```

#### 4. Delete Old Files
**Action**: Remove original files after verification

```bash
rm thonnycontrib/ansi_handler.py
rm thonnycontrib/loading_animation.py
```

### Success Criteria:

#### Automated Verification:
- [ ] Old files deleted: `test ! -f thonnycontrib/ansi_handler.py && test ! -f thonnycontrib/loading_animation.py`
- [ ] New files exist: `test -f thonnycontrib/utils/ansi_handler.py && test -f thonnycontrib/utils/loading_animation.py`
- [ ] No syntax errors: `python -m py_compile thonnycontrib/utils/*.py`
- [ ] Imports work: `python -c "from thonnycontrib.utils.ansi_handler import AnsiColorHandler; from thonnycontrib.utils.loading_animation import LoadingAnimation"`
- [ ] Plugin loads in Thonny without errors

#### Manual Verification:
- [ ] Plugin appears in Thonny's view menu as "Kiro"
- [ ] Terminal displays with correct colors and fonts
- [ ] Loading animation appears when executing commands
- [ ] ANSI color codes render correctly in terminal output

**Implementation Note**: After this phase completes and all automated verification passes, test the plugin manually in Thonny to confirm no regressions before proceeding.

---

## Phase 3: Create Data Models

### Overview
Extract command representation into a dedicated model class. This provides a clean abstraction for command data.

### Changes Required:

#### 1. Create Command Model
**File**: `thonnycontrib/models/command.py`

```python
"""Command data model for terminal commands."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Command:
    """
    Represents a terminal command with its execution context.

    Attributes:
        text: The command string as entered by user
        working_directory: Directory where command should execute
        is_first_command: Whether this is the first kiro-cli command
        timestamp: When command was created (for history)
    """
    text: str
    working_directory: str
    is_first_command: bool = False
    timestamp: Optional[float] = None

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            import time
            self.timestamp = time.time()

    @property
    def is_empty(self) -> bool:
        """Check if command text is empty or whitespace only."""
        return not self.text.strip()

    @property
    def stripped_text(self) -> str:
        """Get command text with whitespace stripped."""
        return self.text.strip()

    def is_builtin(self) -> bool:
        """Check if this is a built-in command (cd, clear)."""
        stripped = self.stripped_text.lower()
        return stripped.startswith("cd ") or stripped == "clear"


@dataclass
class CommandResult:
    """
    Result of command execution.

    Attributes:
        stdout: Standard output from command
        stderr: Standard error from command
        return_code: Exit code from command
        timed_out: Whether command exceeded timeout
        error: Exception if execution failed
    """
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    timed_out: bool = False
    error: Optional[Exception] = None

    @property
    def succeeded(self) -> bool:
        """Check if command executed successfully."""
        return self.return_code == 0 and not self.timed_out and self.error is None

    @property
    def has_output(self) -> bool:
        """Check if command produced any output."""
        return bool(self.stdout or self.stderr)
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `test -f thonnycontrib/models/command.py`
- [ ] No syntax errors: `python -m py_compile thonnycontrib/models/command.py`
- [ ] Can import models: `python -c "from thonnycontrib.models.command import Command, CommandResult; cmd = Command('test', '/tmp'); print(cmd.stripped_text)"`
- [ ] Dataclass methods work correctly (test basic functionality)

#### Manual Verification:
- [ ] Command model correctly represents command data
- [ ] CommandResult model correctly represents execution results
- [ ] Properties return expected values

**Implementation Note**: This phase is pure data modeling with no side effects. All automated tests should pass before proceeding.

---

## Phase 4: Build Console Layer - History Management

### Overview
Extract command history management from MyDockView into a dedicated CommandHistory class.

### Changes Required:

#### 1. Create CommandHistory Class
**File**: `thonnycontrib/console/command_history.py`

```python
"""Command history management for terminal."""

from typing import List, Optional
from thonnycontrib.models.command import Command


class CommandHistory:
    """
    Manages command history with navigation support.

    Provides functionality for:
    - Adding commands to history
    - Navigating through history (up/down arrows)
    - Retrieving historical commands
    """

    def __init__(self):
        """Initialize empty command history."""
        self._history: List[Command] = []
        self._current_index: int = -1

    def add(self, command: Command) -> None:
        """
        Add a command to history.

        Args:
            command: Command to add to history
        """
        if not command.is_empty:
            self._history.append(command)
            self._current_index = len(self._history)

    def navigate_up(self) -> Optional[str]:
        """
        Navigate to previous command in history.

        Returns:
            Command text if available, None otherwise
        """
        if not self._history or self._current_index <= 0:
            return None

        self._current_index -= 1
        return self._history[self._current_index].text

    def navigate_down(self) -> Optional[str]:
        """
        Navigate to next command in history.

        Returns:
            Command text if available, empty string if at end, None if no history
        """
        if not self._history:
            return None

        if self._current_index < len(self._history) - 1:
            self._current_index += 1
            return self._history[self._current_index].text
        elif self._current_index == len(self._history) - 1:
            # At the most recent command, next is empty input
            self._current_index = len(self._history)
            return ""

        return ""

    def get_all(self) -> List[Command]:
        """
        Get all commands in history.

        Returns:
            List of all historical commands
        """
        return self._history.copy()

    def clear(self) -> None:
        """Clear all history."""
        self._history.clear()
        self._current_index = -1

    @property
    def count(self) -> int:
        """Get number of commands in history."""
        return len(self._history)

    @property
    def is_empty(self) -> bool:
        """Check if history is empty."""
        return len(self._history) == 0
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `test -f thonnycontrib/console/command_history.py`
- [ ] No syntax errors: `python -m py_compile thonnycontrib/console/command_history.py`
- [ ] Can import: `python -c "from thonnycontrib.console.command_history import CommandHistory; h = CommandHistory(); print(h.count)"`

#### Manual Verification:
- [ ] History tracking works correctly
- [ ] Navigation up/down returns correct commands
- [ ] Empty commands are not added to history

**Implementation Note**: This phase creates infrastructure but doesn't integrate it yet. Verify the class works in isolation before proceeding.

---

## Phase 5: Build Console Layer - Built-in Commands

### Overview
Extract built-in command handling (cd, clear) from MyDockView into a dedicated module with a registry pattern.

### Changes Required:

#### 1. Create Built-in Commands Module
**File**: `thonnycontrib/console/builtin_commands.py`

```python
"""Built-in terminal commands (cd, clear)."""

import os
from typing import Callable, Optional
from thonnycontrib.models.command import Command, CommandResult


class BuiltinCommand:
    """Base class for built-in commands."""

    def __init__(self, name: str, description: str):
        """
        Initialize built-in command.

        Args:
            name: Command name
            description: Command description
        """
        self.name = name
        self.description = description

    def matches(self, command: Command) -> bool:
        """
        Check if this handler matches the given command.

        Args:
            command: Command to check

        Returns:
            True if this handler should process the command
        """
        raise NotImplementedError

    def execute(self, command: Command, context: dict) -> CommandResult:
        """
        Execute the built-in command.

        Args:
            command: Command to execute
            context: Execution context (e.g., current working directory)

        Returns:
            CommandResult with execution outcome
        """
        raise NotImplementedError


class CdCommand(BuiltinCommand):
    """Change directory command."""

    def __init__(self):
        super().__init__("cd", "Change working directory")

    def matches(self, command: Command) -> bool:
        """Check if command is 'cd <directory>'."""
        return command.stripped_text.startswith("cd ")

    def execute(self, command: Command, context: dict) -> CommandResult:
        """
        Change working directory.

        Args:
            command: Command with directory path
            context: Must contain 'cwd' key with current directory

        Returns:
            CommandResult indicating success or failure
        """
        new_dir = command.stripped_text[3:].strip()

        try:
            # Expand home directory
            if new_dir.startswith("~"):
                new_dir = os.path.expanduser(new_dir)

            # Convert relative to absolute path
            if not os.path.isabs(new_dir):
                current_dir = context.get('cwd', os.getcwd())
                new_dir = os.path.join(current_dir, new_dir)

            new_dir = os.path.normpath(new_dir)

            # Verify directory exists
            if os.path.isdir(new_dir):
                os.chdir(new_dir)
                context['cwd'] = new_dir
                return CommandResult(stdout=f"Changed directory to: {new_dir}\n")
            else:
                return CommandResult(
                    stderr=f"Error: Directory not found: {new_dir}\n",
                    return_code=1
                )
        except Exception as e:
            return CommandResult(
                stderr=f"Error changing directory: {str(e)}\n",
                return_code=1
            )


class ClearCommand(BuiltinCommand):
    """Clear terminal command."""

    def __init__(self):
        super().__init__("clear", "Clear terminal display")

    def matches(self, command: Command) -> bool:
        """Check if command is 'clear'."""
        return command.stripped_text.lower() == "clear"

    def execute(self, command: Command, context: dict) -> CommandResult:
        """
        Signal to clear terminal (actual clearing done by GUI layer).

        Args:
            command: Clear command
            context: Execution context

        Returns:
            CommandResult with special marker for GUI to clear display
        """
        # Return special result that GUI layer will recognize
        result = CommandResult(stdout="__CLEAR_TERMINAL__\n")
        return result


class BuiltinCommandRegistry:
    """Registry for built-in commands."""

    def __init__(self):
        """Initialize registry with default commands."""
        self._commands = [
            CdCommand(),
            ClearCommand(),
        ]

    def find_handler(self, command: Command) -> Optional[BuiltinCommand]:
        """
        Find handler for given command.

        Args:
            command: Command to find handler for

        Returns:
            BuiltinCommand handler if found, None otherwise
        """
        for cmd in self._commands:
            if cmd.matches(command):
                return cmd
        return None

    def is_builtin(self, command: Command) -> bool:
        """
        Check if command is a built-in.

        Args:
            command: Command to check

        Returns:
            True if command is built-in
        """
        return self.find_handler(command) is not None

    def register(self, command: BuiltinCommand) -> None:
        """
        Register a new built-in command.

        Args:
            command: Built-in command to register
        """
        self._commands.append(command)

    def get_all(self) -> list[BuiltinCommand]:
        """Get all registered commands."""
        return self._commands.copy()
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `test -f thonnycontrib/console/builtin_commands.py`
- [ ] No syntax errors: `python -m py_compile thonnycontrib/console/builtin_commands.py`
- [ ] Can import: `python -c "from thonnycontrib.console.builtin_commands import BuiltinCommandRegistry, CdCommand, ClearCommand"`
- [ ] Registry finds correct handlers for commands

#### Manual Verification:
- [ ] CdCommand correctly identifies and processes cd commands
- [ ] ClearCommand correctly identifies clear command
- [ ] Registry pattern allows for future extensibility

**Implementation Note**: Built-in commands are now modular and extensible. Verify logic before integration.

---

## Phase 6: Build Console Layer - Command Executor

### Overview
Extract command execution logic from MyDockView into a dedicated CommandExecutor class that handles subprocess management and threading.

### Changes Required:

#### 1. Create CommandExecutor Class
**File**: `thonnycontrib/console/command_executor.py`

```python
"""Command execution engine for terminal."""

import subprocess
import threading
from typing import Callable, Optional
from thonnycontrib.models.command import Command, CommandResult
from thonnycontrib.console.builtin_commands import BuiltinCommandRegistry
from thonnycontrib.config.settings import COMMAND_TIMEOUT_SECONDS, SHELL_EXECUTABLE


class CommandExecutor:
    """
    Executes commands via subprocess or built-in handlers.

    Handles:
    - Built-in command execution (cd, clear)
    - External command execution via kiro-cli wrapper
    - Threading for async execution
    - Timeout management
    """

    def __init__(self, builtin_registry: Optional[BuiltinCommandRegistry] = None):
        """
        Initialize command executor.

        Args:
            builtin_registry: Registry of built-in commands (creates default if None)
        """
        self.builtin_registry = builtin_registry or BuiltinCommandRegistry()
        self._is_first_kiro_command = True

    def execute(
        self,
        command: Command,
        context: dict,
        callback: Optional[Callable[[CommandResult], None]] = None,
        async_exec: bool = True
    ) -> None:
        """
        Execute a command.

        Args:
            command: Command to execute
            context: Execution context (must include 'cwd' key)
            callback: Function to call with result (required if async_exec=True)
            async_exec: Whether to execute asynchronously in separate thread
        """
        # Check for built-in commands first
        builtin_handler = self.builtin_registry.find_handler(command)
        if builtin_handler:
            result = builtin_handler.execute(command, context)
            if callback:
                callback(result)
            return

        # Execute external command
        if async_exec:
            if not callback:
                raise ValueError("callback required for async execution")
            threading.Thread(
                target=self._execute_external,
                args=(command, context, callback),
                daemon=True
            ).start()
        else:
            result = self._execute_external_sync(command, context)
            if callback:
                callback(result)

    def _execute_external_sync(self, command: Command, context: dict) -> CommandResult:
        """
        Execute external command synchronously.

        Args:
            command: Command to execute
            context: Execution context

        Returns:
            CommandResult with execution outcome
        """
        try:
            kiro_command = self._build_kiro_command(command)

            result = subprocess.run(
                kiro_command,
                shell=True,
                executable=SHELL_EXECUTABLE,
                capture_output=True,
                text=True,
                cwd=context.get('cwd', None),
                timeout=COMMAND_TIMEOUT_SECONDS
            )

            return CommandResult(
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                stderr=f"Error: Command timed out ({COMMAND_TIMEOUT_SECONDS} seconds)\n",
                return_code=124,
                timed_out=True
            )
        except Exception as e:
            return CommandResult(
                stderr=f"Error executing command: {str(e)}\n",
                return_code=1,
                error=e
            )

    def _execute_external(self, command: Command, context: dict, callback: Callable) -> None:
        """
        Execute external command asynchronously (runs in separate thread).

        Args:
            command: Command to execute
            context: Execution context
            callback: Function to call with result
        """
        result = self._execute_external_sync(command, context)
        callback(result)

    def _build_kiro_command(self, command: Command) -> str:
        """
        Build kiro-cli wrapper command.

        Args:
            command: User command to wrap

        Returns:
            Full kiro-cli command string
        """
        escaped_command = command.stripped_text.replace('"', '\\"')

        if self._is_first_kiro_command:
            kiro_cmd = f'kiro-cli chat --no-interactive "{escaped_command}"'
            self._is_first_kiro_command = False
        else:
            kiro_cmd = f'kiro-cli chat --no-interactive --resume "{escaped_command}"'

        return kiro_cmd

    def reset(self) -> None:
        """Reset executor state (for new conversation)."""
        self._is_first_kiro_command = True
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `test -f thonnycontrib/console/command_executor.py`
- [ ] No syntax errors: `python -m py_compile thonnycontrib/console/command_executor.py`
- [ ] Can import: `python -c "from thonnycontrib.console.command_executor import CommandExecutor"`

#### Manual Verification:
- [ ] Built-in commands execute correctly
- [ ] External commands execute via kiro-cli wrapper
- [ ] Async execution with callbacks works
- [ ] Timeout handling works as expected

**Implementation Note**: This phase extracts complex execution logic. Test thoroughly in isolation before integration.

---

## Phase 7: Build Console Layer - Terminal Controller

### Overview
Create a TerminalController that coordinates all console operations (history, execution, built-in commands) and provides a clean interface to the GUI layer.

### Changes Required:

#### 1. Create TerminalController Class
**File**: `thonnycontrib/console/terminal_controller.py`

```python
"""Terminal controller coordinating console operations."""

import os
from typing import Callable, Optional
from thonnycontrib.models.command import Command, CommandResult
from thonnycontrib.console.command_history import CommandHistory
from thonnycontrib.console.command_executor import CommandExecutor
from thonnycontrib.console.builtin_commands import BuiltinCommandRegistry


class TerminalController:
    """
    Coordinates terminal operations including command execution,
    history management, and state tracking.

    Acts as facade for all console-layer functionality.
    """

    def __init__(self, initial_cwd: Optional[str] = None):
        """
        Initialize terminal controller.

        Args:
            initial_cwd: Initial working directory (uses os.getcwd() if None)
        """
        self.cwd = initial_cwd or os.getcwd()
        self.history = CommandHistory()
        self.executor = CommandExecutor(BuiltinCommandRegistry())
        self._is_executing = False

    def execute_command(
        self,
        command_text: str,
        callback: Callable[[CommandResult], None]
    ) -> None:
        """
        Execute a command.

        Args:
            command_text: Command string to execute
            callback: Function to call with result on completion
        """
        if self._is_executing:
            callback(CommandResult(
                stderr="Error: Command already executing\n",
                return_code=1
            ))
            return

        # Create command object
        command = Command(
            text=command_text,
            working_directory=self.cwd,
            is_first_command=self.executor._is_first_kiro_command
        )

        # Skip empty commands
        if command.is_empty:
            callback(CommandResult())
            return

        # Add to history
        self.history.add(command)

        # Prepare execution context
        context = {'cwd': self.cwd}

        # Wrap callback to update state
        def wrapped_callback(result: CommandResult):
            self._is_executing = False
            # Update working directory if changed by cd command
            self.cwd = context['cwd']
            callback(result)

        # Execute command
        self._is_executing = True
        self.executor.execute(command, context, wrapped_callback, async_exec=True)

    def navigate_history_up(self) -> Optional[str]:
        """
        Navigate to previous command in history.

        Returns:
            Previous command text if available, None otherwise
        """
        return self.history.navigate_up()

    def navigate_history_down(self) -> Optional[str]:
        """
        Navigate to next command in history.

        Returns:
            Next command text if available, None otherwise
        """
        return self.history.navigate_down()

    def reset(self) -> None:
        """Reset terminal controller state (new conversation)."""
        self.executor.reset()
        self._is_executing = False
        # Don't clear history or cwd on reset

    @property
    def is_executing(self) -> bool:
        """Check if command is currently executing."""
        return self._is_executing

    @property
    def working_directory(self) -> str:
        """Get current working directory."""
        return self.cwd
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `test -f thonnycontrib/console/terminal_controller.py`
- [ ] No syntax errors: `python -m py_compile thonnycontrib/console/terminal_controller.py`
- [ ] Can import: `python -c "from thonnycontrib.console.terminal_controller import TerminalController; tc = TerminalController(); print(tc.working_directory)"`

#### Manual Verification:
- [ ] Controller correctly coordinates command execution
- [ ] History navigation works through controller
- [ ] State management (is_executing) works correctly
- [ ] Working directory tracking works

**Implementation Note**: This is the main console-layer facade. Ensure all integrations work before proceeding to GUI layer.

---

## Phase 8: Build GUI Layer - Terminal Widget

### Overview
Extract terminal display functionality from MyDockView into a dedicated TerminalWidget component. This handles text display, ANSI colors, and loading animation.

### Changes Required:

#### 1. Create TerminalWidget Class
**File**: `thonnycontrib/gui/terminal_widget.py`

```python
"""Terminal widget for displaying command output."""

import tkinter as tk
from tkinter import ttk
from thonnycontrib.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.utils.loading_animation import LoadingAnimation
from thonnycontrib.config.settings import (
    TERMINAL_BG_COLOR,
    TERMINAL_FG_COLOR,
    TERMINAL_FONT,
    TERMINAL_HEIGHT,
    WELCOME_MESSAGE,
    SEPARATOR_LINE
)


class TerminalWidget(ttk.Frame):
    """
    Terminal display widget with scrollbar, ANSI color support,
    and loading animation.
    """

    def __init__(self, master, **kwargs):
        """
        Initialize terminal widget.

        Args:
            master: Parent widget
            **kwargs: Additional frame arguments
        """
        super().__init__(master, **kwargs)

        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        # Create text widget
        self.text = tk.Text(
            self,
            wrap="word",
            bg=TERMINAL_BG_COLOR,
            fg=TERMINAL_FG_COLOR,
            font=TERMINAL_FONT,
            insertbackground="white",
            yscrollcommand=self.scrollbar.set,
            height=TERMINAL_HEIGHT,
            relief="flat",
            borderwidth=0
        )
        self.text.pack(side="left", fill="both", expand=True)

        # Link scrollbar
        self.scrollbar.config(command=self.text.yview)

        # Initialize utilities
        self.ansi_handler = AnsiColorHandler(self.text)
        self.loading_animation = LoadingAnimation(
            self.text,
            self.write,
            self._get_prompt_symbol
        )

    def write(self, text: str) -> None:
        """
        Write text to terminal with ANSI color support.

        Args:
            text: Text to write (may contain ANSI codes)
        """
        self.ansi_handler.write_text(text)
        self.text.see("end")

    def clear(self) -> None:
        """Clear all terminal contents."""
        self.text.delete("1.0", "end")

    def show_prompt(self) -> None:
        """Display command prompt."""
        prompt = self._get_prompt_symbol()
        self.text.mark_set("prompt_start", "end-1c")
        self.write(prompt)
        self.text.mark_set("prompt_end", "end-1c")
        self.text.mark_gravity("prompt_start", "left")
        self.text.mark_gravity("prompt_end", "left")
        self.text.see("end")
        self.text.focus_set()

    def get_current_input(self) -> str:
        """
        Get text entered after prompt.

        Returns:
            User input text
        """
        try:
            return self.text.get("prompt_end", "end-1c")
        except:
            return ""

    def clear_current_input(self) -> None:
        """Clear text entered after prompt."""
        try:
            self.text.delete("prompt_end", "end")
        except:
            pass

    def set_current_input(self, text: str) -> None:
        """
        Set the input text after prompt.

        Args:
            text: Text to set as input
        """
        self.clear_current_input()
        self.write(text)

    def start_loading(self) -> None:
        """Start loading animation."""
        self.loading_animation.start()

    def stop_loading(self) -> None:
        """Stop loading animation."""
        self.loading_animation.stop()

    def show_welcome(self, working_directory: str) -> None:
        """
        Display welcome message.

        Args:
            working_directory: Current working directory to display
        """
        self.write(f"{WELCOME_MESSAGE}\n")
        self.write(f"Working Directory: {working_directory}\n")
        self.write(SEPARATOR_LINE + "\n\n")
        self.show_prompt()

    def bind_key(self, key: str, callback) -> None:
        """
        Bind keyboard event to callback.

        Args:
            key: Key sequence (e.g., "<Return>", "<Up>")
            callback: Callback function
        """
        self.text.bind(key, callback)

    def get_cursor_position(self) -> str:
        """
        Get current cursor position.

        Returns:
            Position as "line.column" string
        """
        return self.text.index("insert")

    def get_prompt_end_position(self) -> str:
        """
        Get prompt end position.

        Returns:
            Position as "line.column" string
        """
        return self.text.index("prompt_end")

    def compare_positions(self, pos1: str, op: str, pos2: str) -> bool:
        """
        Compare two text positions.

        Args:
            pos1: First position
            op: Comparison operator ("<", "<=", ">", ">=", "==", "!=")
            pos2: Second position

        Returns:
            Result of comparison
        """
        return self.text.compare(pos1, op, pos2)

    def set_cursor_position(self, position: str) -> None:
        """
        Set cursor position.

        Args:
            position: Position as "line.column" or special marker like "end"
        """
        self.text.mark_set("insert", position)

    def focus(self) -> None:
        """Give focus to terminal."""
        self.text.focus_set()

    @staticmethod
    def _get_prompt_symbol() -> str:
        """
        Get prompt symbol with ANSI color.

        Returns:
            Colored prompt string
        """
        # Purple arrow (ANSI color 141)
        return "\x1B[38;5;141m>\x1B[0m "
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `test -f thonnycontrib/gui/terminal_widget.py`
- [ ] No syntax errors: `python -m py_compile thonnycontrib/gui/terminal_widget.py`
- [ ] Can import: `python -c "from thonnycontrib.gui.terminal_widget import TerminalWidget"`

#### Manual Verification:
- [ ] Terminal widget displays correctly when instantiated
- [ ] Text output with ANSI colors renders correctly
- [ ] Scrollbar functions properly
- [ ] Prompt display works
- [ ] Loading animation works

**Implementation Note**: This is the terminal display abstraction. Test UI components manually before integration.

---

## Phase 9: Build GUI Layer - Dock View

### Overview
Refactor MyDockView to use the new architecture. It becomes a thin coordination layer that connects TerminalWidget and TerminalController.

### Changes Required:

#### 1. Create New DockView Class
**File**: `thonnycontrib/gui/dock_view.py`

```python
"""Kiro dock view for Thonny integration."""

from tkinter import ttk
from thonnycontrib.gui.terminal_widget import TerminalWidget
from thonnycontrib.console.terminal_controller import TerminalController
from thonnycontrib.models.command import CommandResult


class KiroDockView(ttk.Frame):
    """
    Kiro Interactive CLI dock view for Thonny.

    Thin coordination layer connecting GUI and console components.
    """

    def __init__(self, master, **kwargs):
        """
        Initialize dock view.

        Args:
            master: Parent widget
            **kwargs: Additional frame arguments
        """
        super().__init__(master, **kwargs)

        # Initialize controller
        self.controller = TerminalController()

        # Header
        header = ttk.Label(self, text="Kiro", font=("TkDefaultFont", 11, "bold"))
        header.pack(anchor="w", padx=10, pady=(10, 6))

        # Reset button
        button_frame = ttk.Frame(self)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))

        reset_button = ttk.Button(button_frame, text="Reset", command=self._on_reset)
        reset_button.pack(side="right")

        # Terminal widget
        terminal_frame = ttk.Frame(self)
        terminal_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        self.terminal = TerminalWidget(terminal_frame)
        self.terminal.pack(fill="both", expand=True)

        # Bind keyboard events
        self.terminal.bind_key("<Return>", self._on_enter_key)
        self.terminal.bind_key("<Up>", self._on_up_key)
        self.terminal.bind_key("<Down>", self._on_down_key)
        self.terminal.bind_key("<KeyPress>", self._on_key_press)

        # Display welcome message
        self.terminal.show_welcome(self.controller.working_directory)

    def _on_enter_key(self, event):
        """Handle Enter key to execute command."""
        # Block if already executing
        if self.controller.is_executing:
            return "break"

        # Get command text
        command_text = self.terminal.get_current_input().strip()

        # Move to new line
        self.terminal.write("\n")

        if command_text:
            # Start loading animation
            self.terminal.start_loading()

            # Execute command
            self.controller.execute_command(command_text, self._on_command_complete)
        else:
            # Show new prompt for empty input
            self.terminal.show_prompt()

        return "break"

    def _on_command_complete(self, result: CommandResult):
        """
        Handle command completion.

        Args:
            result: Command execution result
        """
        # Stop loading animation
        self.terminal.stop_loading()

        # Check for special clear command
        if result.stdout == "__CLEAR_TERMINAL__\n":
            self.terminal.clear()
            self.terminal.show_welcome(self.controller.working_directory)
            return

        # Display output
        if result.stdout:
            self.terminal.write("\n")
            self.terminal.write(result.stdout)
        if result.stderr:
            self.terminal.write("\n")
            self.terminal.write(result.stderr)
        if not result.has_output and not result.succeeded:
            self.terminal.write(f"\nCommand exited with code {result.return_code}\n")

        # Show new prompt
        self.terminal.show_prompt()

    def _on_up_key(self, event):
        """Navigate to previous command in history."""
        if self.controller.is_executing:
            return "break"

        previous_command = self.controller.navigate_history_up()
        if previous_command is not None:
            self.terminal.set_current_input(previous_command)

        return "break"

    def _on_down_key(self, event):
        """Navigate to next command in history."""
        if self.controller.is_executing:
            return "break"

        next_command = self.controller.navigate_history_down()
        if next_command is not None:
            self.terminal.set_current_input(next_command)

        return "break"

    def _on_key_press(self, event):
        """Validate and control keyboard input."""
        # Block all input while executing
        if self.controller.is_executing:
            return "break"

        # Allow navigation keys
        if event.keysym in ["Up", "Down", "Left", "Right", "Home", "End",
                            "Control_L", "Control_R"]:
            return None

        # Get cursor position
        cursor_pos = self.terminal.get_cursor_position()

        try:
            prompt_end_pos = self.terminal.get_prompt_end_position()

            # Handle backspace - prevent deleting prompt
            if event.keysym == "BackSpace":
                if self.terminal.compare_positions(cursor_pos, "<=", prompt_end_pos):
                    return "break"
                return None

            # Handle delete key
            if event.keysym == "Delete":
                return None

            # For regular characters, move cursor to end if before prompt
            if self.terminal.compare_positions(cursor_pos, "<", prompt_end_pos):
                if event.char and event.char.isprintable():
                    self.terminal.set_cursor_position("end")
                    return None
                return "break"
        except:
            pass

        return None

    def _on_reset(self):
        """Reset conversation and clear terminal."""
        # Stop any running animation
        self.terminal.stop_loading()

        # Reset controller state
        self.controller.reset()

        # Clear and redisplay welcome
        self.terminal.clear()
        self.terminal.show_welcome(self.controller.working_directory)
```

### Success Criteria:

#### Automated Verification:
- [ ] File exists: `test -f thonnycontrib/gui/dock_view.py`
- [ ] No syntax errors: `python -m py_compile thonnycontrib/gui/dock_view.py`
- [ ] Can import: `python -c "from thonnycontrib.gui.dock_view import KiroDockView"`

#### Manual Verification:
- [ ] Dock view displays correctly
- [ ] All keyboard shortcuts work
- [ ] Command execution works end-to-end
- [ ] Reset button works
- [ ] Loading animation displays during execution

**Implementation Note**: This is the main GUI integration. Test thoroughly in Thonny before proceeding to final phase.

---

## Phase 10: Update Plugin Entry Point and Cleanup

### Overview
Update main.py to use the new KiroDockView and remove old MyDockView class. Complete the migration.

### Changes Required:

#### 1. Simplify main.py
**File**: `thonnycontrib/main.py`

```python
"""Kiro Interactive CLI plugin for Thonny."""

from thonny import get_workbench
from thonnycontrib.gui.dock_view import KiroDockView


def load_plugin():
    """
    Called by Thonny at startup to load the plugin.

    Registers the Kiro dock view with Thonny's workbench.
    """
    workbench = get_workbench()

    workbench.add_view(
        KiroDockView,
        "Kiro",
        "se",  # Southeast position
        visible_by_default=True,
    )
```

**Action**: Replace entire main.py content (delete old MyDockView class completely)

#### 2. Verify All Imports
**Action**: Ensure all modules can be imported

```bash
python -c "from thonnycontrib.main import load_plugin; print('✓ Main module OK')"
python -c "from thonnycontrib.gui.dock_view import KiroDockView; print('✓ GUI layer OK')"
python -c "from thonnycontrib.console.terminal_controller import TerminalController; print('✓ Console layer OK')"
python -c "from thonnycontrib.models.command import Command; print('✓ Models OK')"
python -c "from thonnycontrib.utils.ansi_handler import AnsiColorHandler; print('✓ Utils OK')"
python -c "from thonnycontrib.config.settings import TERMINAL_BG_COLOR; print('✓ Config OK')"
```

#### 3. Update pyproject.toml if needed
**File**: `pyproject.toml`

Verify entry point is still correct:
```toml
[project.entry-points."thonny.plugins"]
smart_rover_ai_tutor = "thonnycontrib.main:load_plugin"
```

No changes needed if entry point references `thonnycontrib.main:load_plugin` (which it should).

#### 4. Final File Structure Verification

**Expected structure**:
```
thonnycontrib/
├── __init__.py
├── main.py                    # New simplified version
├── gui/
│   ├── __init__.py
│   ├── dock_view.py
│   └── terminal_widget.py
├── console/
│   ├── __init__.py
│   ├── builtin_commands.py
│   ├── command_executor.py
│   ├── command_history.py
│   └── terminal_controller.py
├── models/
│   ├── __init__.py
│   └── command.py
├── utils/
│   ├── __init__.py
│   ├── ansi_handler.py
│   └── loading_animation.py
└── config/
    ├── __init__.py
    └── settings.py
```

**Old files that should NOT exist**:
- `thonnycontrib/ansi_handler.py` (moved to utils/)
- `thonnycontrib/loading_animation.py` (moved to utils/)

### Success Criteria:

#### Automated Verification:
- [ ] Old files deleted: `test ! -f thonnycontrib/ansi_handler.py && test ! -f thonnycontrib/loading_animation.py`
- [ ] All new files exist: `find thonnycontrib -name "*.py" | wc -l` shows correct count (15 files)
- [ ] No syntax errors: `python -m py_compile thonnycontrib/**/*.py`
- [ ] All imports successful: Run import verification commands above
- [ ] Plugin entry point correct: `grep "load_plugin" pyproject.toml`

#### Manual Verification:
- [ ] Plugin loads successfully in Thonny without errors
- [ ] "Kiro" view appears in Thonny's View menu
- [ ] Terminal displays welcome message
- [ ] Can execute commands successfully
- [ ] Loading animation appears during command execution
- [ ] Command history works (up/down arrows)
- [ ] Built-in commands work (cd, clear)
- [ ] Reset button clears terminal and restarts conversation
- [ ] ANSI colors display correctly
- [ ] Scrollbar functions properly
- [ ] No visual regressions from original implementation

**Implementation Note**: This is the final integration phase. After all automated verification passes, perform comprehensive manual testing of all features in Thonny to ensure no regressions. Test edge cases like:
- Rapid command execution
- Commands that timeout
- Long output with scrolling
- Directory changes with cd command
- Clear command
- Reset during command execution
- Command history at boundaries

---

## Testing Strategy

### Manual Testing Checklist

After completing all phases, perform this comprehensive test:

#### Basic Functionality:
- [ ] Plugin loads without errors in Thonny
- [ ] Terminal displays welcome message
- [ ] Prompt is visible and colored purple
- [ ] Can type commands
- [ ] Enter key executes commands
- [ ] Loading animation displays during execution

#### Command Execution:
- [ ] Simple commands execute successfully
- [ ] Command output displays with correct ANSI colors
- [ ] Error messages display correctly
- [ ] Long-running commands can execute
- [ ] Commands that timeout show timeout error

#### Built-in Commands:
- [ ] `cd` command changes working directory
- [ ] `cd ~` expands home directory
- [ ] `cd ..` navigates to parent directory
- [ ] `cd` to non-existent directory shows error
- [ ] `clear` command clears terminal

#### History:
- [ ] Up arrow navigates to previous command
- [ ] Down arrow navigates to next command
- [ ] Can edit historical command before executing
- [ ] History persists across multiple commands

#### UI/UX:
- [ ] Reset button clears terminal and restarts
- [ ] Scrollbar appears when content exceeds viewport
- [ ] Can scroll through long output
- [ ] Cannot edit text before prompt
- [ ] Backspace doesn't delete prompt
- [ ] Input blocked while command executing

#### Edge Cases:
- [ ] Empty command (just Enter) shows new prompt
- [ ] Reset during command execution works
- [ ] Multiple rapid commands handled correctly
- [ ] Very long output displays correctly
- [ ] Special characters in commands handled

### Regression Testing

Compare behavior against original implementation:

| Feature | Original | Refactored | Status |
|---------|----------|------------|--------|
| Command execution | Working | ? | ☐ |
| ANSI colors | Working | ? | ☐ |
| Loading animation | Working | ? | ☐ |
| History navigation | Working | ? | ☐ |
| cd command | Working | ? | ☐ |
| clear command | Working | ? | ☐ |
| Reset button | Working | ? | ☐ |
| Scrollbar visibility | Working | ? | ☐ |
| Input validation | Working | ? | ☐ |

### Performance Testing

- [ ] Command execution time similar to original
- [ ] UI responsiveness maintained
- [ ] No memory leaks after extended use
- [ ] Animation smooth and non-blocking

## Performance Considerations

This refactoring maintains existing performance characteristics:

- **No new external dependencies** - same libraries (tkinter, subprocess, threading)
- **Similar execution paths** - command flow logically equivalent
- **Same threading model** - async execution unchanged
- **No additional I/O** - no new file operations

**Potential improvements** (not implemented in this phase):
- Command execution could be optimized with connection pooling
- History could be persisted to disk
- Configuration could be cached

## Migration Notes

### For Future Development:

**Adding New Built-in Commands**:
1. Create new class extending `BuiltinCommand` in `builtin_commands.py`
2. Implement `matches()` and `execute()` methods
3. Register with `BuiltinCommandRegistry` in `__init__`

**Example**:
```python
class HelpCommand(BuiltinCommand):
    def __init__(self):
        super().__init__("help", "Show available commands")

    def matches(self, command: Command) -> bool:
        return command.stripped_text.lower() == "help"

    def execute(self, command: Command, context: dict) -> CommandResult:
        help_text = "Available commands:\n  cd <dir> - Change directory\n  clear - Clear terminal\n"
        return CommandResult(stdout=help_text)

# In BuiltinCommandRegistry.__init__:
self._commands = [
    CdCommand(),
    ClearCommand(),
    HelpCommand(),  # Add new command
]
```

**Changing Configuration**:
Edit `thonnycontrib/config/settings.py` to change colors, timeouts, fonts, etc.

**Testing Individual Components**:
Each component can now be tested in isolation:
```python
# Test command history
from thonnycontrib.console.command_history import CommandHistory
from thonnycontrib.models.command import Command

history = CommandHistory()
history.add(Command("test", "/tmp"))
assert history.navigate_up() == "test"
```

## References

- Original implementation: `thonnycontrib/main.py` (pre-refactor)
- Thonny plugin documentation: https://github.com/thonny/thonny/wiki/Plugins
- Related issue: Scrollbar visibility bug (`thoughts/shared/plans/2026-02-03-fix-scrollbar-visibility.md`)
- Terminal prompt visibility investigation: `thoughts/shared/handoffs/general/2026-02-05_09-38-59_terminal-prompt-visibility-bug.md`
