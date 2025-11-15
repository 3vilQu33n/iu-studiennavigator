# controllers/auth_controller.py
"""
Authentication Controller

Verwaltet Login, Passwort-Änderung und User-Registrierung.
Verwendet die 'login' Tabelle (früher 'auth_user').
"""
import sqlite3
from typing import Dict, Any
from datetime import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from utils import password_meets_policy, generate_strong_password
import logging

logger = logging.getLogger(__name__)
ph = PasswordHasher()


class AuthController:
    """
    Controller für Authentifizierung

    Verwendet die 'login' Tabelle für User-Authentifizierung.
    Alle Passwörter werden mit Argon2id gehasht.
    """

    def __init__(self, db_path: str):
        """
        Initialisiert AuthController

        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = db_path

    def _con(self):
        """Erstellt neue Datenbankverbindung"""
        return sqlite3.connect(self.db_path)

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login mit login Tabelle

        Args:
            email: E-Mail Adresse
            password: Passwort (Klartext)

        Returns:
            Dictionary mit:
            - success: bool - Login erfolgreich?
            - user_id: int - User-ID (nur bei success=True)
            - email: str - E-Mail (nur bei success=True)
            - must_change_password: bool - Passwort muss geändert werden?
            - error: str - Fehlermeldung (nur bei success=False)
        """
        try:
            with self._con() as con:
                con.row_factory = sqlite3.Row

                # Suche nach E-Mail in login Tabelle
                row = con.execute(
                    """SELECT id, email, password_hash, is_active, must_change_password
                       FROM login
                       WHERE LOWER(email) = ?""",
                    (email.strip().lower(),)
                ).fetchone()

                if not row:
                    logger.error(f"❌ Kein login Eintrag gefunden für: {email}")
                    return {
                        'success': False,
                        'error': 'E-Mail oder Passwort ist falsch.'
                    }

                logger.info(f"✅ login Eintrag gefunden: id={row['id']}")

                # Prüfe ob Account aktiv ist
                if not row["is_active"]:
                    logger.warning(f"⚠️ Account deaktiviert: {email}")
                    return {
                        'success': False,
                        'error': 'Account ist deaktiviert.'
                    }

                # Verifiziere Passwort mit Argon2
                try:
                    ph.verify(row["password_hash"], password)
                    logger.info(f"✅ Login erfolgreich: {email}")

                    # Update last_login timestamp
                    con.execute(
                        "UPDATE login SET last_login = ? WHERE id = ?",
                        (datetime.now().isoformat(), row['id'])
                    )
                    con.commit()

                    return {
                        'success': True,
                        'user_id': row['id'],
                        'email': row['email'],
                        'must_change_password': bool(row['must_change_password'])
                    }

                except VerifyMismatchError:
                    logger.error(f"❌ Falsches Passwort für: {email}")
                    return {
                        'success': False,
                        'error': 'E-Mail oder Passwort ist falsch.'
                    }

        except (sqlite3.Error, ValueError, TypeError) as e:
            logger.exception(f"❌ Fehler beim Login: {e}")
            return {
                'success': False,
                'error': 'Ein Fehler ist aufgetreten.'
            }

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Ändert das Passwort eines Users

        Args:
            user_id: ID des Users (login.id)
            old_password: Altes Passwort (zur Verifikation)
            new_password: Neues Passwort

        Returns:
            Dictionary mit success, message oder error
        """
        try:
            with self._con() as con:
                con.row_factory = sqlite3.Row

                # Lade aktuellen password_hash aus login Tabelle
                row = con.execute(
                    "SELECT password_hash FROM login WHERE id = ?",
                    (user_id,)
                ).fetchone()

                if not row:
                    return {
                        'success': False,
                        'error': 'Benutzerkonto nicht gefunden.'
                    }

                # Verifiziere altes Passwort
                try:
                    ph.verify(row["password_hash"], old_password)
                except VerifyMismatchError:
                    return {
                        'success': False,
                        'error': 'Altes Passwort ist nicht korrekt.'
                    }

                # Prüfe ob neues Passwort Policy erfüllt
                ok, msg = password_meets_policy(new_password)
                if not ok:
                    return {
                        'success': False,
                        'error': msg
                    }

                # Hash neues Passwort und update in Datenbank
                new_hash = ph.hash(new_password)
                con.execute(
                    "UPDATE login SET password_hash = ?, must_change_password = 0 WHERE id = ?",
                    (new_hash, user_id)
                )
                con.commit()

                logger.info(f"✅ Passwort geändert für user_id={user_id}")

                return {
                    'success': True,
                    'message': 'Passwort geändert.'
                }

        except Exception as e:
            logger.exception(f"Fehler beim Passwort ändern: {e}")
            return {
                'success': False,
                'error': 'Ein Fehler ist aufgetreten.'
            }

    def register(self, email: str, password: str, student_id: int = None) -> Dict[str, Any]:
        """
        Registriert neuen User in login Tabelle

        Args:
            email: E-Mail Adresse
            password: Passwort (Klartext)
            student_id: Optional - FK zu student Tabelle

        Returns:
            Dictionary mit success, user_id, email oder error
        """
        try:
            # Prüfe Passwort Policy
            ok, msg = password_meets_policy(password)
            if not ok:
                return {
                    'success': False,
                    'error': msg
                }

            with self._con() as con:
                # Prüfe ob E-Mail bereits existiert
                exists = con.execute(
                    "SELECT 1 FROM login WHERE LOWER(email) = ?",
                    (email.strip().lower(),)
                ).fetchone()

                if exists:
                    return {
                        'success': False,
                        'error': 'E-Mail bereits registriert.'
                    }

                # Hash Passwort mit Argon2
                password_hash = ph.hash(password)

                # Insert neuen User in login Tabelle
                cur = con.execute(
                    """INSERT INTO login (student_id, email, password_hash, is_active, role,
                                          created_at, must_change_password)
                       VALUES (?, ?, ?, 1, 'student', ?, 0)""",
                    (student_id, email.strip().lower(), password_hash, datetime.now().isoformat())
                )
                con.commit()

                logger.info(f"✅ Neuer User registriert: {email} (id={cur.lastrowid})")

                return {
                    'success': True,
                    'user_id': cur.lastrowid,
                    'email': email
                }

        except Exception as e:
            logger.exception(f"Fehler bei Registrierung: {e}")
            return {
                'success': False,
                'error': 'Ein Fehler ist aufgetreten.'
            }

    def issue_initial_password(self, email: str, student_id: int = None) -> Dict[str, Any]:
        """
        Generiert Initialpasswort für Admin-Zwecke

        Wenn User existiert: Passwort zurücksetzen und must_change_password = 1
        Wenn User nicht existiert: Neuen User anlegen mit must_change_password = 1

        Args:
            email: E-Mail Adresse
            student_id: Optional - FK zu student Tabelle

        Returns:
            Dictionary mit success, password, message oder error
        """
        try:
            # Generiere sicheres Passwort
            pw = generate_strong_password(16)
            pw_hash = ph.hash(pw)

            with self._con() as con:
                # Prüfe ob User bereits existiert
                exists = con.execute(
                    "SELECT id FROM login WHERE LOWER(email) = ?",
                    (email.strip().lower(),)
                ).fetchone()

                if exists:
                    # User existiert - Passwort zurücksetzen
                    con.execute(
                        "UPDATE login SET password_hash = ?, must_change_password = 1 WHERE id = ?",
                        (pw_hash, exists[0])
                    )
                    logger.info(f"✅ Passwort zurückgesetzt für: {email}")
                else:
                    # Neuen User anlegen
                    con.execute(
                        """INSERT INTO login (student_id, email, password_hash, is_active, role,
                                              created_at, must_change_password)
                           VALUES (?, ?, ?, 1, 'student', ?, 1)""",
                        (student_id, email.strip().lower(), pw_hash, datetime.now().isoformat())
                    )
                    logger.info(f"✅ Neuer User mit Initialpasswort: {email}")

                con.commit()

                return {
                    'success': True,
                    'password': pw,
                    'message': f'Initialpasswort für {email} erstellt.'
                }

        except Exception as e:
            logger.exception(f"Fehler beim Erstellen des Initialpassworts: {e}")
            return {
                'success': False,
                'error': 'Ein Fehler ist aufgetreten.'
            }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import os

    # Test mit Beispiel-Datenbank
    test_db = "test_login.db"

    # Erstelle Test-Datenbank
    with sqlite3.connect(test_db) as con:
        con.execute("""
                    CREATE TABLE IF NOT EXISTS login
                    (
                        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id           INTEGER,
                        email                TEXT UNIQUE NOT NULL,
                        password_hash        TEXT        NOT NULL,
                        is_active            INTEGER DEFAULT 1,
                        role                 TEXT    DEFAULT 'student',
                        created_at           TEXT,
                        must_change_password INTEGER DEFAULT 0,
                        last_login           TEXT
                    )
                    """)

    print("=== AuthController Test ===\n")

    auth = AuthController(test_db)

    # Test 1: Registrierung
    print("Test 1: Registrierung")
    result = auth.register("test@example.com", "TestPassword123!")
    print(f"  Ergebnis: {result}\n")

    # Test 2: Login (korrekt)
    print("Test 2: Login (korrekt)")
    result = auth.login("test@example.com", "TestPassword123!")
    print(f"  Ergebnis: {result}\n")

    # Test 3: Login (falsches Passwort)
    print("Test 3: Login (falsches Passwort)")
    result = auth.login("test@example.com", "FalschesPasswort")
    print(f"  Ergebnis: {result}\n")

    # Test 4: Initialpasswort
    print("Test 4: Initialpasswort generieren")
    result = auth.issue_initial_password("admin@example.com")
    print(f"  Ergebnis: {result}\n")

    # Cleanup
    os.remove(test_db)
    print("✅ Test-Datenbank gelöscht")