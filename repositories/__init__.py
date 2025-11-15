# repositories/__init__.py
"""
Repositories Package - Data Access Layer

Zentrale Exports aller Repositories und DB Gateway.

Usage:
    from repositories import StudentRepository, ModulRepository, db_gateway
"""

# ============================================================================
# DATABASE GATEWAY
# ============================================================================

try:
    from repositories import db_gateway
    from repositories.db_gateway import DBGateway
except ImportError:
    db_gateway = None
    DBGateway = None

# ============================================================================
# REPOSITORIES
# ============================================================================

try:
    from repositories.student_repository import StudentRepository
except ImportError:
    StudentRepository = None

try:
    from repositories.modul_repository import ModulRepository, ModulDTO
except ImportError:
    ModulRepository = None
    ModulDTO = None

try:
    from repositories.modulbuchung_repository import ModulbuchungRepository
except ImportError:
    ModulbuchungRepository = None

try:
    from repositories.einschreibung_repository import EinschreibungRepository
except ImportError:
    EinschreibungRepository = None

try:
    from repositories.gebuehr_repository import GebuehrRepository
except ImportError:
    GebuehrRepository = None

try:
    from repositories.progress_repository import ProgressRepository
except ImportError:
    ProgressRepository = None

try:
    from repositories.pruefung_repository import PruefungRepository
except ImportError:
    PruefungRepository = None

try:
    from repositories.pruefungsanmeldung_repository import PruefungsanmeldungRepository
except ImportError:
    PruefungsanmeldungRepository = None

try:
    from repositories.pruefungstermin_repository import PruefungsterminRepository
except ImportError:
    PruefungsterminRepository = None

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # DB Gateway
    'db_gateway',
    'DBGateway',

    # Repositories
    'StudentRepository',
    'ModulRepository',
    'ModulDTO',
    'ModulbuchungRepository',
    'EinschreibungRepository',
    'GebuehrRepository',
    'ProgressRepository',
    'PruefungRepository',
    'PruefungsanmeldungRepository',
    'PruefungsterminRepository',
]