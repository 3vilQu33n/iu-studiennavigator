# repositories/student_repository.py
"""
Repository: Student

Verantwortlich für alle Datenbankoperationen mit der student Tabelle.
Trennt Domain Logic (Student Model) von Datenbankzugriff.

DB-STRUKTUR:
    CREATE TABLE student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vorname TEXT NOT NULL,
        nachname TEXT NOT NULL,
        matrikel_nr TEXT UNIQUE NOT NULL,
        login_id INTEGER UNIQUE,
        FOREIGN KEY (login_id) REFERENCES login(id)
    );

WICHTIG: sqlite3.Row hat KEINE .get() Methode!
Wir verwenden row['spalte'] mit try/except für optionale Werte.
"""
import sqlite3
import logging
from typing import Optional, List

# Import des Student Models
from models import Student

logger = logging.getLogger(__name__)


class StudentRepository:
    """
    Repository für Student-Datenbankoperationen

    Implementiert das Repository Pattern:
    - Kapselt alle DB-Operationen für Student
    - Gibt immer Student-Objekte zurück (nie rohe DB-Rows)
    - Verwendet login_id FK (KOMPOSITION zu Login) mit UNIQUE Constraint

    WICHTIG: Verwendet row['spalte'] statt row.get('spalte')
    da sqlite3.Row keine .get() Methode hat!
    """

    def __init__(self, db_path: str):
        """
        Initialisiert Repository

        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.__db_path = db_path

    def __get_connection(self) -> sqlite3.Connection:
        """PRIVATE: Erstellt DB-Verbindung mit Row Factory"""
        conn = sqlite3.connect(self.__db_path)
        conn.row_factory = sqlite3.Row  # Ermöglicht row['spalte'] Zugriff
        conn.execute("PRAGMA foreign_keys = ON")  # FK aktivieren
        return conn

    # ========== PUBLIC Methods (CRUD) ==========

    def get_by_id(self, student_id: int) -> Optional[Student]:
        """
        PUBLIC: Lädt Student anhand der ID

        Args:
            student_id: Student ID

        Returns:
            Student-Objekt oder None wenn nicht gefunden
        """
        try:
            with self.__get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM student WHERE id = ?",
                    (student_id,)
                ).fetchone()

                if row:
                    return Student.from_db_row(row)
                return None

        except sqlite3.Error as e:
            logger.error(f"DB-Fehler beim Laden student: {e}")
            return None

    def get_by_login_id(self, login_id: int) -> Optional[Student]:
        """
        PUBLIC: Lädt Student anhand der login_id (KOMPOSITION!)

        Args:
            login_id: Login ID (FK, UNIQUE)

        Returns:
            Student-Objekt oder None wenn nicht gefunden
        """
        try:
            with self.__get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM student WHERE login_id = ?",
                    (login_id,)
                ).fetchone()

                if row:
                    return Student.from_db_row(row)
                return None

        except sqlite3.Error as e:
            logger.error(f"DB-Fehler beim Laden student: {e}")
            return None

    def get_by_matrikel_nr(self, matrikel_nr: str) -> Optional[Student]:
        """
        PUBLIC: Lädt Student anhand der Matrikelnummer

        Args:
            matrikel_nr: Matrikelnummer (eindeutig)

        Returns:
            Student-Objekt oder None wenn nicht gefunden
        """
        try:
            with self.__get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM student WHERE matrikel_nr = ?",
                    (matrikel_nr,)
                ).fetchone()

                if row:
                    return Student.from_db_row(row)
                return None

        except sqlite3.Error as e:
            logger.error(f"DB-Fehler beim Laden student: {e}")
            return None

    def get_all(self) -> List[Student]:
        """
        PUBLIC: Lädt alle Studenten

        Returns:
            Liste von Student-Objekten (leer wenn keine Studenten)
        """
        try:
            with self.__get_connection() as conn:
                rows = conn.execute("SELECT * FROM student").fetchall()
                return [Student.from_db_row(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"DB-Fehler beim Laden aller students: {e}")
            return []

    def insert(self, student: Student) -> int:
        """
        PUBLIC: Legt einen neuen Studenten an

        Args:
            student: Student-Objekt (id wird ignoriert, da AUTO_INCREMENT)

        Returns:
            Die neu vergebene ID

        Raises:
            ValueError: Bei Validierungsfehlern oder UNIQUE Constraint Verletzungen
            RuntimeError: Bei anderen Datenbankfehlern
        """
        # Validierung vor dem Insert
        is_valid, error_msg = student.validate()
        if not is_valid:
            raise ValueError(error_msg)

        try:
            with self.__get_connection() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO student (vorname, nachname, matrikel_nr, login_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        student.vorname,
                        student.nachname,
                        student.matrikel_nr,
                        student.login_id
                    )
                )
                conn.commit()
                logger.info(f"✅ Student angelegt: {student.matrikel_nr} (id={cur.lastrowid})")
                return cur.lastrowid

        except sqlite3.IntegrityError as e:
            logger.error(f"Constraint-Verletzung beim Insert: {e}")
            error_str = str(e)

            if "UNIQUE constraint failed: student.matrikel_nr" in error_str:
                raise ValueError(f"Matrikelnummer {student.matrikel_nr} existiert bereits")
            elif "UNIQUE constraint failed: student.login_id" in error_str:
                raise ValueError(f"Login-ID {student.login_id} ist bereits vergeben")
            elif "FOREIGN KEY constraint failed" in error_str:
                raise ValueError(f"Login-ID {student.login_id} existiert nicht in login-Tabelle")
            else:
                raise ValueError(f"Student konnte nicht angelegt werden: {e}")

        except sqlite3.Error as e:
            logger.error(f"DB-Fehler beim Insert: {e}")
            raise RuntimeError(f"Datenbankfehler: {e}")

    def update(self, student: Student) -> bool:
        """
        PUBLIC: Aktualisiert einen Studenten

        Args:
            student: Student-Objekt mit neuen Daten (id muss gesetzt sein)

        Returns:
            True bei Erfolg

        Raises:
            ValueError: Bei Validierungsfehlern oder UNIQUE Constraint Verletzungen
        """
        # Validierung vor dem Update
        is_valid, error_msg = student.validate()
        if not is_valid:
            raise ValueError(error_msg)

        try:
            with self.__get_connection() as conn:
                conn.execute(
                    """
                    UPDATE student
                    SET vorname     = ?,
                        nachname    = ?,
                        matrikel_nr = ?,
                        login_id    = ?
                    WHERE id = ?
                    """,
                    (
                        student.vorname,
                        student.nachname,
                        student.matrikel_nr,
                        student.login_id,
                        student.id
                    )
                )
                conn.commit()
                logger.info(f"✅ Student aktualisiert: {student.matrikel_nr} (id={student.id})")
                return True

        except sqlite3.IntegrityError as e:
            logger.error(f"Constraint-Verletzung beim Update: {e}")
            error_str = str(e)

            if "UNIQUE constraint failed: student.matrikel_nr" in error_str:
                raise ValueError(f"Matrikelnummer {student.matrikel_nr} existiert bereits")
            elif "UNIQUE constraint failed: student.login_id" in error_str:
                raise ValueError(f"Login-ID {student.login_id} ist bereits vergeben")
            elif "FOREIGN KEY constraint failed" in error_str:
                raise ValueError(f"Login-ID {student.login_id} existiert nicht in login-Tabelle")
            else:
                raise ValueError(f"Student konnte nicht aktualisiert werden: {e}")

        except sqlite3.Error as e:
            logger.error(f"DB-Fehler beim Update: {e}")
            return False

    def delete(self, student_id: int) -> bool:
        """
        PUBLIC: Löscht einen Studenten

        Args:
            student_id: ID des zu löschenden Students

        Returns:
            True bei Erfolg, False bei Fehler

        Note:
            Durch ON DELETE CASCADE in login-Tabelle wird der Login automatisch gelöscht
        """
        try:
            with self.__get_connection() as conn:
                conn.execute("DELETE FROM student WHERE id = ?", (student_id,))
                conn.commit()
                logger.info(f"✅ Student gelöscht: id={student_id}")
                return True

        except sqlite3.Error as e:
            logger.error(f"DB-Fehler beim Löschen: {e}")
            return False

    def exists(self, matrikel_nr: str) -> bool:
        """
        PUBLIC: Prüft ob Student mit Matrikelnummer existiert

        Args:
            matrikel_nr: Matrikelnummer

        Returns:
            True wenn Student existiert, sonst False
        """
        try:
            with self.__get_connection() as conn:
                row = conn.execute(
                    "SELECT 1 FROM student WHERE matrikel_nr = ?",
                    (matrikel_nr,)
                ).fetchone()
                return row is not None

        except sqlite3.Error as e:
            logger.error(f"DB-Fehler beim Prüfen: {e}")
            return False


# ============================================================================
# TESTING / BEISPIEL-VERWENDUNG
# ============================================================================

if __name__ == "__main__":
    print("=== StudentRepository Test ===\n")

    # Test mit Beispiel-Datenbank
    test_db = "test_students.db"

    # Erstelle Test-Datenbank mit korrektem Schema
    with sqlite3.connect(test_db) as con:
        con.execute("PRAGMA foreign_keys = ON")

        # Login-Tabelle zuerst (wegen FK)
        con.execute("""
            CREATE TABLE IF NOT EXISTS login (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        """)

        # Test-Login einfügen
        con.execute("INSERT INTO login (id) VALUES (1)")

        # Student-Tabelle (mit UNIQUE constraint auf login_id!)
        con.execute("""
            CREATE TABLE IF NOT EXISTS student(
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                vorname     TEXT        NOT NULL,
                nachname    TEXT        NOT NULL,
                matrikel_nr TEXT UNIQUE NOT NULL,
                login_id    INTEGER UNIQUE,
                FOREIGN KEY (login_id) REFERENCES login (id)
            )
        """)
        con.commit()

    repo = StudentRepository(test_db)

    # Test 1: Student erstellen und einfügen
    print("Test 1: Student einfügen")
    student = Student(
        id=0,  # wird ignoriert
        matrikel_nr="IU12345678",
        vorname="Max",
        nachname="Mustermann",
        login_id=1
    )

    student_id = repo.insert(student)
    print(f"  ✅ Student angelegt mit ID: {student_id}\n")

    # Test 2: Student laden (by ID)
    print("Test 2: Student laden (by ID)")
    loaded = repo.get_by_id(student_id)
    print(f"  Geladen: {loaded}\n")

    # Test 3: Student laden (by login_id)
    print("Test 3: Student laden (by login_id)")
    loaded_by_login = repo.get_by_login_id(1)
    print(f"  Geladen: {loaded_by_login}\n")

    # Test 4: Student laden (by matrikel_nr)
    print("Test 4: Student laden (by matrikel_nr)")
    loaded_by_matrikel = repo.get_by_matrikel_nr("IU12345678")
    print(f"  Geladen: {loaded_by_matrikel}\n")

    # Test 5: Alle Studenten laden
    print("Test 5: Alle Studenten laden")
    all_students = repo.get_all()
    print(f"  Anzahl: {len(all_students)}\n")

    # Test 6: Student aktualisieren
    print("Test 6: Student aktualisieren")
    student.vorname = "Maximilian"
    student.id = student_id
    success = repo.update(student)
    print(f"  Update erfolgreich: {success}\n")

    # Test 7: Existenz prüfen
    print("Test 7: Existenz prüfen")
    exists = repo.exists("IU12345678")
    print(f"  Student existiert: {exists}\n")

    # Cleanup
    import os
    os.remove(test_db)
    print("✅ Test-Datenbank gelöscht")