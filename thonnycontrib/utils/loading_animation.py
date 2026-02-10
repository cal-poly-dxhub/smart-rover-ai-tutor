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
