"""ANSI color code handler for terminal display."""

import re
from thonnycontrib.smart_rover.config.settings import AnsiColorConfig


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
