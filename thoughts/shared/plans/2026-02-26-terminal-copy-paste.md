# Terminal Copy and Paste Implementation Plan

## Overview

Implement copy and paste functionality for the Kiro terminal widget to enable users to copy text from the terminal and paste it into Thonny's main editor or back into the terminal. This will support standard keyboard shortcuts (Ctrl+C, Ctrl+V) and a right-click context menu.

## Current State Analysis

The terminal widget (`thonnycontrib/smart_rover/gui/terminal_widget.py`) uses a tkinter Text widget which has built-in text selection capabilities, but:

- **No clipboard integration exists** - no Ctrl+C/Ctrl+V bindings implemented
- **No context menu** - no right-click menu for copy/paste operations
- **Control keys are blocked** - line 130 allows navigation keys but doesn't handle Ctrl+C/Ctrl+V
- **Text selection works** - users can already select text with the mouse via tkinter's default behavior
- **Prompt protection is enforced** - lines 124-154 prevent editing terminal output

### Key Discoveries:

- Terminal widget at `terminal_widget.py:39-53` uses standard tkinter Text widget
- Event binding pattern established at lines 66-71 for keyboard events
- Prompt protection uses marks (`"prompt_end"`) to define editable regions (lines 78-87)
- State-based input blocking via callbacks (`is_executing`, `is_logged_in`) at lines 18-19, 27-28
- No existing clipboard operations in codebase

## Desired End State

Users should be able to:
1. Select text in the terminal with the mouse (already works)
2. Press Ctrl+C to copy selected text to the system clipboard
3. Press Ctrl+V to paste clipboard content at the current cursor position
4. Right-click to open a context menu with Copy and Paste options
5. Paste into the terminal respects prompt protection (can't paste before `prompt_end`)
6. Paste into Thonny's main editor works by default (standard tkinter clipboard)

### Verification:
- Select terminal output text and Ctrl+C copies it
- Ctrl+V in terminal pastes at cursor position (after prompt only)
- Ctrl+V in Thonny editor pastes the copied terminal text
- Right-click in terminal shows context menu with appropriate options enabled/disabled
- Copy only works when text is selected
- Paste respects prompt protection and login/execution state

## What We're NOT Doing

- Ctrl+C will NOT interrupt running commands (keeping existing behavior)
- No special "Paste to Editor" command needed (standard clipboard works across widgets)
- No visual feedback beyond standard selection behavior (selection clears after copy)
- No clipboard history or advanced clipboard features
- No copy/paste of ANSI color codes (plain text only)

## Implementation Approach

Extend the terminal widget's event handling system to support clipboard operations. Use tkinter's built-in clipboard methods (`clipboard_get()`, `clipboard_clear()`, `clipboard_append()`) and add event bindings for Ctrl+C, Ctrl+V, and right-click. Implement state checks to ensure paste respects prompt protection and execution state.

## Phase 1: Implement Copy Functionality

### Overview
Add Ctrl+C keyboard binding to copy selected text to the system clipboard using tkinter's clipboard API.

### Changes Required:

#### 1. Terminal Widget - Add Copy Event Binding and Handler

**File**: `thonnycontrib/smart_rover/gui/terminal_widget.py`

**Changes in `_bind_events()` method (line 66-71)**:

Add Ctrl+C binding after existing event bindings:

```python
def _bind_events(self):
    """Bind keyboard events."""
    self.terminal.bind("<Return>", self._on_enter_key)
    self.terminal.bind("<Up>", self._on_up_key)
    self.terminal.bind("<Down>", self._on_down_key)
    self.terminal.bind("<KeyPress>", self._on_key_press)
    self.terminal.bind("<Control-c>", self._on_copy)  # NEW: Add copy binding
```

**Add new method `_on_copy()` after `_on_down_key()` (after line 194)**:

```python
def _on_copy(self, event):
    """Handle Ctrl+C for copying selected text."""
    try:
        # Check if there's a selection using the "sel" tag
        selection_ranges = self.terminal.tag_ranges("sel")

        if selection_ranges:
            # Get the selected text
            selected_text = self.terminal.get(selection_ranges[0], selection_ranges[1])

            # Copy to clipboard
            self.terminal.clipboard_clear()
            self.terminal.clipboard_append(selected_text)

    except tk.TclError:
        # No selection exists, do nothing
        pass

    # Always return "break" to prevent default Ctrl+C behavior
    return "break"
```

### Success Criteria:

#### Automated Verification:
- [x] No import errors: `python -c "from thonnycontrib.smart_rover.gui.terminal_widget import TerminalWidget; print('Success')"`
- [x] No syntax errors when loading the module

#### Manual Verification:
- [x] Select text in terminal with mouse, press Ctrl+C, paste into Thonny editor - text appears correctly
- [x] Copy terminal output and verify clipboard contains plain text (no ANSI codes visible when pasted)
- [x] Ctrl+C without selection does nothing (no error, no crash)
- [x] Multiple copy operations replace previous clipboard content

**Implementation Note**: After completing this phase and all automated verification passes, test manually that text can be copied from terminal and pasted into Thonny's main editor before proceeding to Phase 2.

---

## Phase 2: Implement Paste Functionality

### Overview
Add Ctrl+V keyboard binding to paste clipboard content into the terminal at the cursor position, respecting prompt protection and execution state.

### Changes Required:

#### 1. Terminal Widget - Add Paste Event Binding and Handler

**File**: `thonnycontrib/smart_rover/gui/terminal_widget.py`

**Changes in `_bind_events()` method (line 66-71)**:

Add Ctrl+V binding after the Ctrl+C binding:

```python
def _bind_events(self):
    """Bind keyboard events."""
    self.terminal.bind("<Return>", self._on_enter_key)
    self.terminal.bind("<Up>", self._on_up_key)
    self.terminal.bind("<Down>", self._on_down_key)
    self.terminal.bind("<KeyPress>", self._on_key_press)
    self.terminal.bind("<Control-c>", self._on_copy)
    self.terminal.bind("<Control-v>", self._on_paste)  # NEW: Add paste binding
```

**Add new method `_on_paste()` after `_on_copy()` method**:

```python
def _on_paste(self, event):
    """Handle Ctrl+V for pasting clipboard content."""
    # Block paste if executing or not logged in
    if self._is_executing() or not self._is_logged_in():
        return "break"

    try:
        # Get clipboard content
        clipboard_text = self.terminal.clipboard_get()

        if not clipboard_text:
            return "break"

        # Get current cursor position
        insert_pos = self.terminal.index("insert")
        prompt_end_pos = self.terminal.index("prompt_end")

        # Only allow paste after prompt_end
        if self.terminal.compare(insert_pos, "<", prompt_end_pos):
            # Move cursor to end if before prompt
            self.terminal.mark_set("insert", "end")

        # Insert clipboard text at cursor position
        self.terminal.insert("insert", clipboard_text)

    except tk.TclError:
        # Clipboard is empty or contains non-text data
        pass

    return "break"
```

### Success Criteria:

#### Automated Verification:
- [x] No import errors: `python -c "from thonnycontrib.smart_rover.gui.terminal_widget import TerminalWidget; print('Success')"`
- [x] No syntax errors when loading the module

#### Manual Verification:
- [x] Copy text from anywhere, press Ctrl+V in terminal after prompt - text is inserted
- [x] Cursor before prompt + Ctrl+V moves cursor to end and pastes
- [x] Ctrl+V while command executing does nothing
- [x] Ctrl+V while not logged in does nothing
- [x] Paste with empty clipboard does nothing (no error, no crash)
- [x] Multi-line paste inserts all lines correctly

**Implementation Note**: After completing this phase, verify that paste works correctly in the terminal and respects prompt protection before proceeding to Phase 3.

---

## Phase 3: Add Right-Click Context Menu

### Overview
Add a right-click context menu with Copy and Paste options that are enabled/disabled based on selection state and clipboard content.

### Changes Required:

#### 1. Terminal Widget - Add Context Menu

**File**: `thonnycontrib/smart_rover/gui/terminal_widget.py`

**Import tkinter menu module at top of file (after line 3)**:

```python
import tkinter as tk
from tkinter import ttk, Menu  # Add Menu import
from typing import Callable, Optional
```

**Add context menu creation in `_setup_ui()` method (after line 55)**:

Add this after scrollbar configuration (after line 55):

```python
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
        borderwidth=TerminalConfig.BORDER_WIDTH,
        padx=TerminalConfig.TEXT_PADDING_X,
        pady=TerminalConfig.TEXT_PADDING_Y
    )
    self.terminal.pack(side="left", fill="both", expand=True)

    self.scrollbar.config(command=self.terminal.yview)

    # NEW: Create context menu
    self._create_context_menu()

def _create_context_menu(self):
    """Create the right-click context menu."""
    self.context_menu = Menu(self.terminal, tearoff=0)
    self.context_menu.add_command(label="Copy", command=self._copy_from_menu)
    self.context_menu.add_command(label="Paste", command=self._paste_from_menu)
```

**Add right-click binding in `_bind_events()` method (after line 71)**:

```python
def _bind_events(self):
    """Bind keyboard events."""
    self.terminal.bind("<Return>", self._on_enter_key)
    self.terminal.bind("<Up>", self._on_up_key)
    self.terminal.bind("<Down>", self._on_down_key)
    self.terminal.bind("<KeyPress>", self._on_key_press)
    self.terminal.bind("<Control-c>", self._on_copy)
    self.terminal.bind("<Control-v>", self._on_paste)
    self.terminal.bind("<Button-3>", self._on_right_click)  # NEW: Add right-click binding
```

**Add new methods for context menu handling (after `_on_paste()` method)**:

```python
def _on_right_click(self, event):
    """Handle right-click to show context menu."""
    # Update menu item states based on current conditions
    self._update_context_menu_state()

    # Show menu at mouse position
    try:
        self.context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        self.context_menu.grab_release()

    return "break"

def _update_context_menu_state(self):
    """Enable/disable context menu items based on current state."""
    # Check if there's a selection for Copy
    try:
        selection_ranges = self.terminal.tag_ranges("sel")
        has_selection = len(selection_ranges) > 0
    except tk.TclError:
        has_selection = False

    # Enable Copy only if text is selected
    if has_selection:
        self.context_menu.entryconfig("Copy", state="normal")
    else:
        self.context_menu.entryconfig("Copy", state="disabled")

    # Enable Paste only if logged in and not executing
    if self._is_logged_in() and not self._is_executing():
        # Also check if clipboard has content
        try:
            clipboard_content = self.terminal.clipboard_get()
            if clipboard_content:
                self.context_menu.entryconfig("Paste", state="normal")
            else:
                self.context_menu.entryconfig("Paste", state="disabled")
        except tk.TclError:
            # Clipboard is empty
            self.context_menu.entryconfig("Paste", state="disabled")
    else:
        self.context_menu.entryconfig("Paste", state="disabled")

def _copy_from_menu(self):
    """Copy selected text when triggered from context menu."""
    # Simulate Ctrl+C event
    self._on_copy(None)

def _paste_from_menu(self):
    """Paste clipboard content when triggered from context menu."""
    # Simulate Ctrl+V event
    self._on_paste(None)
```

### Success Criteria:

#### Automated Verification:
- [x] No import errors: `python -c "from thonnycontrib.smart_rover.gui.terminal_widget import TerminalWidget; print('Success')"`
- [x] No syntax errors when loading the module

#### Manual Verification:
- [x] Right-click in terminal shows context menu with Copy and Paste options
- [x] Copy is disabled when no text is selected
- [x] Copy is enabled when text is selected
- [x] Paste is disabled when not logged in
- [x] Paste is disabled when command is executing
- [x] Paste is disabled when clipboard is empty
- [x] Paste is enabled when logged in, not executing, and clipboard has content
- [x] Clicking Copy from menu copies selected text
- [x] Clicking Paste from menu pastes clipboard content
- [x] Context menu closes when clicking elsewhere

**Implementation Note**: After completing this phase, thoroughly test all context menu scenarios to ensure proper state management before proceeding to Phase 4.

---

## Phase 4: Integration Testing and Edge Cases

### Overview
Comprehensive testing of the copy/paste functionality across different scenarios and edge cases.

### Testing Strategy

#### Unit-Level Tests:
No automated unit tests required (manual testing sufficient for UI interaction).

#### Integration Tests:
Manual testing to verify end-to-end functionality.

#### Manual Testing Steps:

**Copy Tests:**
1. Select multi-line terminal output, press Ctrl+C, paste into Thonny editor - verify all lines appear
2. Select single line, press Ctrl+C, paste into Thonny editor - verify correct
3. Select text with ANSI colors, copy and paste - verify plain text without escape codes
4. Press Ctrl+C without selection - verify no error, clipboard unchanged
5. Copy from terminal, copy from another app, copy from terminal again - verify last copy wins

**Paste Tests:**
1. Copy text, click after prompt in terminal, press Ctrl+V - text appears at cursor
2. Copy text, click before prompt, press Ctrl+V - cursor moves to end and text is pasted
3. Run a command (executing state), try Ctrl+V - nothing happens
4. Logout, try Ctrl+V - nothing happens
5. Copy multi-line text, paste into terminal - all lines inserted correctly
6. Paste with empty clipboard - no error, nothing happens

**Context Menu Tests:**
1. Right-click without selection - Copy is disabled
2. Select text, right-click - Copy is enabled
3. Right-click while logged out - Paste is disabled
4. Right-click while logged in with clipboard content - Paste is enabled
5. Right-click with empty clipboard - Paste is disabled
6. Click Copy from menu - text is copied
7. Click Paste from menu - text is pasted
8. Click outside menu - menu closes

**Cross-Widget Tests:**
1. Copy from terminal, paste into Thonny editor - works correctly
2. Copy from Thonny editor, paste into terminal - works correctly
3. Copy from external app, paste into terminal - works correctly
4. Copy from terminal, paste into external app - works correctly

**Edge Cases:**
1. Select partial command input, copy, paste - works correctly
2. Very long text (1000+ characters) - copy and paste work
3. Text with special characters (tabs, newlines, unicode) - preserved correctly
4. Rapid copy/paste operations - no race conditions or crashes
5. Copy while command executing - works (copy doesn't require input state)

### Success Criteria:

#### Automated Verification:
- [x] Plugin loads without errors in Thonny
- [x] No Python exceptions in Thonny's error log

#### Manual Verification:
- [x] All copy tests pass
- [x] All paste tests pass
- [x] All context menu tests pass
- [x] All cross-widget tests pass
- [x] All edge case tests pass
- [x] No regressions in existing terminal functionality (command execution, history, etc.)

**Implementation Note**: This is the final phase. Complete all manual testing and verify no regressions before considering the feature complete.

---

## Testing Strategy

### Manual Testing Steps:

See Phase 4 for comprehensive testing checklist.

### Key Test Scenarios:

1. **Basic Copy**: Select terminal output → Ctrl+C → Paste in Thonny editor
2. **Basic Paste**: Copy text → Ctrl+V in terminal after prompt
3. **Prompt Protection**: Copy text → Click before prompt → Ctrl+V → Cursor moves to end
4. **State Blocking**: Execute command → Try Ctrl+V → Nothing happens
5. **Context Menu**: Right-click → Select Copy/Paste → Action occurs

## Performance Considerations

- Clipboard operations are synchronous and should be fast for typical terminal output
- No performance impact on command execution or terminal rendering
- Context menu state updates are O(1) operations checking selection and clipboard state
- Large clipboard content (MB+) may cause brief lag, but this is rare in terminal usage

## Migration Notes

No migration required. This is a new feature with no impact on existing functionality or saved state.

## References

- Terminal Widget: `thonnycontrib/smart_rover/gui/terminal_widget.py:11-195`
- Event Binding Pattern: `terminal_widget.py:66-71`
- Prompt Protection: `terminal_widget.py:124-154`
- State-Based Input Blocking: `terminal_widget.py:127-128`, `159-160`, `171-172`, `184-185`
- Tkinter Text Widget Clipboard Methods: Standard tkinter.Text API
- Tkinter Menu Widget: Standard tkinter.Menu API

## Implementation Notes

- Clipboard operations use tkinter's built-in methods (cross-platform compatible)
- Text copied is always plain text (ANSI codes are not copied)
- Paste into terminal respects all existing input restrictions (prompt protection, login state, execution state)
- Context menu state is updated each time before display to reflect current conditions
- All event handlers return "break" to prevent default tkinter behavior
