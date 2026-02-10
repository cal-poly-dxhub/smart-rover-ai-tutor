# Fix Scrollbar Visibility in Plugin Dockable Window

## Overview

Fix the invisible scrollbar issue in the Kiro plugin's terminal interface. The scrollbar is implemented in code but not visible to users, making it difficult to navigate through long terminal output.

## Current State Analysis

**Existing Implementation**: `thonnycontrib/main.py:62-64`
```python
scrollbar = ttk.Scrollbar(terminal_frame, command=self.terminal.yview)
scrollbar.pack(side="right", fill="y")
self.terminal.config(yscrollcommand=scrollbar.set)
```

**Key Discoveries:**
- Scrollbar exists and is properly linked to the Text widget at `main.py:62-64`
- Uses `ttk.Scrollbar` which follows Thonny's theme
- Terminal widget has black background (`bg="black"`) at `main.py:47`
- Terminal frame uses pack geometry manager with terminal on left, scrollbar on right at `main.py:42-64`
- Scrollbar may be invisible due to theme colors blending with dark terminal or improper sizing

**Root Causes:**
1. **Theme Color Conflict**: ttk.Scrollbar inherits theme colors that may blend with the black terminal background
2. **Layout Issue**: Scrollbar might not be getting allocated visible space
3. **Content Threshold**: Scrollbar may only appear when content exceeds viewport (tkinter default behavior)
4. **Widget Stacking**: Terminal widget might be overlapping the scrollbar area

## Desired End State

A clearly visible, functional scrollbar that:
- Is always visible (not just when content overflows)
- Has contrasting colors against the black terminal background
- Responds to mouse wheel and click interactions
- Maintains consistent appearance across different Thonny themes
- Does not interfere with terminal text display or input

### Verification:
- Scrollbar is visually present on the right side of the terminal
- Scrollbar thumb is visible and distinct from the trough
- Scrollbar works with both mouse click and mouse wheel
- Scrollbar appearance is consistent after window resize
- Terminal text remains fully visible and editable

## What We're NOT Doing

- Not adding horizontal scrollbar (terminal uses word wrap)
- Not changing the terminal color scheme or font
- Not modifying ANSI color handling or loading animation
- Not altering the command execution logic
- Not changing the dockable window position or size
- Not implementing custom scrollbar widgets (using standard ttk)

## Implementation Approach

The fix involves three strategies applied in sequence:
1. **Ensure proper layout** - Fix any packing issues that prevent scrollbar visibility
2. **Style the scrollbar** - Apply custom styling to make it visible against dark background
3. **Force visibility** - Configure the scrollbar to always be visible, not auto-hide

We'll modify only the scrollbar configuration section in `main.py` without affecting other functionality.

## Phase 1: Fix Layout and Basic Visibility

### Overview
Ensure the scrollbar is properly laid out with allocated space and basic visibility by adjusting the packing configuration and widget ordering.

### Changes Required:

#### 1. Terminal Frame Layout Fix
**File**: `thonnycontrib/main.py`
**Changes**: Update the terminal frame and scrollbar packing configuration (lines 42-64)

**Current Code** (lines 42-64):
```python
# Terminal frame
terminal_frame = ttk.Frame(self)
terminal_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

# Terminal display/input
self.terminal = tk.Text(terminal_frame, wrap="word",
                       bg="black", fg="white", font=("Consolas", 10),
                       insertbackground="white")
self.terminal.pack(side="left", fill="both", expand=True)

# Initialize ANSI color handler
self.ansi_handler = AnsiColorHandler(self.terminal)

# Initialize loading animation
self.loading_animation = LoadingAnimation(
    self.terminal,
    self._write_output,
    self._get_prompt_symbol
)

# Scrollbar
scrollbar = ttk.Scrollbar(terminal_frame, command=self.terminal.yview)
scrollbar.pack(side="right", fill="y")
self.terminal.config(yscrollcommand=scrollbar.set)
```

**New Code**:
```python
# Terminal frame
terminal_frame = ttk.Frame(self)
terminal_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

# Scrollbar (pack BEFORE terminal to ensure it gets space)
scrollbar = ttk.Scrollbar(terminal_frame, orient="vertical")
scrollbar.pack(side="right", fill="y")

# Terminal display/input
self.terminal = tk.Text(terminal_frame, wrap="word",
                       bg="black", fg="white", font=("Consolas", 10),
                       insertbackground="white",
                       yscrollcommand=scrollbar.set)
self.terminal.pack(side="left", fill="both", expand=True)

# Link scrollbar to terminal
scrollbar.config(command=self.terminal.yview)

# Initialize ANSI color handler
self.ansi_handler = AnsiColorHandler(self.terminal)

# Initialize loading animation
self.loading_animation = LoadingAnimation(
    self.terminal,
    self._write_output,
    self._get_prompt_symbol
)
```

**Key Changes:**
1. Pack scrollbar BEFORE terminal widget (ensures space allocation)
2. Explicitly set `orient="vertical"` on scrollbar
3. Move `yscrollcommand=scrollbar.set` to terminal widget initialization
4. Configure scrollbar command after both widgets are created

**Rationale:**
- Packing order matters in tkinter - widgets packed first get priority for space allocation
- Explicit orientation prevents ambiguity
- Moving yscrollcommand to Text constructor is cleaner and ensures proper binding from initialization

### Success Criteria:

#### Automated Verification:
- [ ] Python syntax is valid: `python -m py_compile thonnycontrib/main.py`
- [ ] No import errors: `python -c "from thonnycontrib.main import load_plugin"`
- [ ] Plugin loads in Thonny without errors

#### Manual Verification:
- [ ] Scrollbar appears on the right side of the terminal area
- [ ] Scrollbar has allocated space (not zero width)
- [ ] Terminal text is still fully visible
- [ ] No layout breaking or widget overlap

**Implementation Note**: After completing this phase and automated verification passes, test in Thonny IDE to confirm scrollbar is visible before proceeding to the next phase.

---

## Phase 2: Enhance Scrollbar Styling for Dark Theme

### Overview
Apply custom styling to make the scrollbar more visible against the dark terminal background by configuring ttk styles.

### Changes Required:

#### 1. Add Scrollbar Style Configuration
**File**: `thonnycontrib/main.py`
**Changes**: Add style configuration after the terminal frame setup

**Insert after line 43** (after `terminal_frame.pack(...)`):
```python
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
```

**Update scrollbar creation** (around line 62):
```python
# Scrollbar (pack BEFORE terminal to ensure it gets space)
scrollbar = ttk.Scrollbar(terminal_frame, orient="vertical", style="Kiro.Vertical.TScrollbar")
scrollbar.pack(side="right", fill="y")
```

**Rationale:**
- Custom ttk.Style allows overriding theme defaults
- Lighter gray colors contrast with black terminal background
- Style.map provides hover feedback
- Try-except prevents crashes if style configuration fails
- Custom style name "Kiro.Vertical.TScrollbar" avoids affecting other Thonny widgets

#### 2. Alternative: Store Scrollbar as Instance Variable
**File**: `thonnycontrib/main.py`
**Changes**: Change scrollbar from local to instance variable for future customization

**Change from:**
```python
scrollbar = ttk.Scrollbar(terminal_frame, orient="vertical", style="Kiro.Vertical.TScrollbar")
```

**To:**
```python
self.scrollbar = ttk.Scrollbar(terminal_frame, orient="vertical", style="Kiro.Vertical.TScrollbar")
```

**And update references:**
```python
self.scrollbar.pack(side="right", fill="y")
# ...
self.terminal = tk.Text(terminal_frame, wrap="word",
                       bg="black", fg="white", font=("Consolas", 10),
                       insertbackground="white",
                       yscrollcommand=self.scrollbar.set)
# ...
self.scrollbar.config(command=self.terminal.yview)
```

**Rationale:**
- Instance variable allows future methods to modify scrollbar behavior
- Consistent with other widgets (self.terminal, self.ansi_handler)
- Enables potential future features (e.g., hiding/showing scrollbar)

### Success Criteria:

#### Automated Verification:
- [ ] Python syntax is valid: `python -m py_compile thonnycontrib/main.py`
- [ ] No import errors: `python -c "from thonnycontrib.main import load_plugin"`
- [ ] Plugin loads in Thonny without errors

#### Manual Verification:
- [ ] Scrollbar has visible contrast against black terminal
- [ ] Scrollbar thumb is distinguishable from trough
- [ ] Hover effects work (thumb changes appearance on mouseover)
- [ ] Scrollbar maintains visibility with different Thonny themes (light and dark)
- [ ] Terminal functionality remains unaffected

**Implementation Note**: Test with both light and dark Thonny themes to ensure the custom colors work in both contexts. If the custom styling causes issues with light themes, consider detecting the theme and applying conditional styling.

---

## Phase 3: Ensure Scrollbar Always Visible

### Overview
Configure the terminal and scrollbar to ensure the scrollbar is always visible, even when content fits in the viewport, and improve scrolling behavior.

### Changes Required:

#### 1. Configure Terminal Height for Scroll Behavior
**File**: `thonnycontrib/main.py`
**Changes**: Update terminal widget configuration to ensure content can overflow

**Modify terminal creation** (around line 47):
```python
# Terminal display/input
self.terminal = tk.Text(terminal_frame, wrap="word",
                       bg="black", fg="white", font=("Consolas", 10),
                       insertbackground="white",
                       yscrollcommand=scrollbar.set,
                       height=20,  # Set explicit height to ensure scrollbar shows
                       relief="flat",  # Remove border for cleaner look
                       borderwidth=0)
self.terminal.pack(side="left", fill="both", expand=True)
```

**Rationale:**
- Explicit height ensures the widget has defined dimensions for scroll calculation
- `relief="flat"` and `borderwidth=0` improve visual appearance
- Setting height doesn't prevent expansion (expand=True still applies)

#### 2. Add Initial Content to Trigger Scrollbar
**File**: `thonnycontrib/main.py`
**Changes**: No code changes needed; current implementation already adds welcome content

**Current working code** (lines 73-76):
```python
# Display welcome message and first prompt
self._write_output(f"Kiro Interactive CLI\n")
self._write_output(f"Working Directory: {self.cwd}\n")
self._write_output("=" * 60 + "\n\n")
self._show_prompt()
```

**Verify this content is sufficient to make scrollbar visible**. If needed, add extra blank lines to ensure content exceeds initial viewport:
```python
# Display welcome message and first prompt
self._write_output(f"Kiro Interactive CLI\n")
self._write_output(f"Working Directory: {self.cwd}\n")
self._write_output("=" * 60 + "\n\n")
# Add enough blank lines to ensure scrollbar appears initially
self._write_output("\n" * 10)
self._show_prompt()
```

**Rationale:**
- Scrollbar typically only appears when content exceeds viewport
- Initial content ensures scrollbar is visible from startup
- Extra blank lines are harmless and disappear as user adds output

#### 3. Optional: Configure Scrollbar to Always Show
**File**: `thonnycontrib/main.py`
**Changes**: Consider platform-specific options if needed

**Note**: Standard ttk.Scrollbar doesn't have an "always visible" option. The approaches above (explicit height + initial content) achieve the same goal. On some platforms, scrollbars auto-hide when content fits; this is OS-level behavior that cannot be overridden with standard ttk widgets.

**If needed for specific platforms**, document this limitation:
```python
# Note: On some platforms (macOS, modern Windows), scrollbars may auto-hide
# when content fits in viewport. This is OS-level behavior.
# The scrollbar will reappear when content exceeds the visible area.
```

### Success Criteria:

#### Automated Verification:
- [ ] Python syntax is valid: `python -m py_compile thonnycontrib/main.py`
- [ ] No import errors: `python -c "from thonnycontrib.main import load_plugin"`
- [ ] Plugin loads in Thonny without errors

#### Manual Verification:
- [ ] Scrollbar is visible immediately when plugin opens
- [ ] Scrollbar remains visible after window resize
- [ ] Scrollbar responds to mouse wheel scrolling
- [ ] Scrollbar thumb can be dragged to scroll
- [ ] Scrollbar arrows (if present) work correctly
- [ ] Auto-scroll to bottom (via `self.terminal.see("end")`) still works
- [ ] Terminal remains responsive and functional
- [ ] No visual glitches or layout issues when scrolling

**Implementation Note**: Test on multiple platforms (Windows, macOS, Linux) if possible, as scrollbar behavior can vary by OS. Document any platform-specific quirks discovered.

---

## Testing Strategy

### Unit Tests:
Not applicable - this is purely UI/visual testing

### Integration Tests:
Not applicable - requires manual GUI testing

### Manual Testing Steps:
1. **Initial Visibility Test**:
   - Start Thonny IDE
   - Open the Kiro plugin panel
   - Verify scrollbar is visible on the right side of terminal
   - Check scrollbar has visible contrast against black background

2. **Scrolling Function Test**:
   - Type several commands to generate output
   - Verify scrollbar thumb size adjusts based on content length
   - Click and drag scrollbar thumb
   - Verify terminal content scrolls correspondingly
   - Use mouse wheel over terminal
   - Verify scrolling works smoothly

3. **Window Resize Test**:
   - Resize the Thonny window (make it smaller)
   - Verify scrollbar remains visible and functional
   - Resize the window (make it larger)
   - Verify scrollbar still works correctly

4. **Theme Compatibility Test**:
   - Test with Thonny's light theme (if available)
   - Test with Thonny's dark theme (if available)
   - Verify scrollbar is visible in both themes
   - Check that custom styling doesn't clash with theme colors

5. **Long Output Test**:
   - Execute a command that generates long output (e.g., help text)
   - Verify scrollbar thumb becomes smaller (more content)
   - Scroll to top, middle, and bottom of output
   - Verify smooth scrolling throughout

6. **Reset Function Test**:
   - Generate some output
   - Scroll to middle of content
   - Click Reset button
   - Verify scrollbar resets to top position

7. **Auto-Scroll Test**:
   - Scroll to top of terminal
   - Execute a new command
   - Verify terminal auto-scrolls to show new output at bottom
   - Verify scrollbar position updates to reflect bottom position

## Performance Considerations

**Layout Performance**:
- Reordering pack operations (scrollbar before terminal) has no performance impact
- Pack geometry manager is efficient for this simple layout

**Style Configuration**:
- ttk.Style configuration is a one-time operation at initialization
- No runtime performance impact
- Try-except block prevents crashes with minimal overhead

**Scrolling Performance**:
- Standard ttk.Scrollbar is optimized for performance
- Text widget scrolling is efficient even with thousands of lines
- ANSI color handling (existing) is the main performance factor, not scrollbar

**Memory**:
- No additional memory usage from these changes
- Scrollbar and style objects are lightweight

**Potential Issues**:
- None expected; changes are minimal and use standard tkinter features

## Migration Notes

Not applicable - this is a bug fix, not a data migration.

**Backward Compatibility**:
- Changes are fully backward compatible
- No API changes or configuration file updates required
- Users will simply see the scrollbar after updating

**Deployment**:
- Update the plugin files
- Rebuild the package: `python -m build`
- Users install updated package via pip
- No Thonny restart required (though recommended)

## References

- Current implementation: `thonnycontrib/main.py:42-64`
- tkinter Text widget docs: https://docs.python.org/3/library/tkinter.html#tkinter.Text
- ttk Scrollbar docs: https://docs.python.org/3/library/tkinter.ttk.html#scrollbar
- ttk Style docs: https://docs.python.org/3/library/tkinter.ttk.html#tkinter.ttk.Style
- Thonny plugin development: https://github.com/thonny/thonny/wiki/Plugins
