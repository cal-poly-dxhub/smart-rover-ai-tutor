---
date: 2026-02-05T09:38:59+0000
researcher: Claude Sonnet 4.5
git_commit: d2b525a63952d23989919bb2578bc02ded191ed2
branch: main
repository: smart-rover-ai-tutor
topic: "Terminal Prompt Visibility Bug Investigation"
tags: [debugging, ui, tkinter, thonny-plugin]
status: complete
last_updated: 2026-02-05
last_updated_by: Claude Sonnet 4.5
type: debugging_investigation
---

# Handoff: Terminal Prompt Visibility Bug

## Task(s)

**Status: Investigation Complete, Fix Not Applied**

Investigated a UI bug where the terminal input prompt (purple `>` symbol) becomes invisible when the Kiro panel fills with content. The user reported this issue occurred at commit 18b4b9b ("Reset bug fix"), noting that it seemed intermittent and would temporarily resolve after clicking the "Reset" button.

## Critical References

- `thonnycontrib/main.py` - Main plugin implementation with terminal UI code

## Recent changes

No code changes were made during this session. This was a pure investigation/debugging session.

## Learnings

### Bug Timeline & Root Cause

The prompt visibility bug has a complex history involving multiple commits:

1. **Commit 18b4b9b** ("Reset bug fix") - Where bug was originally reported
   - At this commit, the scrollbar was packed **after** the terminal widget
   - This is a Tkinter packing order issue that can cause layout problems
   - Code had `expand=True` at thonnycontrib/main.py:49
   - Scrollbar created at lines 61-64 (after terminal initialization)

2. **Commit 419cedf** (".claude prompt setup") - Attempted fix
   - Moved scrollbar to be packed **before** the terminal widget
   - Added custom scrollbar styling
   - Added `height=20` parameter to text widget
   - Still had `expand=True` present

3. **Commit 64f2c96** ("Remove custom scrollbar styling code") - Regression introduced
   - Removed custom scrollbar styling (good)
   - **Accidentally removed `expand=True`** from thonnycontrib/main.py:57 (bad)
   - Changed from: `self.terminal.pack(side="left", fill="both", expand=True)`
   - Changed to: `self.terminal.pack(side="left", fill="both")`

4. **Current main branch** - Bug still present
   - Missing `expand=True` on line 57
   - Scrollbar properly packed before terminal (correct)
   - But terminal doesn't expand to fill space (incorrect)

### Why `expand=True` Matters

Without `expand=True`, the Text widget:
- Has a fixed height of 20 character rows (set at line 54)
- Doesn't dynamically expand to fill available vertical space
- As content grows, the prompt line gets pushed below the visible viewport
- The `self.terminal.see("end")` calls can't work properly without expansion
- Clicking "Reset" clears content, temporarily hiding the problem

### Widget Packing Order in Tkinter

The correct pattern for a scrolled text widget is:
1. Pack the scrollbar first with `side="right", fill="y"`
2. Pack the text widget second with `side="left", fill="both", expand=True`

This ensures the scrollbar gets its space allocation before the text widget expands.

## Artifacts

None - this was a pure investigation session with no documents created.

## Action Items & Next Steps

1. **Apply the fix**: Add `expand=True` back to thonnycontrib/main.py:57
   - Current: `self.terminal.pack(side="left", fill="both")`
   - Fixed: `self.terminal.pack(side="left", fill="both", expand=True)`

2. **Test the fix**:
   - Build the package: `python -m build`
   - Install in Thonny from `dist/smart_rover_ai_tutor-0.1.0-py3-none-any.whl`
   - Enter multiple prompts with long responses to fill the terminal
   - Verify the purple `>` prompt remains visible at the bottom
   - Verify it doesn't disappear as content accumulates

3. **Commit and deploy**:
   - Create commit with message like "Fix terminal prompt visibility by restoring expand=True"
   - Reference this bug investigation
   - Build and distribute updated package

## Other Notes

### How to Reproduce the Bug (Current State)

1. Install the plugin in Thonny
2. Open the Kiro panel
3. Enter multiple prompts that generate lengthy responses
4. After enough content accumulates, the input prompt disappears
5. Clicking "Reset" temporarily fixes it by clearing content

### Related Code Locations

- `thonnycontrib/main.py:34-43` - Button frame setup (Reset button)
- `thonnycontrib/main.py:42-57` - Terminal frame and widget setup
- `thonnycontrib/main.py:90-99` - `_show_prompt()` method that displays the prompt
- `thonnycontrib/main.py:106-117` - `_reset_conversation()` method

### Git Investigation Commands Used

```bash
git show 18b4b9b:thonnycontrib/main.py  # Original bug report commit
git show 64f2c96                         # Commit that introduced regression
git log --oneline --graph -15            # View commit timeline
```

### User's Testing Question

The user asked how to test the bug in the actual application. The answer:
1. Build: `python -m build`
2. Install in Thonny via Tools → Manage plugins
3. Test by filling terminal with content and observing if prompt disappears
