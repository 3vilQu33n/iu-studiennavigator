#!/usr/bin/env python3
# reset_password.py
"""
Passwort-Reset Tool für Dashboard

Setzt Passwort für einen Benutzer in der login Tabelle zurück.
Verwendet Argon2 Password Hashing.
"""
import sqlite3
import sys
from pathlib import Path
from argon2 import PasswordHasher

# Konfiguration
DB_PATH = Path(__file__).parent / 'dashboard.db'
ph = PasswordHasher()


def reset_password(email: str, new_password: str) -> bool:
    """
    Setzt Passwort für einen User zurück

    Args:
        email: E-Mail des Users
        new_password: Neues Passwort (Klartext)

    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    try:
        # Neuen Hash erstellen
        new_hash = ph.hash(new_password)

        with sqlite3.connect(DB_PATH) as conn:
            # Prüfe ob User existiert
            cursor = conn.execute(
                "SELECT id, email FROM login WHERE LOWER(email) = LOWER(?)",
                (email,)
            )
            user = cursor.fetchone()

            if not user:
                print(f"❌ User nicht gefunden: {email}")
                return False

            # Passwort updaten
            conn.execute(
                """UPDATE login
                   SET password_hash        = ?,
                       must_change_password = 0,
                       last_login           = NULL
                   WHERE id = ?""",
                (new_hash, user[0])
            )
            conn.commit()

            print(f"✅ Passwort erfolgreich geändert!")
            print(f"📧 E-Mail:   {user[1]}")
            print(f"🔑 Passwort: {new_password}")
            print(f"")
            print(f"ℹ️  must_change_password wurde auf 0 gesetzt")

            return True

    except sqlite3.Error as e:
        print(f"❌ Datenbankfehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def list_users():
    """Zeigt alle User in der Datenbank"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """SELECT id, email, role, is_active
                   FROM login
                   ORDER BY id"""
            )
            users = cursor.fetchall()

            if not users:
                print("Keine User gefunden!")
                return

            print("\n=== Verfügbare User ===")
            for user_id, email, role, is_active in users:
                status = "✅ aktiv" if is_active else "❌ inaktiv"
                print(f"  [{user_id}] {email} ({role}) - {status}")
            print()

    except sqlite3.Error as e:
        print(f"❌ Datenbankfehler: {e}")


def interactive_mode():
    """Interaktiver Modus"""
    print("=" * 60)
    print("  PASSWORD RESET TOOL")
    print("=" * 60)
    print()

    # Zeige verfügbare User
    list_users()

    # Eingabe
    email = input("📧 E-Mail: ").strip()
    if not email:
        print("❌ E-Mail erforderlich!")
        return

    password = input("🔑 Neues Passwort: ").strip()
    if not password:
        print("❌ Passwort erforderlich!")
        return

    # Bestätigung
    confirm = input(f"\nPasswort für '{email}' ändern? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Abgebrochen.")
        return

    print()
    reset_password(email, password)


# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

if __name__ == "__main__":
    # Prüfe DB existiert
    if not DB_PATH.exists():
        print(f"❌ Datenbank nicht gefunden: {DB_PATH}")
        sys.exit(1)

    # CLI Argumente?
    if len(sys.argv) == 3:
        # Direkt: python reset_password.py email@example.com NewPassword123!
        email = sys.argv[1]
        password = sys.argv[2]
        reset_password(email, password)
    else:
        # Interaktiv
        interactive_mode()