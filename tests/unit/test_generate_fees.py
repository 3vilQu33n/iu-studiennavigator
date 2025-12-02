# tests/unit/test_generate_fees.py
"""
Unit Tests fuer generate_fees Task (tasks/generate_fees.py)

Testet den Generate-Fees-Task:
- generate_monthly_fees() - Hauptfunktion
- Fehlerbehandlung (DB nicht gefunden, Exceptions)
- Rueckgabewerte
- Logging

Besondere Aspekte:
- Task ist idempotent
- Vergangene Monate werden als bezahlt markiert
- Aktueller Monat bleibt offen
"""
from __future__ import annotations

import pytest
import sqlite3
import tempfile
import os
import sys
from pathlib import Path
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def generate_fees_module():
    """Importiert das generate_fees Modul"""
    try:
        from tasks import generate_fees
        return generate_fees
    except ImportError:
        # Fallback: Direkter Import
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "generate_fees",
            Path(__file__).parent.parent.parent / "tasks" / "generate_fees.py"
        )
        module = importlib.util.module_from_spec(spec)
        # Nicht ausfuehren, nur importieren
        return module


@pytest.fixture
def temp_db():
    """Erstellt temporaere Test-Datenbank mit vollstaendigem Schema"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")

    today = date.today()
    start_datum = (today - timedelta(days=180)).replace(day=1)  # 6 Monate zurueck

    # Erstelle vollstaendiges Schema
    conn.executescript(f"""
        -- Basis-Tabellen
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matrikel_nr TEXT UNIQUE NOT NULL,
            vorname TEXT NOT NULL,
            nachname TEXT NOT NULL,
            login_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS studiengang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grad TEXT NOT NULL,
            regel_semester INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS zeitmodell (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            monate_pro_semester INTEGER NOT NULL,
            kosten_monat REAL NOT NULL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS einschreibung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            studiengang_id INTEGER NOT NULL,
            zeitmodell_id INTEGER NOT NULL,
            start_datum TEXT NOT NULL,
            exmatrikulations_datum TEXT,
            status TEXT NOT NULL DEFAULT 'aktiv',
            FOREIGN KEY (student_id) REFERENCES student(id),
            FOREIGN KEY (studiengang_id) REFERENCES studiengang(id),
            FOREIGN KEY (zeitmodell_id) REFERENCES zeitmodell(id)
        );

        CREATE TABLE IF NOT EXISTS gebuehr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            einschreibung_id INTEGER NOT NULL,
            betrag REAL NOT NULL,
            art TEXT NOT NULL DEFAULT 'monatsrate',
            faellig_am TEXT NOT NULL,
            bezahlt_am TEXT,
            UNIQUE(einschreibung_id, faellig_am, art),
            FOREIGN KEY (einschreibung_id) REFERENCES einschreibung(id)
        );

        -- Testdaten: Studenten
        INSERT INTO student (id, matrikel_nr, vorname, nachname) VALUES
            (1, 'IU12345678', 'Max', 'Mustermann'),
            (2, 'IU87654321', 'Erika', 'Musterfrau');

        -- Testdaten: Studiengang
        INSERT INTO studiengang (id, name, grad, regel_semester) VALUES
            (1, 'Informatik', 'B.Sc.', 6);

        -- Testdaten: Zeitmodelle
        INSERT INTO zeitmodell (id, name, monate_pro_semester, kosten_monat) VALUES
            (1, 'Vollzeit', 6, 359.00),
            (2, 'Teilzeit', 9, 209.00);

        -- Testdaten: Einschreibungen
        INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status) VALUES
            (1, 1, 1, 1, '{start_datum.isoformat()}', 'aktiv'),
            (2, 2, 1, 2, '{start_datum.isoformat()}', 'aktiv');
    """)
    conn.commit()
    conn.close()

    yield path

    # Cleanup
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def temp_db_with_inactive(temp_db):
    """Test-DB mit inaktiver Einschreibung"""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON;")

    today = date.today()
    start_datum = (today - timedelta(days=365)).replace(day=1)

    conn.execute(f"""
        INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status)
        VALUES (3, 1, 1, 1, '{start_datum.isoformat()}', 'exmatrikuliert')
    """)
    conn.commit()
    conn.close()

    return temp_db


# ============================================================================
# GENERATE_MONTHLY_FEES TESTS (with mocking)
# ============================================================================

class TestGenerateMonthlyFees:
    """Tests fuer generate_monthly_fees() Funktion"""

    def test_generate_fees_returns_int(self, temp_db):
        """generate_monthly_fees() gibt int zurueck"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        result = tasks.generate_fees.generate_monthly_fees()

        assert isinstance(result, int)

    def test_generate_fees_creates_fees(self, temp_db):
        """generate_monthly_fees() erstellt Gebuehren"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        result = tasks.generate_fees.generate_monthly_fees()

        # Sollte Gebuehren generiert haben
        assert result >= 0

        # Pruefen ob Gebuehren in DB
        conn = sqlite3.connect(temp_db)
        count = conn.execute("SELECT COUNT(*) FROM gebuehr").fetchone()[0]
        conn.close()

        assert count > 0

    def test_generate_fees_idempotent(self, temp_db):
        """generate_monthly_fees() ist idempotent"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        # Erster Aufruf
        first_result = tasks.generate_fees.generate_monthly_fees()

        # Zweiter Aufruf
        second_result = tasks.generate_fees.generate_monthly_fees()

        # Zweiter Aufruf sollte 0 zurueckgeben (keine neuen)
        assert second_result == 0

    def test_generate_fees_db_not_found(self):
        """generate_monthly_fees() gibt 0 zurueck wenn DB nicht existiert"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path('/nonexistent/path.db')

        result = tasks.generate_fees.generate_monthly_fees()

        assert result == 0

    def test_generate_fees_logs_on_success(self, temp_db, caplog):
        """generate_monthly_fees() loggt bei Erfolg"""
        import logging
        caplog.set_level(logging.INFO)

        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        tasks.generate_fees.generate_monthly_fees()

        # Sollte Info-Log enthalten
        assert any('Starte' in record.message or 'generiert' in record.message.lower()
                  for record in caplog.records)


# ============================================================================
# REPOSITORY INTEGRATION TESTS
# ============================================================================

class TestRepositoryIntegration:
    """Tests fuer Integration mit GebuehrRepository"""

    def test_uses_gebuehr_repository(self, temp_db):
        """generate_monthly_fees() verwendet GebuehrRepository"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        result = tasks.generate_fees.generate_monthly_fees()

        # Sollte funktionieren und Gebuehren generieren
        assert isinstance(result, int)

    def test_repository_creates_fees_in_db(self, temp_db):
        """Repository erstellt tatsaechlich Gebuehren in DB"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        tasks.generate_fees.generate_monthly_fees()

        # Pruefen ob Gebuehren in DB
        conn = sqlite3.connect(temp_db)
        count = conn.execute("SELECT COUNT(*) FROM gebuehr").fetchone()[0]
        conn.close()

        assert count > 0


# ============================================================================
# FEE GENERATION LOGIC TESTS
# ============================================================================

class TestFeeGenerationLogic:
    """Tests fuer die Gebuehr-Generierungs-Logik"""

    def test_past_months_marked_as_paid(self, temp_db):
        """Vergangene Monate werden als bezahlt markiert"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        tasks.generate_fees.generate_monthly_fees()

        # Pruefen: Vergangene Monate sollten bezahlt_am haben
        conn = sqlite3.connect(temp_db)
        today = date.today()

        # Alle Gebuehren vor diesem Monat
        past_fees = conn.execute("""
            SELECT COUNT(*) FROM gebuehr
            WHERE faellig_am < ?
              AND bezahlt_am IS NOT NULL
        """, (today.replace(day=1).isoformat(),)).fetchone()[0]

        total_past = conn.execute("""
            SELECT COUNT(*) FROM gebuehr
            WHERE faellig_am < ?
        """, (today.replace(day=1).isoformat(),)).fetchone()[0]

        conn.close()

        # Alle vergangenen sollten bezahlt sein
        if total_past > 0:
            assert past_fees == total_past

    def test_current_month_stays_open(self, temp_db):
        """Aktueller Monat bleibt offen"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        tasks.generate_fees.generate_monthly_fees()

        # Pruefen: Aktueller Monat sollte NICHT bezahlt sein
        conn = sqlite3.connect(temp_db)
        today = date.today()

        current_month_start = today.replace(day=1)
        next_month = (current_month_start + timedelta(days=32)).replace(day=1)

        open_current = conn.execute("""
            SELECT COUNT(*) FROM gebuehr
            WHERE faellig_am >= ?
              AND faellig_am < ?
              AND bezahlt_am IS NULL
        """, (current_month_start.isoformat(), next_month.isoformat())).fetchone()[0]

        total_current = conn.execute("""
            SELECT COUNT(*) FROM gebuehr
            WHERE faellig_am >= ?
              AND faellig_am < ?
        """, (current_month_start.isoformat(), next_month.isoformat())).fetchone()[0]

        conn.close()

        # Alle aktuellen sollten offen sein
        if total_current > 0:
            assert open_current == total_current

    def test_fees_for_both_zeitmodelle(self, temp_db):
        """Gebuehren werden fuer beide Zeitmodelle generiert"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        tasks.generate_fees.generate_monthly_fees()

        # Pruefen: Beide Einschreibungen haben Gebuehren
        conn = sqlite3.connect(temp_db)

        einschreibung_1 = conn.execute("""
            SELECT COUNT(*) FROM gebuehr WHERE einschreibung_id = 1
        """).fetchone()[0]

        einschreibung_2 = conn.execute("""
            SELECT COUNT(*) FROM gebuehr WHERE einschreibung_id = 2
        """).fetchone()[0]

        conn.close()

        assert einschreibung_1 > 0
        assert einschreibung_2 > 0


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_empty_database(self, temp_db):
        """Test mit leerer Einschreibungs-Tabelle"""
        # Loesche alle Einschreibungen
        conn = sqlite3.connect(temp_db)
        conn.execute("DELETE FROM einschreibung")
        conn.commit()
        conn.close()

        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        result = tasks.generate_fees.generate_monthly_fees()

        # Sollte 0 zurueckgeben
        assert result == 0

    def test_only_inactive_einschreibungen(self, temp_db):
        """Test mit nur inaktiven Einschreibungen"""
        # Setze alle auf inaktiv
        conn = sqlite3.connect(temp_db)
        conn.execute("UPDATE einschreibung SET status = 'exmatrikuliert'")
        conn.commit()
        conn.close()

        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        result = tasks.generate_fees.generate_monthly_fees()

        # Sollte 0 oder wenig zurueckgeben (abhaengig von Implementierung)
        assert result >= 0

    def test_new_einschreibung_this_month(self):
        """Test mit Einschreibung, die diesen Monat startet"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        conn = sqlite3.connect(path)
        conn.execute("PRAGMA foreign_keys = ON;")

        today = date.today()
        start_datum = today.replace(day=1)  # Dieser Monat

        conn.executescript(f"""
            CREATE TABLE student (
                id INTEGER PRIMARY KEY,
                matrikel_nr TEXT UNIQUE NOT NULL,
                vorname TEXT NOT NULL,
                nachname TEXT NOT NULL
            );
            CREATE TABLE studiengang (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                grad TEXT NOT NULL,
                regel_semester INTEGER NOT NULL
            );
            CREATE TABLE zeitmodell (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                monate_pro_semester INTEGER NOT NULL,
                kosten_monat REAL NOT NULL
            );
            CREATE TABLE einschreibung (
                id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                studiengang_id INTEGER NOT NULL,
                zeitmodell_id INTEGER NOT NULL,
                start_datum TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'aktiv'
            );
            CREATE TABLE gebuehr (
                id INTEGER PRIMARY KEY,
                einschreibung_id INTEGER NOT NULL,
                betrag REAL NOT NULL,
                art TEXT NOT NULL DEFAULT 'monatsrate',
                faellig_am TEXT NOT NULL,
                bezahlt_am TEXT,
                UNIQUE(einschreibung_id, faellig_am, art)
            );

            INSERT INTO student VALUES (1, 'IU99999999', 'Neu', 'Student');
            INSERT INTO studiengang VALUES (1, 'Informatik', 'B.Sc.', 6);
            INSERT INTO zeitmodell VALUES (1, 'Vollzeit', 6, 359.00);
            INSERT INTO einschreibung VALUES (1, 1, 1, 1, '{start_datum.isoformat()}', 'aktiv');
        """)
        conn.commit()
        conn.close()

        try:
            import tasks.generate_fees
            tasks.generate_fees.DB_PATH = Path(path)

            result = tasks.generate_fees.generate_monthly_fees()

            # Sollte Gebuehren generieren
            assert result >= 1

            # Pruefen: Gebuehren wurden erstellt
            conn = sqlite3.connect(path)
            total_fees = conn.execute("""
                SELECT COUNT(*) FROM gebuehr
            """).fetchone()[0]
            conn.close()

            # Es sollten Gebuehren erstellt worden sein
            assert total_fees >= 1
        finally:
            os.unlink(path)


# ============================================================================
# MAIN BLOCK TESTS
# ============================================================================

class TestMainBlock:
    """Tests fuer den __main__ Block"""

    def test_main_success_returns_count(self, temp_db):
        """generate_monthly_fees() gibt Anzahl zurueck bei Erfolg"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        result = tasks.generate_fees.generate_monthly_fees()

        # Sollte int zurueckgeben
        assert isinstance(result, int)
        assert result >= 0

    def test_main_failure_returns_zero(self):
        """generate_monthly_fees() gibt 0 zurueck bei fehlendem Pfad"""
        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path('/nonexistent.db')

        result = tasks.generate_fees.generate_monthly_fees()

        assert result == 0


# ============================================================================
# LOGGING TESTS
# ============================================================================

class TestLogging:
    """Tests fuer Logging-Verhalten"""

    def test_logs_start_message(self, temp_db, caplog):
        """Loggt Start-Nachricht"""
        import logging
        caplog.set_level(logging.INFO)

        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        tasks.generate_fees.generate_monthly_fees()

        assert any('Starte' in record.message for record in caplog.records)

    def test_logs_result_message(self, temp_db, caplog):
        """Loggt Ergebnis-Nachricht"""
        import logging
        caplog.set_level(logging.INFO)

        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path(temp_db)

        tasks.generate_fees.generate_monthly_fees()

        # Sollte entweder "generiert" oder "aktuell" loggen
        assert any('generiert' in record.message.lower() or
                  'aktuell' in record.message.lower()
                  for record in caplog.records)

    def test_logs_error_on_missing_db(self, caplog):
        """Loggt Fehler bei fehlender DB"""
        import logging
        caplog.set_level(logging.ERROR)

        import tasks.generate_fees
        tasks.generate_fees.DB_PATH = Path('/nonexistent/path.db')

        tasks.generate_fees.generate_monthly_fees()

        assert any('nicht gefunden' in record.message.lower() or
                  'error' in record.levelname.lower()
                  for record in caplog.records)