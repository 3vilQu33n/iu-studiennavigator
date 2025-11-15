# utils/__init__.py
"""
Utils Package - Helper Functions & Utilities

Zentrale Exports aller Utility-Funktionen.

Usage:
    from utils import some_helper_function
"""

# ============================================================================
# UTILITIES
# ============================================================================

# Login Utilities (falls vorhanden)
try:
    from utils.login import *
except ImportError:
    pass

# Path Detection
try:
    from utils.path_detector import detect_project_root
except ImportError:
    detect_project_root = None

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    'detect_project_root',
]