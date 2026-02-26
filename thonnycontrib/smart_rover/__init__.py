"""Smart Rover AI Tutor plugin for Thonny."""

__version__ = "0.1.0"
"""Kiro plugin for Thonny IDE."""

from thonny import get_workbench
from thonnycontrib.smart_rover.gui.dock_view import KiroDockView


def load_plugin():
    """
    Called by Thonny at startup.
    Registers the Kiro dockable view with Thonny workbench.
    """
    wb = get_workbench()
    wb.add_view(
        KiroDockView,
        "Kiro",
        "se",
        visible_by_default=True,
    )