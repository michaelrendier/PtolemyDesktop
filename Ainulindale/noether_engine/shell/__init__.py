"""
noether_engine.shell — on-shell / off-shell derivation handlers.

on_shell   : use equations of motion when verifying conservation
off_shell  : BV/cohomological formulation (session 2)
"""

from .on_shell import is_on_shell_zero

__all__ = ['is_on_shell_zero']
