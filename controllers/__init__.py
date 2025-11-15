# controllers/__init__.py
"""
Controllers Package - Request Handler

Zentrale Exports aller Controller.

Usage:
    from controllers import AuthController, DashboardController
"""

# ============================================================================
# CONTROLLERS
# ============================================================================

try:
    from controllers.auth_controller import AuthController
except ImportError:
    AuthController = None

try:
    from controllers.dashboard_controller import DashboardController
except ImportError:
    DashboardController = None

try:
    from controllers.semester_controller import SemesterController
except ImportError:
    SemesterController = None

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    'AuthController',
    'DashboardController',
    'SemesterController',
]