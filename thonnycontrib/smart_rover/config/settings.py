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
    TEXT_PADDING_X = 10
    TEXT_PADDING_Y = 10


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
    TERMINAL_PADDING_Y = (0, 0)
    SEPARATOR_LINE = "=" * 30


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
