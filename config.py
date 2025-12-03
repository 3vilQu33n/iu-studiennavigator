# config.py
"""
Zentrale Projekt-Konfiguration

Gemeinsame Imports und Konstanten für ALLE Python-Dateien im Projekt.
Verhindert wiederholte Imports in jeder Datei.

Usage in beliebiger Python-Datei:
    from config import *

    # Jetzt sind alle Standard-Imports verfügbar:
    s = Student(...)
    repo = StudentRepository(...)
"""

# ============================================================================
# STANDARD LIBRARY IMPORTS
# ============================================================================

import sys
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Tuple, Any
import logging

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

from dotenv import load_dotenv

# Lade .env Datei
load_dotenv()

# ============================================================================
# PROJECT ROOT SETUP
# ============================================================================

# Automatisch Project Root zum Python Path hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================================
# THIRD-PARTY IMPORTS
# ============================================================================

try:
    import flask
    from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
    from flask_login import LoginManager, login_required, current_user, login_user, logout_user
    from flask_mail import Mail, Message
except ImportError as e:
    flask = None
    print(f"Warning: Flask imports failed: {e}")

try:
    import sqlite3
except ImportError:
    sqlite3 = None

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
except ImportError:
    PasswordHasher = None
    VerifyMismatchError = None

# ============================================================================
# DOMAIN MODELS
# ============================================================================

from models import (
    Student,
    Modul,
    ModulBuchung,
    Modulbuchung,
    Pruefungsleistung,
    Gebuehr,
    Einschreibung,
    Progress,
    Studiengang,
    StudiengangModul,
)

# ============================================================================
# REPOSITORIES
# ============================================================================

from repositories import (
    db_gateway,
    StudentRepository,
    ModulRepository,
    ModulDTO,
    ModulbuchungRepository,
    EinschreibungRepository,
    GebuehrRepository,
    ProgressRepository,
)

# ============================================================================
# CONTROLLERS
# ============================================================================

from controllers import (
    AuthController,
    DashboardController,
    SemesterController,
)

# ============================================================================
# CONSTANTS FROM ENVIRONMENT
# ============================================================================

# Database
DB_PATH = PROJECT_ROOT / os.getenv('DB_PATH', 'data/dashboard.db')
TEST_DB_PATH = PROJECT_ROOT / "test.db"

# Flask Secret Key
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# E-Mail Configuration
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.strato.de')
MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'True') == 'True'
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False') == 'True'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'Studiennavigator <noreply@study.ignatzek.org>')

# App Config
DEBUG = True
TESTING = False

# Logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'


# ============================================================================
# CONFIGURATION CLASSES
# ============================================================================

class Config:
    """Base configuration"""
    SECRET_KEY = SECRET_KEY

    # Database
    DB_PATH = DB_PATH

    # Session
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Mail
    MAIL_SERVER = MAIL_SERVER
    MAIL_PORT = MAIL_PORT
    MAIL_USE_SSL = MAIL_USE_SSL
    MAIL_USE_TLS = MAIL_USE_TLS
    MAIL_USERNAME = MAIL_USERNAME
    MAIL_PASSWORD = MAIL_PASSWORD
    MAIL_DEFAULT_SENDER = MAIL_DEFAULT_SENDER

    # Logging
    LOG_LEVEL = LOG_LEVEL


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # HTTPS only


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(level=LOG_LEVEL):
    """Konfiguriert Logging für das Projekt"""
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
        ]
    )
    return logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """Gibt einen Logger mit dem gegebenen Namen zurück"""
    return logging.getLogger(name)


def validate_env_vars():
    """Validiert dass alle kritischen Environment Variables gesetzt sind"""
    missing = []

    if not SECRET_KEY or SECRET_KEY == 'dev-secret-key-change-in-production':
        missing.append('SECRET_KEY')

    if not MAIL_USERNAME:
        missing.append('MAIL_USERNAME')

    if not MAIL_PASSWORD:
        missing.append('MAIL_PASSWORD')

    if missing:
        logger = get_logger(__name__)
        logger.warning(f"⚠️  Fehlende Environment Variables: {', '.join(missing)}")
        logger.warning("⚠️  Bitte .env Datei erstellen und ausfüllen!")
        logger.warning("⚠️  Template: .env.example")
        return False

    return True


# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # Standard Library
    'Path',
    'date',
    'datetime',
    'timedelta',
    'Decimal',
    'Optional',
    'List',
    'Dict',
    'Tuple',
    'Any',
    'logging',
    'os',

    # Project
    'PROJECT_ROOT',

    # Third-Party
    'Flask',
    'render_template',
    'request',
    'redirect',
    'url_for',
    'session',
    'jsonify',
    'flash',
    'LoginManager',
    'login_required',
    'current_user',
    'login_user',
    'logout_user',
    'Mail',
    'Message',
    'sqlite3',
    'PasswordHasher',
    'VerifyMismatchError',

    # Models
    'Student',
    'Modul',
    'ModulBuchung',
    'Modulbuchung',
    'Pruefungsleistung',
    'Gebuehr',
    'Einschreibung',
    'Progress',
    'Studiengang',
    'StudiengangModul',

    # Repositories
    'db_gateway',
    'StudentRepository',
    'ModulRepository',
    'ModulDTO',
    'ModulbuchungRepository',
    'EinschreibungRepository',
    'GebuehrRepository',
    'ProgressRepository',

    # Controllers
    'AuthController',
    'DashboardController',
    'SemesterController',

    # Configuration
    'Config',
    'DevelopmentConfig',
    'ProductionConfig',

    # Constants
    'DB_PATH',
    'TEST_DB_PATH',
    'SECRET_KEY',
    'MAIL_SERVER',
    'MAIL_PORT',
    'MAIL_USE_SSL',
    'MAIL_USE_TLS',
    'MAIL_USERNAME',
    'MAIL_PASSWORD',
    'MAIL_DEFAULT_SENDER',
    'DEBUG',
    'TESTING',

    # Functions
    'setup_logging',
    'get_logger',
    'validate_env_vars',
]