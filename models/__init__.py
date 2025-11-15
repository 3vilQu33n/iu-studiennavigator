# models/__init__.py
"""
Models Package - Domain Models

Zentrale Exports aller Domain Models.
Ermöglicht einfacheren Import in ALLEN Python-Dateien des Projekts.

Usage:
    from models import Student, Modul, Einschreibung

    # Statt:
    # from models.student import Student
    # from models.modul import Modul
    # from models.einschreibung import Einschreibung
"""

# ============================================================================
# DOMAIN MODELS
# ============================================================================

from models.student import Student
from models.modul import Modul, ModulBuchung
from models.modulbuchung import Modulbuchung
from models.pruefungsleistung import Pruefungsleistung
from models.pruefungstermin import Pruefungstermin
from models.pruefungsanmeldung import Pruefungsanmeldung
from models.gebuehr import Gebuehr
from models.einschreibung import (
    Einschreibung,
    Status,  # ← NEU!
    EinschreibungError,
    ValidationError,
    DatabaseError,
    NotFoundError
)
from models.progress import Progress
from models.studiengang import Studiengang
from models.studiengang_modul import StudiengangModul

# Falls du Login-Model hast:
try:
    from models.login import Login, create_login_for_student, ph
except ImportError:
    Login = None
    create_login_for_student = None
    ph = None

# ============================================================================
# PACKAGE METADATA
# ============================================================================

__version__ = "1.0.0"
__author__ = "Dashboard Project Team"

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # Domain Models
    'Student',
    'Modul',
    'ModulBuchung',
    'Modulbuchung',
    'Pruefungsleistung',
    'Pruefungstermin',
    'Pruefungsanmeldung',
    'Gebuehr',
    'Einschreibung',
    'Progress',
    'Studiengang',
    'StudiengangModul',

    # Type Aliases
    'Status',

    # Exceptions
    'EinschreibungError',
    'ValidationError',
    'DatabaseError',
    'NotFoundError',

    # Login (optional)
    'Login',
    'create_login_for_student',
    'ph',
]