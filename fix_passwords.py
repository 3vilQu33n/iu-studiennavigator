#!/usr/bin/env python3
# fix_passwords.py
"""
Setzt Passwörter für alle User in der login Tabelle zurück

Verwendet Argon2id für sicheres Password-Hashing.
Alle User bekommen das gleiche Passwort: Ignatzek123!
"""
import sqlite3
from argon2 import PasswordHasher

# Datenbank-Pfad
DB_PATH = 'dashboard.db'

# Passwort für alle User
PASSWORD = 'Ignatzek123!'

# Argon2 Password Hasher
ph = PasswordHasher()


def fix_all_passwords():
    """Setzt Passwörter für alle User zurück"""
    try:
        # Passwort hashen
        password_hash = ph.hash(PASSWORD)

        print(f"🔐 Generierter Hash: {password_hash[:50]}...")
        print(f"🔐 Hash-Länge: {len(password_hash)}")

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row

            # Hole alle User
            users = conn.execute("SELECT id, email FROM login").fetchall()

            if not users:
                print("❌ Keine User in der Datenbank gefunden!")
                return

            print(f"\n📋 Gefunden: {len(users)} User\n")

            # Update alle User mit neuem Hash
            # Benedikt (id=2) muss NICHT ändern (zum Testen)
            # Alle anderen müssen Passwort ändern
            updated = 0
            for user in users:
                must_change = 0 if user['id'] == 2 else 1

                conn.execute(
                    """UPDATE login
                       SET password_hash        = ?,
                           must_change_password = ?,
                           is_active            = 1
                       WHERE id = ?""",
                    (password_hash, must_change, user['id'])
                )
                status = "kann direkt einloggen" if user['id'] == 2 else "muss Passwort ändern"
                print(f"✅ Passwort gesetzt für: {user['email']} ({status})")
                updated += 1

            conn.commit()

            print(f"\n✅ {updated} User aktualisiert")
            print(f"📧 E-Mails: *.ignatzek@study.ignatzek.org")
            print(f"🔑 Passwort: {PASSWORD}")

            # Verifikation
            print(f"\n🔍 Verifikation...")
            for user in users:
                row = conn.execute(
                    "SELECT password_hash FROM login WHERE id = ?",
                    (user['id'],)
                ).fetchone()

                try:
                    ph.verify(row['password_hash'], PASSWORD)
                    print(f"  ✅ {user['email']}: Hash ist korrekt")
                except Exception as e:
                    print(f"  ❌ {user['email']}: Hash ist FALSCH! ({e})")

    except Exception as e:
        print(f"❌ Fehler: {e}")
        raise


if __name__ == '__main__':
    fix_all_passwords()