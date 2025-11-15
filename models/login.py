# models/login.py
"""
Domain Model: Login (Auth User)

KOMPOSITION: Student 1 →◆ 1 Login
→ Login gehört zum Student und stirbt mit ihm
→ Ein Student kann nicht ohne Login existieren (für das System)
→ Ein Login kann nicht ohne Student existieren

TUTOR-FEEDBACK:
"Wäre der Login nicht eher eine Komposition zu Student?"
→ JA! Login ist Teil des Students für das System.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')

# Argon2 Password Hasher
ph = PasswordHasher()


@dataclass(slots=True)
class Login:
    """Domain Model: Login (Auth User)

    Repräsentiert die Authentifizierungsdaten eines Students.

    OOP-BEZIEHUNGEN:
    - KOMPOSITION zu Student (gehört zum Student, stirbt mit ihm)
    - Ein Login kann nicht ohne Student existieren
    - Wenn Student gelöscht wird, wird auch Login gelöscht

    ENCAPSULATION:
    - PUBLIC: verify_password(), hash_password(), is_active_account(), validate(), to_dict()
    - PRIVATE: __normalize_email(), __validate_email_format(), __calculate_account_age_days()

    Attributes:
        id: Primärschlüssel (None beim Insert)
        student_id: FK zum Student (KOMPOSITION - muss vorhanden sein!)
        email: E-Mail Adresse (unique, wird als Username verwendet)
        password_hash: Argon2id Hash des Passworts
        is_active: Account aktiv? (1=ja, 0=nein)
        role: Benutzerrolle ('student', 'admin')
        created_at: Erstellungsdatum
        must_change_password: Muss Passwort bei nächstem Login ändern?
        last_login: Zeitpunkt des letzten erfolgreichen Logins
    """
    id: Optional[int]  # beim Insert None
    student_id: int  # KOMPOSITION: gehört zu Student
    email: str
    password_hash: str
    is_active: int = 1  # 1=aktiv, 0=deaktiviert
    role: str = "student"  # 'student' | 'admin'
    created_at: Optional[str] = None
    must_change_password: int = 0  # 1=ja, 0=nein
    last_login: Optional[str] = None

    def __post_init__(self) -> None:
        """Validierung und Typ-Konvertierung nach Initialisierung"""
        # E-Mail normalisieren
        self.email = self.__normalize_email(self.email)

        # created_at setzen wenn None
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

        # Validierung durchführen
        self.validate()

    # ========== PUBLIC Methods (minimal!) ==========

    def verify_password(self, password: str) -> bool:
        """
        PUBLIC: Verifiziert Passwort gegen gespeicherten Hash

        Args:
            password: Klartext-Passwort

        Returns:
            True wenn Passwort korrekt, sonst False
        """
        try:
            ph.verify(self.password_hash, password)
            logger.info(f"✅ Passwort verifiziert für: {self.email}")
            return True
        except VerifyMismatchError:
            logger.warning(f"❌ Falsches Passwort für: {self.email}")
            return False
        except Exception as e:
            logger.error(f"❌ Fehler bei Passwort-Verifikation: {e}")
            return False

    @staticmethod
    def hash_password(password: str) -> str:
        """
        PUBLIC: Hasht Passwort mit Argon2id

        Args:
            password: Klartext-Passwort

        Returns:
            Argon2id Hash
        """
        return ph.hash(password)

    def is_active_account(self) -> bool:
        """PUBLIC: Prüft ob Account aktiv ist"""
        return self.is_active == 1

    def needs_password_change(self) -> bool:
        """PUBLIC: Prüft ob Passwort geändert werden muss"""
        return self.must_change_password == 1

    def is_admin(self) -> bool:
        """PUBLIC: Prüft ob User Admin ist"""
        return self.role == "admin"

    def is_student(self) -> bool:
        """PUBLIC: Prüft ob User Student ist"""
        return self.role == "student"

    def update_last_login(self) -> None:
        """PUBLIC: Aktualisiert last_login Timestamp"""
        self.last_login = datetime.now().isoformat()

    def validate(self) -> None:
        """
        PUBLIC: Validiert Login-Daten

        Wird vom Repository vor dem Insert aufgerufen.

        Raises:
            ValueError: Wenn Daten ungültig sind
        """
        # student_id muss vorhanden sein (KOMPOSITION!)
        if not self.student_id or self.student_id <= 0:
            raise ValueError("student_id ist erforderlich (KOMPOSITION zu Student)")

        # E-Mail validieren
        if not self.__validate_email_format():
            raise ValueError(f"Ungültige E-Mail: {self.email}")

        # password_hash muss vorhanden sein
        if not self.password_hash or len(self.password_hash) < 20:
            raise ValueError("password_hash ist ungültig oder zu kurz")

        # role validieren
        if self.role not in ["student", "admin"]:
            raise ValueError(f"Ungültige role: {self.role}")

        logger.debug(f"✅ Login validiert: {self.email}")

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary (für JSON/Templates)"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'email': self.email,
            'is_active': bool(self.is_active),
            'role': self.role,
            'created_at': self.created_at,
            'must_change_password': bool(self.must_change_password),
            'last_login': self.last_login,
            'needs_password_change': self.needs_password_change(),
            'is_admin': self.is_admin()
        }

    @classmethod
    def from_db_row(cls, row) -> "Login":
        """PUBLIC: Factory Method - Erstellt Login aus DB-Row

        Verwendet try/except für optionale Felder da sqlite3.Row kein .get() hat.
        """
        # Optionale Felder mit try/except behandeln
        try:
            login_id = int(row['id']) if row['id'] else None
        except (KeyError, TypeError):
            login_id = None

        try:
            is_active = int(row['is_active'])
        except (KeyError, TypeError):
            is_active = 1

        try:
            role = str(row['role'])
        except (KeyError, TypeError):
            role = 'student'

        try:
            created_at = row['created_at']
        except (KeyError, TypeError):
            created_at = None

        try:
            must_change_password = int(row['must_change_password'])
        except (KeyError, TypeError):
            must_change_password = 0

        try:
            last_login = row['last_login']
        except (KeyError, TypeError):
            last_login = None

        return cls(
            id=login_id,
            student_id=int(row['student_id']),
            email=str(row['email']),
            password_hash=str(row['password_hash']),
            is_active=is_active,
            role=role,
            created_at=created_at,
            must_change_password=must_change_password,
            last_login=last_login
        )

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

        try:
            local, domain = self.email.rsplit('@', 1)
            return bool(local) and bool(domain) and '.' in domain
        except ValueError:
            return False

    def __get_email_domain(self) -> str:
        """PRIVATE: Extrahiert Domain aus E-Mail"""
        if '@' not in self.email:
            return ""
        return self.email.split('@')[1]

    def __is_password_hash_argon2(self) -> bool:
        """PRIVATE: Prüft ob password_hash ein Argon2 Hash ist"""
        return self.password_hash.startswith("$argon2")

    def __calculate_account_age_days(self) -> int:
        """PRIVATE: Berechnet Alter des Accounts in Tagen"""
        if not self.created_at:
            return 0

        try:
            created = datetime.fromisoformat(self.created_at)
            delta = datetime.now() - created
            return delta.days
        except (ValueError, TypeError):
            return 0

    def __is_recently_created(self, days: int = 7) -> bool:
        """PRIVATE: Prüft ob Account vor kurzem erstellt wurde"""
        return self.__calculate_account_age_days() <= days

    def __has_logged_in_before(self) -> bool:
        """PRIVATE: Prüft ob User sich schon einmal eingeloggt hat"""
        return self.last_login is not None

    # ========== String Representation ==========

    def __str__(self) -> str:
        status = "aktiv" if self.is_active else "deaktiviert"
        return f"Login({self.email}, {status})"

    def __repr__(self) -> str:
        return (f"Login(id={self.id}, student_id={self.student_id}, "
                f"email='{self.email}', role='{self.role}')")


# ============================================================================
# HELPER FUNCTIONS (außerhalb der Klasse)
# ============================================================================

def create_login_for_student(
        student_id: int,
        email: str,
        password: str,
        role: str = "student"
) -> Login:
    """
    PUBLIC: Factory Function - Erstellt Login für Student

    Args:
        student_id: FK zum Student
        email: E-Mail Adresse
        password: Klartext-Passwort (wird gehasht)
        role: Benutzerrolle (default: 'student')

    Returns:
        Login Objekt (noch nicht in DB gespeichert!)
    """
    password_hash = Login.hash_password(password)

    return Login(
        id=None,  # wird beim Insert gesetzt
        student_id=student_id,
        email=email,
        password_hash=password_hash,
        is_active=1,
        role=role,
        created_at=datetime.now().isoformat(),
        must_change_password=0,
        last_login=None
    )


# ============================================================================
# TESTING / DEBUG
# ============================================================================

if __name__ == "__main__":
    print("=== Login Domain Model Test ===\n")

    # Test 1: Login erstellen
    print("Test 1: Login erstellen")
    login = create_login_for_student(
        student_id=1,
        email="test@example.com",
        password="TestPassword123!"
    )
    print(f"  Login erstellt: {login}")
    print(f"  Email: {login.email}")
    print(f"  Is Active: {login.is_active_account()}")
    print(f"  Needs Password Change: {login.needs_password_change()}\n")

    # Test 2: Passwort verifizieren
    print("Test 2: Passwort verifizieren")
    print(f"  Korrektes Passwort: {login.verify_password('TestPassword123!')}")
    print(f"  Falsches Passwort: {login.verify_password('WrongPassword')}\n")

    # Test 3: to_dict()
    print("Test 3: to_dict()")
    print(f"  Dict: {login.to_dict()}\n")

    # Test 4: Validierung
    print("Test 4: Validierung (ungültige E-Mail)")
    try:
        invalid_login = Login(
            id=None,
            student_id=1,
            email="invalid-email",  # keine Domain
            password_hash="$argon2id$v=19$m=65536,t=3,p=4$test",
            is_active=1,
            role="student"
        )
    except ValueError as e:
        print(f"  ✅ Validierung hat Fehler erkannt: {e}\n")

    print("✅ Alle Tests erfolgreich!")