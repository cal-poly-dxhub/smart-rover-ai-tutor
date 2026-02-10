# Refactor Imports to Match New Folder Structure

## Overview

Fix 26 broken import statements across 12 files that are using incorrect paths after the codebase was reorganized into the `thonnycontrib.smart_rover` package structure. All internal imports currently reference `thonnycontrib.MODULE` but need to reference `thonnycontrib.smart_rover.MODULE` to match the current directory structure.

## Current State Analysis

After commit `e863a4e` ("Refactor codebase to object-oriented architecture"), the code was moved into a `smart_rover` subdirectory under `thonnycontrib/`:

```
thonnycontrib/
  └── smart_rover/          # Code moved here
      ├── config/
      ├── console/
      ├── gui/
      ├── models/
      └── utils/
```

However, all imports still reference the old flat structure paths, causing import errors.

### Key Discoveries:
- 26 incorrect import statements across 12 Python files
- All use pattern: `from thonnycontrib.MODULE import ...`
- Should use: `from thonnycontrib.smart_rover.MODULE import ...`
- 1 file (`utils/__init__.py`) has duplicate import blocks (lines 3-6 duplicated at 8-11)
- The plugin likely fails to load due to these broken imports

## Desired End State

All imports correctly reference the `thonnycontrib.smart_rover.*` package structure, and the Thonny plugin loads successfully without import errors.

### Verification:
1. All import statements include `smart_rover` in the path
2. No duplicate imports exist
3. Plugin loads in Thonny without errors
4. All plugin features work as expected

## What We're NOT Doing

- NOT switching to relative imports (staying with absolute imports)
- NOT reorganizing the folder structure further
- NOT refactoring any functionality
- NOT updating external dependencies

## Implementation Approach

Systematically update all import statements file-by-file, organized by package directory. Use a consistent pattern: replace `thonnycontrib.` with `thonnycontrib.smart_rover.` for all internal imports. Remove duplicate imports in `utils/__init__.py`.

---

## Phase 1: Fix Root Package Imports

### Overview
Fix the main entry point `__init__.py` to correctly import the GUI components.

### Changes Required:

#### 1. Root Package Init
**File**: `thonnycontrib/smart_rover/__init__.py`
**Changes**: Update line 7 to include `smart_rover` in path

**Current**:
```python
from thonny import get_workbench
from thonnycontrib.gui.dock_view import KiroDockView
```

**Updated**:
```python
from thonny import get_workbench
from thonnycontrib.smart_rover.gui.dock_view import KiroDockView
```

### Success Criteria:

#### Automated Verification:
- [ ] File syntax is valid: `python -m py_compile thonnycontrib/smart_rover/__init__.py`
- [ ] Import can be resolved: `python -c "from thonnycontrib.smart_rover.gui.dock_view import KiroDockView"`

#### Manual Verification:
- [ ] No syntax errors when opening file in IDE
- [ ] Import statement uses correct path with `smart_rover`

---

## Phase 2: Fix Config Package Imports

### Overview
Update all imports in the config package to reference the correct paths.

### Changes Required:

#### 1. Config Package Init
**File**: `thonnycontrib/smart_rover/config/__init__.py`
**Changes**: Update line 3 to include `smart_rover` in path

**Current**:
```python
from thonnycontrib.config.settings import (
    TerminalConfig,
    AnimationConfig,
    ExecutionConfig,
    UIConfig,
    AnsiColorConfig
)
```

**Updated**:
```python
from thonnycontrib.smart_rover.config.settings import (
    TerminalConfig,
    AnimationConfig,
    ExecutionConfig,
    UIConfig,
    AnsiColorConfig
)
```

### Success Criteria:

#### Automated Verification:
- [ ] File syntax is valid: `python -m py_compile thonnycontrib/smart_rover/config/__init__.py`
- [ ] Imports can be resolved: `python -c "from thonnycontrib.smart_rover.config import TerminalConfig"`

#### Manual Verification:
- [ ] Import statement uses correct path with `smart_rover`

---

## Phase 3: Fix Console Package Imports

### Overview
Update all imports across the 4 console module files.

### Changes Required:

#### 1. Console Package Init
**File**: `thonnycontrib/smart_rover/console/__init__.py`
**Changes**: Update lines 3-6 to include `smart_rover` in paths

**Current**:
```python
from thonnycontrib.console.terminal_controller import TerminalController
from thonnycontrib.console.command_executor import CommandExecutor
from thonnycontrib.console.command_history import CommandHistory
from thonnycontrib.console.builtin_commands import BuiltinCommandHandler
```

**Updated**:
```python
from thonnycontrib.smart_rover.console.terminal_controller import TerminalController
from thonnycontrib.smart_rover.console.command_executor import CommandExecutor
from thonnycontrib.smart_rover.console.command_history import CommandHistory
from thonnycontrib.smart_rover.console.builtin_commands import BuiltinCommandHandler
```

#### 2. Builtin Commands
**File**: `thonnycontrib/smart_rover/console/builtin_commands.py`
**Changes**: Update line 5

**Current**:
```python
from thonnycontrib.models.command import Command, CommandResult
```

**Updated**:
```python
from thonnycontrib.smart_rover.models.command import Command, CommandResult
```

#### 3. Command Executor
**File**: `thonnycontrib/smart_rover/console/command_executor.py`
**Changes**: Update lines 6-7

**Current**:
```python
from thonnycontrib.models.command import Command, CommandResult
from thonnycontrib.config.settings import ExecutionConfig
```

**Updated**:
```python
from thonnycontrib.smart_rover.models.command import Command, CommandResult
from thonnycontrib.smart_rover.config.settings import ExecutionConfig
```

#### 4. Terminal Controller
**File**: `thonnycontrib/smart_rover/console/terminal_controller.py`
**Changes**: Update lines 5-8

**Current**:
```python
from thonnycontrib.models.command import Command, CommandResult
from thonnycontrib.console.command_executor import CommandExecutor
from thonnycontrib.console.command_history import CommandHistory
from thonnycontrib.console.builtin_commands import BuiltinCommandHandler
```

**Updated**:
```python
from thonnycontrib.smart_rover.models.command import Command, CommandResult
from thonnycontrib.smart_rover.console.command_executor import CommandExecutor
from thonnycontrib.smart_rover.console.command_history import CommandHistory
from thonnycontrib.smart_rover.console.builtin_commands import BuiltinCommandHandler
```

### Success Criteria:

#### Automated Verification:
- [ ] All console files compile: `python -m py_compile thonnycontrib/smart_rover/console/*.py`
- [ ] Console package imports work: `python -c "from thonnycontrib.smart_rover.console import TerminalController"`

#### Manual Verification:
- [ ] All import statements in console/ use correct paths with `smart_rover`

---

## Phase 4: Fix GUI Package Imports

### Overview
Update all imports across the 2 GUI module files.

### Changes Required:

#### 1. GUI Package Init
**File**: `thonnycontrib/smart_rover/gui/__init__.py`
**Changes**: Update lines 3-4

**Current**:
```python
from thonnycontrib.gui.dock_view import KiroDockView
from thonnycontrib.gui.terminal_widget import TerminalWidget
```

**Updated**:
```python
from thonnycontrib.smart_rover.gui.dock_view import KiroDockView
from thonnycontrib.smart_rover.gui.terminal_widget import TerminalWidget
```

#### 2. Dock View
**File**: `thonnycontrib/smart_rover/gui/dock_view.py`
**Changes**: Update lines 4-6

**Current**:
```python
from thonnycontrib.gui.terminal_widget import TerminalWidget
from thonnycontrib.console.terminal_controller import TerminalController
from thonnycontrib.config.settings import UIConfig
```

**Updated**:
```python
from thonnycontrib.smart_rover.gui.terminal_widget import TerminalWidget
from thonnycontrib.smart_rover.console.terminal_controller import TerminalController
from thonnycontrib.smart_rover.config.settings import UIConfig
```

#### 3. Terminal Widget
**File**: `thonnycontrib/smart_rover/gui/terminal_widget.py`
**Changes**: Update lines 6-8

**Current**:
```python
from thonnycontrib.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.utils.loading_animation import LoadingAnimation
from thonnycontrib.config.settings import TerminalConfig, AnsiColorConfig
```

**Updated**:
```python
from thonnycontrib.smart_rover.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.smart_rover.utils.loading_animation import LoadingAnimation
from thonnycontrib.smart_rover.config.settings import TerminalConfig, AnsiColorConfig
```

### Success Criteria:

#### Automated Verification:
- [ ] All GUI files compile: `python -m py_compile thonnycontrib/smart_rover/gui/*.py`
- [ ] GUI package imports work: `python -c "from thonnycontrib.smart_rover.gui import KiroDockView"`

#### Manual Verification:
- [ ] All import statements in gui/ use correct paths with `smart_rover`

---

## Phase 5: Fix Models Package Imports

### Overview
Update the models package init file.

### Changes Required:

#### 1. Models Package Init
**File**: `thonnycontrib/smart_rover/models/__init__.py`
**Changes**: Update line 3

**Current**:
```python
from thonnycontrib.models.command import Command, CommandResult
```

**Updated**:
```python
from thonnycontrib.smart_rover.models.command import Command, CommandResult
```

### Success Criteria:

#### Automated Verification:
- [ ] File compiles: `python -m py_compile thonnycontrib/smart_rover/models/__init__.py`
- [ ] Models import works: `python -c "from thonnycontrib.smart_rover.models import Command"`

#### Manual Verification:
- [ ] Import statement uses correct path with `smart_rover`

---

## Phase 6: Fix Utils Package Imports and Remove Duplicates

### Overview
Update all imports in utils package and remove duplicate import blocks.

### Changes Required:

#### 1. Utils Package Init
**File**: `thonnycontrib/smart_rover/utils/__init__.py`
**Changes**: Update lines 3-4 and remove duplicate lines 8-11

**Current**:
```python
from thonnycontrib.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.utils.loading_animation import LoadingAnimation

__all__ = ["AnsiColorHandler", "LoadingAnimation"]

from thonnycontrib.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.utils.loading_animation import LoadingAnimation

__all__ = ["AnsiColorHandler", "LoadingAnimation"]
```

**Updated**:
```python
from thonnycontrib.smart_rover.utils.ansi_handler import AnsiColorHandler
from thonnycontrib.smart_rover.utils.loading_animation import LoadingAnimation

__all__ = ["AnsiColorHandler", "LoadingAnimation"]
```

#### 2. ANSI Handler
**File**: `thonnycontrib/smart_rover/utils/ansi_handler.py`
**Changes**: Update line 4

**Current**:
```python
from thonnycontrib.config.settings import AnsiColorConfig
```

**Updated**:
```python
from thonnycontrib.smart_rover.config.settings import AnsiColorConfig
```

#### 3. Loading Animation
**File**: `thonnycontrib/smart_rover/utils/loading_animation.py`
**Changes**: Update line 3

**Current**:
```python
from thonnycontrib.config.settings import AnimationConfig
```

**Updated**:
```python
from thonnycontrib.smart_rover.config.settings import AnimationConfig
```

### Success Criteria:

#### Automated Verification:
- [ ] All utils files compile: `python -m py_compile thonnycontrib/smart_rover/utils/*.py`
- [ ] Utils imports work: `python -c "from thonnycontrib.smart_rover.utils import AnsiColorHandler"`
- [ ] No duplicate lines in `utils/__init__.py`: `grep -n "from thonnycontrib" thonnycontrib/smart_rover/utils/__init__.py | wc -l` returns 2

#### Manual Verification:
- [ ] All import statements in utils/ use correct paths with `smart_rover`
- [ ] No duplicate import blocks exist in `utils/__init__.py`

---

## Phase 7: End-to-End Verification

### Overview
Verify the entire plugin works correctly with all imports fixed.

### Testing Steps:

#### Automated Verification:
- [ ] All Python files compile: `find thonnycontrib/smart_rover -name "*.py" -exec python -m py_compile {} \;`
- [ ] Top-level package imports: `python -c "import thonnycontrib.smart_rover"`
- [ ] No references to old paths remain: `grep -r "from thonnycontrib\\.\\(config\\|console\\|gui\\|models\\|utils\\)" thonnycontrib/smart_rover/ | grep -v smart_rover` returns no results
- [ ] Count of correct imports: `grep -r "from thonnycontrib.smart_rover" thonnycontrib/smart_rover/ | wc -l` returns 26

#### Manual Verification:
- [ ] Install plugin in Thonny's plugin directory
- [ ] Restart Thonny - plugin loads without import errors
- [ ] Open the Smart Rover terminal from Tools menu
- [ ] Test basic commands (help, clear, echo)
- [ ] Verify ANSI colors display correctly
- [ ] Verify loading animation works
- [ ] Run a Python command and verify execution works

**Implementation Note**: After all automated verification passes, pause here for manual confirmation that the plugin works correctly in Thonny before considering this phase complete.

---

## Testing Strategy

### Unit Tests:
- Compile all Python files to catch syntax errors
- Import each package to verify import chains work
- Search for old import patterns to ensure none remain

### Manual Testing Steps:
1. Copy `thonnycontrib` directory to Thonny's plugin site-packages
2. Launch Thonny and check for startup errors in the console
3. Open Tools → Smart Rover Terminal
4. Execute `help` command - should display available commands
5. Execute `echo Hello World` - should display the text
6. Execute `python print("test")` - should run Python code
7. Verify colored output appears correctly
8. Verify no error messages about missing modules

## Performance Considerations

No performance impact - this is purely fixing broken imports. The import mechanism and runtime behavior remain unchanged.

## Migration Notes

No migration needed - this is a bug fix for code organization. Users simply need to update to the fixed version.

## Files Modified Summary

Total: 12 files
- `thonnycontrib/smart_rover/__init__.py` - 1 import fixed
- `thonnycontrib/smart_rover/config/__init__.py` - 1 import fixed
- `thonnycontrib/smart_rover/console/__init__.py` - 4 imports fixed
- `thonnycontrib/smart_rover/console/builtin_commands.py` - 1 import fixed
- `thonnycontrib/smart_rover/console/command_executor.py` - 2 imports fixed
- `thonnycontrib/smart_rover/console/terminal_controller.py` - 4 imports fixed
- `thonnycontrib/smart_rover/gui/__init__.py` - 2 imports fixed
- `thonnycontrib/smart_rover/gui/dock_view.py` - 3 imports fixed
- `thonnycontrib/smart_rover/gui/terminal_widget.py` - 3 imports fixed
- `thonnycontrib/smart_rover/models/__init__.py` - 1 import fixed
- `thonnycontrib/smart_rover/utils/__init__.py` - 2 imports fixed + duplicates removed
- `thonnycontrib/smart_rover/utils/ansi_handler.py` - 1 import fixed
- `thonnycontrib/smart_rover/utils/loading_animation.py` - 1 import fixed

**Total import fixes**: 26 imports + 1 duplicate removal

## References

- Refactoring commit: `e863a4e` - "Refactor codebase to object-oriented architecture with separation of concerns"
- Import analysis: Research completed 2026-02-10
- Pattern found: All imports missing `smart_rover` in path after code reorganization
