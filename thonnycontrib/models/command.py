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
