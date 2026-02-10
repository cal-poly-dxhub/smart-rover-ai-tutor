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
