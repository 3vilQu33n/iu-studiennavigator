# utils/login.py
"""
Login-Utilities: User-Klasse für Flask-Login und Passwort-Management

WICHTIG: Diese Datei ist ein UTILITY für Flask-Login!
Sie ist NICHT das Domain Model (das ist in models/login.py)
"""
import re
import secrets
import string
import sqlite3
from typing import Tuple, Optional
from flask_login import UserMixin


# ============================================================================
# FLASK-LOGIN USER CLASS
# ============================================================================

class User(UserMixin):
    """
    User-Klasse für Flask-Login

    Implementiert UserMixin für Flask-Login Integration.
    Lädt User-Daten aus der 'login' Tabelle.

    WICHTIG: Verwendet die 'login' Tabelle (nicht 'auth_user')
             Verwendet 'email' als Identifier (nicht 'benutzername')

    ENCAPSULATION:
    - PUBLIC: get(), get_by_email(), get_id()
    - PRIVATE: __validate_email(), __normalize_email()
    """

    def __init__(self, id: int, email: str):
        """
        Initialisiert User-Objekt

        Args:
            id: User-ID aus Datenbank (login.id)
            email: E-Mail Adresse des Users
        """
        self.id = id
        self.email = self.__normalize_email(email)

    @staticmethod
    def get(user_id: int, db_path: str) -> Optional['User']:
        """
        Lädt User aus Datenbank (login Tabelle)

        Args:
            user_id: ID des Users
            db_path: Pfad zur SQLite-Datenbank

        Returns:
            User-Objekt oder None wenn nicht gefunden
        """
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row

                row = conn.execute(
                    "SELECT id, email FROM login WHERE id = ?",
                    (user_id,)
                ).fetchone()

                if row:
                    return User(
                        id=int(row['id']),
                        email=str(row['email'])
                    )

                return None

        except sqlite3.Error as e:
            print(f"Datenbankfehler beim Laden des Users: {e}")
            return None
        except Exception as e:
            print(f"Fehler beim Laden des Users: {e}")
            return None

    @staticmethod
    def get_by_email(email: str, db_path: str) -> Optional['User']:
        """
        Lädt User anhand der E-Mail Adresse

        Args:
            email: E-Mail Adresse
            db_path: Pfad zur SQLite-Datenbank

        Returns:
            User-Objekt oder None wenn nicht gefunden
        """
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row

                row = conn.execute(
                    "SELECT id, email FROM login WHERE LOWER(email) = LOWER(?)",
                    (email,)
                ).fetchone()

                if row:
                    return User(
                        id=int(row['id']),
                        email=str(row['email'])
                    )

                return None

        except sqlite3.Error as e:
            print(f"Datenbankfehler beim Laden des Users: {e}")
            return None
        except Exception as e:
            print(f"Fehler beim Laden des Users: {e}")
            return None

    def get_id(self) -> str:
        """
        Gibt User-ID als String zurück (für Flask-Login)

        Returns:
            User-ID als String
        """
        return str(self.id)

    # ========== PRIVATE Helper Methods ==========

    def __normalize_email(self, email: str) -> str:
        """PRIVATE: Normalisiert E-Mail (lowercase, stripped)"""
        if not isinstance(email, str):
            return ""
        return email.strip().lower()

    def __validate_email_format(self) -> bool:
        """PRIVATE: Prüft ob E-Mail Format gültig ist"""
        if not self.email or '@' not in self.email:
            return False
        local, domain = self.email.rsplit('@', 1)
        return bool(local) and bool(domain) and '.' in domain

    # ========== String Representation ==========

    def __repr__(self) -> str:
        """String-Repräsentation für Debugging"""
        return f"<User id={self.id} email='{self.email}'>"

    def __str__(self) -> str:
        """User-freundliche String-Repräsentation"""
        return self.email


# ============================================================================
# PASSWORT-POLICY
# ============================================================================

PASSWORD_MIN_LENGTH = 12


def password_meets_policy(pw: str) -> Tuple[bool, str]:
    """
    Prüft ob Passwort den Sicherheitsanforderungen entspricht

    PUBLIC FUNCTION (wird von außen aufgerufen)

    Anforderungen:
    - Mindestens PASSWORD_MIN_LENGTH Zeichen (Standard: 12)
    - Mindestens ein Kleinbuchstabe
    - Mindestens ein Großbuchstabe
    - Mindestens eine Ziffer
    - Mindestens ein Sonderzeichen

    Args:
        pw: Zu prüfendes Passwort

    Returns:
        Tuple (erfüllt: bool, fehlermeldung: str)
        - (True, "") wenn alle Anforderungen erfüllt
        - (False, "Fehlertext") wenn Anforderungen nicht erfüllt
    """
    if not isinstance(pw, str):
        return False, "Ungültiger Passwort-Typ."

    problems = []

    # Länge prüfen
    if not __check_password_length(pw):
        problems.append(f"mindestens {PASSWORD_MIN_LENGTH} Zeichen")

    # Kleinbuchstabe prüfen
    if not __has_lowercase(pw):
        problems.append("mindestens ein Kleinbuchstabe")

    # Großbuchstabe prüfen
    if not __has_uppercase(pw):
        problems.append("mindestens ein Großbuchstabe")

    # Ziffer prüfen
    if not __has_digit(pw):
        problems.append("mindestens eine Ziffer")

    # Sonderzeichen prüfen
    if not __has_special_char(pw):
        problems.append("mindestens ein Sonderzeichen")

    if problems:
        error_msg = "Passwortanforderungen nicht erfüllt: " + ", ".join(problems) + "."
        return False, error_msg

    return True, ""


# ============================================================================
# PRIVATE PASSWORD VALIDATION HELPERS
# ============================================================================

def __check_password_length(pw: str) -> bool:
    """PRIVATE: Prüft Passwort-Länge"""
    return len(pw) >= PASSWORD_MIN_LENGTH


def __has_lowercase(pw: str) -> bool:
    """PRIVATE: Prüft auf Kleinbuchstaben"""
    return bool(re.search(r"[a-z]", pw))


def __has_uppercase(pw: str) -> bool:
    """PRIVATE: Prüft auf Großbuchstaben"""
    return bool(re.search(r"[A-Z]", pw))


def __has_digit(pw: str) -> bool:
    """PRIVATE: Prüft auf Ziffern"""
    return bool(re.search(r"\d", pw))


def __has_special_char(pw: str) -> bool:
    """PRIVATE: Prüft auf Sonderzeichen"""
    return bool(re.search(r"[^A-Za-z0-9]", pw))


# ============================================================================
# PASSWORT-GENERATOR
# ============================================================================

# Zeichen-Pools für Passwort-Generierung
_LO = string.ascii_lowercase  # a-z
_UP = string.ascii_uppercase  # A-Z
_DI = string.digits  # 0-9
_SP = "!@#$%^&*()-_=+[]{};:,.?/"  # Sonderzeichen


def generate_strong_password(length: int = 16) -> str:
    """
    Generiert ein kryptographisch sicheres Passwort

    PUBLIC FUNCTION (wird von außen aufgerufen)

    Das Passwort enthält garantiert mindestens:
    - Ein Zeichen aus jeder Kategorie (Kleinbuchstabe, Großbuchstabe, Ziffer, Sonderzeichen)
    - Wird mit Fisher-Yates Shuffle gemischt
    - Verwendet secrets-Modul für kryptographische Sicherheit

    Args:
        length: Gewünschte Passwortlänge (mindestens PASSWORD_MIN_LENGTH)

    Returns:
        Sicheres Passwort als String

    Example:
        >>> pw = generate_strong_password(16)
        >>> print(len(pw))
        16
        >>> password_meets_policy(pw)
        (True, '')
    """
    # Mindestlänge sicherstellen
    length = max(length, PASSWORD_MIN_LENGTH)

    # Starte mit mindestens einem Zeichen aus jeder Kategorie
    chars = __generate_required_chars()

    # Rest der Länge mit zufälligen Zeichen auffüllen
    chars += __generate_random_chars(length - 4)

    # Sicher mischen mit Fisher-Yates Shuffle
    __shuffle_chars(chars)

    return "".join(chars)


# ============================================================================
# PRIVATE PASSWORD GENERATION HELPERS
# ============================================================================

def __generate_required_chars() -> list:
    """PRIVATE: Generiert Pflichtzeichen (1x jede Kategorie)"""
    return [
        secrets.choice(_LO),  # Kleinbuchstabe
        secrets.choice(_UP),  # Großbuchstabe
        secrets.choice(_DI),  # Ziffer
        secrets.choice(_SP)  # Sonderzeichen
    ]


def __generate_random_chars(count: int) -> list:
    """PRIVATE: Generiert zufällige Zeichen aus allen Kategorien"""
    pool = _LO + _UP + _DI + _SP
    return [secrets.choice(pool) for _ in range(count)]


def __shuffle_chars(chars: list) -> None:
    """PRIVATE: Mischt Zeichen mit Fisher-Yates Shuffle (in-place)"""
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validiert eine E-Mail Adresse (einfache Prüfung)

    PUBLIC FUNCTION (wird von außen aufgerufen)

    Regeln:
    - Muss @ enthalten
    - Muss . nach @ enthalten
    - Mindestens 5 Zeichen

    Args:
        email: Zu validierende E-Mail

    Returns:
        Tuple (valid: bool, error_message: str)
    """
    if not isinstance(email, str):
        return False, "Ungültiger E-Mail-Typ"

    email = email.strip()

    if not __check_min_email_length(email):
        return False, "E-Mail zu kurz"

    if not __has_at_symbol(email):
        return False, "E-Mail muss @ enthalten"

    local, domain = email.rsplit('@', 1)

    if not __has_local_and_domain(local, domain):
        return False, "Ungültige E-Mail Format"

    if not __domain_has_dot(domain):
        return False, "Domain muss . enthalten"

    if not __matches_email_pattern(email):
        return False, "Ungültiges E-Mail Format"

    return True, ""


# ============================================================================
# PRIVATE EMAIL VALIDATION HELPERS
# ============================================================================

def __check_min_email_length(email: str) -> bool:
    """PRIVATE: Prüft Mindestlänge"""
    return len(email) >= 5


def __has_at_symbol(email: str) -> bool:
    """PRIVATE: Prüft ob @ vorhanden ist"""
    return '@' in email


def __has_local_and_domain(local: str, domain: str) -> bool:
    """PRIVATE: Prüft ob Local-Part und Domain vorhanden sind"""
    return bool(local) and bool(domain)


def __domain_has_dot(domain: str) -> bool:
    """PRIVATE: Prüft ob Domain einen Punkt enthält"""
    return '.' in domain


def __matches_email_pattern(email: str) -> bool:
    """PRIVATE: Prüft ob E-Mail dem Regex-Pattern entspricht"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# ============================================================================
# TESTING / DEBUG
# ============================================================================

if __name__ == "__main__":
    # Test Passwort-Generierung
    print("=== Passwort-Generator Test ===")
    pw = generate_strong_password(16)
    print(f"Generiertes Passwort: {pw}")
    print(f"Länge: {len(pw)}")

    valid, msg = password_meets_policy(pw)
    print(f"Policy erfüllt: {valid}")
    if not valid:
        print(f"Fehler: {msg}")

    # Test E-Mail-Validierung
    print("\n=== E-Mail-Validierung Test ===")
    test_emails = [
        "alice@example.com",
        "bob.smith@company.co.uk",
        "test+tag@domain.org",
        "invalid",  # kein @
        "@domain.com",  # kein local part
        "user@",  # keine domain
        "user@domain",  # kein . in domain
    ]

    for email in test_emails:
        valid, msg = validate_email(email)
        status = "✓" if valid else "✗"
        print(f"{status} '{email}': {msg if not valid else 'OK'}")