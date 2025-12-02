# tests/integration/test_generate_fees.py
"""
Integrationstests fuer das generate_fees Task-Script

Testet mit echter SQLite-Datenbank und echtem GebuehrRepository.
"""
import pytest
import sqlite3
import sys
from pathlib import Path
from datetime import date, timedelta

# Import des zu testenden Moduls
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Mark this whole module as integration
pytestmark = pytest.mark.integration


# ============================================================================
# INTEGRATION TESTS (mit echter DB)
# ============================================================================

class TestGenerateFeesIntegration:
    """Integrationstests fuer generate_fees mit echter SQLite-Datenbank"""

    @pytest.fixture
    def test_db(self, tmp_path):
        """Erstellt eine Test-Datenbank mit dem ECHTEN Schema"""
        db_path = tmp_path / "test_dashboard.db"

        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")

            # student Tabelle (echtes Schema)
            # noinspection SqlResolve
            conn.execute("""
                         CREATE TABLE student
                         (
                             id          INTEGER PRIMARY KEY AUTOINCREMENT,
                             vorname     TEXT        NOT NULL,
                             nachname    TEXT        NOT NULL,
                             matrikel_nr TEXT UNIQUE NOT NULL,
                             login_id    INTEGER UNIQUE
                         )
                         """)

            # studiengang Tabelle (echtes Schema)
            # noinspection SqlResolve
            conn.execute("""
                         CREATE TABLE studiengang
                         (
                             id             INTEGER PRIMARY KEY AUTOINCREMENT,
                             name           TEXT    NOT NULL,
                             grad           TEXT    NOT NULL,
                             regel_semester INTEGER NOT NULL
                         )
                         """)

            # zeitmodell Tabelle (echtes Schema)
            # noinspection SqlResolve
            conn.execute("""
                         CREATE TABLE zeitmodell
                         (
                             id           INTEGER PRIMARY KEY AUTOINCREMENT,
                             name         TEXT           NOT NULL UNIQUE,
                             dauer_monate INTEGER        NOT NULL,
                             kosten_monat DECIMAL(10, 2) NOT NULL
                         )
                         """)

            # einschreibung Tabelle (echtes Schema)
            # noinspection SqlResolve
            conn.execute("""
                         CREATE TABLE einschreibung
                         (
                             id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                             student_id             INTEGER NOT NULL,
                             studiengang_id         INTEGER NOT NULL,
                             zeitmodell_id          INTEGER NOT NULL,
                             start_datum            DATE    NOT NULL,
                             exmatrikulations_datum DATE,
                             status                 TEXT    NOT NULL DEFAULT 'aktiv'
                                 CHECK (status IN ('aktiv', 'pausiert', 'exmatrikuliert')),
                             FOREIGN KEY (student_id) REFERENCES student (id),
                             FOREIGN KEY (studiengang_id) REFERENCES studiengang (id),
                             FOREIGN KEY (zeitmodell_id) REFERENCES zeitmodell (id)
                         )
                         """)

            # gebuehr Tabelle (echtes Schema)
            # noinspection SqlResolve
            conn.execute("""
                         CREATE TABLE gebuehr
                         (
                             id               INTEGER PRIMARY KEY AUTOINCREMENT,
                             einschreibung_id INTEGER        NOT NULL,
                             art              TEXT           NOT NULL,
                             betrag           DECIMAL(10, 2) NOT NULL,
                             faellig_am       DATE           NOT NULL,
                             bezahlt_am       DATE,
                             FOREIGN KEY (einschreibung_id) REFERENCES einschreibung (id)
                         )
                         """)

            # Unique Index fuer Idempotenz
            # noinspection SqlResolve
            conn.execute("""
                         CREATE UNIQUE INDEX idx_gebuehr_einschreibung_faellig
                             ON gebuehr (einschreibung_id, faellig_am)
                         """)

            # Test-Daten einfuegen
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO student (id, vorname, nachname, matrikel_nr)
                         VALUES (1, 'Max', 'Mustermann', 'IU12345')
                         """)

            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO studiengang (id, name, grad, regel_semester)
                         VALUES (1, 'Informatik', 'B.Sc.', 6)
                         """)

            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO zeitmodell (id, name, dauer_monate, kosten_monat)
                         VALUES (1, 'Vollzeit', 36, 199.00)
                         """)

            # Einschreibung 6 Monate in der Vergangenheit
            start_datum = (date.today() - timedelta(days=180)).isoformat()
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status)
                         VALUES (1, 1, 1, 1, ?, 'aktiv')
                         """, (start_datum,))

            conn.commit()

        return db_path

    def test_generate_fees_creates_entries(self, test_db):
        """Test: Gebuehren werden in der Datenbank erstellt"""
        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))

        # Vor der Generierung: keine Gebuehren
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            count_before = conn.execute("SELECT COUNT(*) FROM gebuehr").fetchone()[0]

        assert count_before == 0

        # Gebuehren generieren
        inserted = repo.ensure_monthly_fees()

        # Nach der Generierung: Gebuehren vorhanden
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            count_after = conn.execute("SELECT COUNT(*) FROM gebuehr").fetchone()[0]

        assert count_after > 0
        assert inserted > 0  # Methode gibt Anzahl versuchter Inserts zurueck

    def test_idempotent_execution(self, test_db):
        """Test: Mehrfache Ausfuehrung ist idempotent"""
        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))

        # Erste Ausfuehrung
        repo.ensure_monthly_fees()

        # Zaehle Gebuehren nach erster Ausfuehrung
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            count_after_first = conn.execute("SELECT COUNT(*) FROM gebuehr").fetchone()[0]

        # Zweite Ausfuehrung
        repo.ensure_monthly_fees()

        # Zaehle Gebuehren nach zweiter Ausfuehrung
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            count_after_second = conn.execute("SELECT COUNT(*) FROM gebuehr").fetchone()[0]

        # Gesamtanzahl bleibt gleich (idempotent)
        assert count_after_first == count_after_second
        assert count_after_first > 0

    def test_correct_amounts(self, test_db):
        """Test: Betraege entsprechen dem Zeitmodell"""
        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            fees = conn.execute("""
                                SELECT betrag
                                FROM gebuehr
                                WHERE einschreibung_id = 1
                                """).fetchall()

        # Alle Betraege sollten 199.00 sein (aus zeitmodell)
        for fee in fees:
            assert float(fee[0]) == 199.00

    def test_past_fees_marked_paid(self, test_db):
        """Test: Vergangene Gebuehren werden als bezahlt markiert"""
        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        today = date.today()

        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            fees = conn.execute("""
                                SELECT faellig_am, bezahlt_am
                                FROM gebuehr
                                WHERE einschreibung_id = 1
                                ORDER BY faellig_am
                                """).fetchall()

        for faellig_am, bezahlt_am in fees:
            faellig_date = date.fromisoformat(faellig_am)

            if faellig_date < today.replace(day=1):
                # Vergangene Monate sollten bezahlt sein
                assert bezahlt_am is not None
            else:
                # Aktueller/zukuenftiger Monat sollte offen sein
                assert bezahlt_am is None

    def test_only_active_einschreibungen(self, test_db):
        """Test: Nur aktive Einschreibungen erhalten Gebuehren"""
        from repositories.gebuehr_repository import GebuehrRepository

        # Exmatrikulierte Einschreibung hinzufuegen
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO student (id, vorname, nachname, matrikel_nr)
                         VALUES (2, 'Anna', 'Beispiel', 'IU67890')
                         """)

            start_datum = (date.today() - timedelta(days=180)).isoformat()
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status)
                         VALUES (2, 2, 1, 1, ?, 'exmatrikuliert')
                         """, (start_datum,))
            conn.commit()

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        # Nur Gebuehren fuer aktive Einschreibung (ID 1)
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            fees_active = conn.execute("""
                                       SELECT COUNT(*)
                                       FROM gebuehr
                                       WHERE einschreibung_id = 1
                                       """).fetchone()[0]
            # noinspection SqlResolve
            fees_inactive = conn.execute("""
                                         SELECT COUNT(*)
                                         FROM gebuehr
                                         WHERE einschreibung_id = 2
                                         """).fetchone()[0]

        assert fees_active > 0
        assert fees_inactive == 0

    def test_pausiert_einschreibungen_no_fees(self, test_db):
        """Test: Pausierte Einschreibungen erhalten keine Gebuehren"""
        from repositories.gebuehr_repository import GebuehrRepository

        # Pausierte Einschreibung hinzufuegen
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO student (id, vorname, nachname, matrikel_nr)
                         VALUES (2, 'Anna', 'Beispiel', 'IU67890')
                         """)

            start_datum = (date.today() - timedelta(days=180)).isoformat()
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status)
                         VALUES (2, 2, 1, 1, ?, 'pausiert')
                         """, (start_datum,))
            conn.commit()

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        # Nur Gebuehren fuer aktive Einschreibung (ID 1)
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            fees_pausiert = conn.execute("""
                                         SELECT COUNT(*)
                                         FROM gebuehr
                                         WHERE einschreibung_id = 2
                                         """).fetchone()[0]

        assert fees_pausiert == 0

    def test_fee_art_is_monatsrate(self, test_db):
        """Test: Art der Gebuehr ist 'Monatsrate'"""
        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            arts = conn.execute("""
                                SELECT DISTINCT art
                                FROM gebuehr
                                """).fetchall()

        assert len(arts) == 1
        assert arts[0][0] == 'Monatsrate'

    def test_multiple_students(self, test_db):
        """Test: Gebuehren fuer mehrere Studenten"""
        # Zweiten aktiven Studenten hinzufuegen
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO student (id, vorname, nachname, matrikel_nr)
                         VALUES (2, 'Anna', 'Beispiel', 'IU67890')
                         """)

            start_datum = (date.today() - timedelta(days=90)).isoformat()
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status)
                         VALUES (2, 2, 1, 1, ?, 'aktiv')
                         """, (start_datum,))
            conn.commit()

        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            fees_s1 = conn.execute("""
                                   SELECT COUNT(*)
                                   FROM gebuehr
                                   WHERE einschreibung_id = 1
                                   """).fetchone()[0]
            # noinspection SqlResolve
            fees_s2 = conn.execute("""
                                   SELECT COUNT(*)
                                   FROM gebuehr
                                   WHERE einschreibung_id = 2
                                   """).fetchone()[0]

        # Beide sollten Gebuehren haben
        assert fees_s1 > 0
        assert fees_s2 > 0

        # Student 1 hat mehr (laengere Einschreibung)
        assert fees_s1 > fees_s2

    def test_different_zeitmodelle(self, test_db):
        """Test: Verschiedene Zeitmodelle haben verschiedene Betraege"""
        # Teilzeit-Zeitmodell hinzufuegen
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO zeitmodell (id, name, dauer_monate, kosten_monat)
                         VALUES (2, 'Teilzeit I', 48, 149.00)
                         """)

            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO student (id, vorname, nachname, matrikel_nr)
                         VALUES (2, 'Anna', 'Beispiel', 'IU67890')
                         """)

            start_datum = (date.today() - timedelta(days=90)).isoformat()
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status)
                         VALUES (2, 2, 1, 2, ?, 'aktiv')
                         """, (start_datum,))
            conn.commit()

        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        with sqlite3.connect(str(test_db)) as conn:
            # Vollzeit-Gebuehren
            # noinspection SqlResolve
            fees_vollzeit = conn.execute("""
                                         SELECT DISTINCT betrag
                                         FROM gebuehr
                                         WHERE einschreibung_id = 1
                                         """).fetchone()[0]
            # Teilzeit-Gebuehren
            # noinspection SqlResolve
            fees_teilzeit = conn.execute("""
                                         SELECT DISTINCT betrag
                                         FROM gebuehr
                                         WHERE einschreibung_id = 2
                                         """).fetchone()[0]

        assert float(fees_vollzeit) == 199.00
        assert float(fees_teilzeit) == 149.00

    def test_fees_start_from_einschreibung_date(self, test_db):
        """Test: Gebuehren starten ab Einschreibungsdatum"""
        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        # Hole Einschreibungsdatum
        start_datum = (date.today() - timedelta(days=180))

        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            earliest_fee = conn.execute("""
                                        SELECT MIN(faellig_am)
                                        FROM gebuehr
                                        WHERE einschreibung_id = 1
                                        """).fetchone()[0]

        earliest_date = date.fromisoformat(earliest_fee)

        # Frueheste Gebuehr sollte im Monat der Einschreibung oder danach sein
        assert earliest_date.year >= start_datum.year
        assert earliest_date.month >= start_datum.month or earliest_date.year > start_datum.year

    def test_no_duplicate_fees_for_same_month(self, test_db):
        """Test: Keine doppelten Gebuehren fuer denselben Monat"""
        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        with sqlite3.connect(str(test_db)) as conn:
            # Zaehle Gebuehren pro Monat
            # noinspection SqlResolve
            duplicates = conn.execute("""
                                      SELECT faellig_am, COUNT(*) as cnt
                                      FROM gebuehr
                                      WHERE einschreibung_id = 1
                                      GROUP BY faellig_am
                                      HAVING cnt > 1
                                      """).fetchall()

        # Es sollte keine Duplikate geben
        assert len(duplicates) == 0

    def test_unique_index_prevents_duplicates(self, test_db):
        """Test: Der Unique Index verhindert doppelte Eintraege"""
        from repositories.gebuehr_repository import GebuehrRepository

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        # Versuche manuell eine doppelte Gebuehr einzufuegen
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            existing_fee = conn.execute("""
                                        SELECT einschreibung_id, faellig_am
                                        FROM gebuehr
                                        LIMIT 1
                                        """).fetchone()

            # IntegrityError sollte geworfen werden
            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                conn.execute("""
                             INSERT INTO gebuehr (einschreibung_id, art, betrag, faellig_am)
                             VALUES (?, 'Monatsrate', 199.00, ?)
                             """, (existing_fee[0], existing_fee[1]))

    def test_exmatrikulations_datum_respected(self, test_db):
        """Test: Gebuehren werden nur bis zum Exmatrikulationsdatum generiert"""
        from repositories.gebuehr_repository import GebuehrRepository

        # Einschreibung mit Exmatrikulationsdatum
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO student (id, vorname, nachname, matrikel_nr)
                         VALUES (2, 'Anna', 'Beispiel', 'IU67890')
                         """)

            start_datum = (date.today() - timedelta(days=180)).isoformat()
            exmat_datum = (date.today() - timedelta(days=60)).isoformat()

            # noinspection SqlResolve
            conn.execute("""
                         INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id,
                                                    start_datum, exmatrikulations_datum, status)
                         VALUES (2, 2, 1, 1, ?, ?, 'exmatrikuliert')
                         """, (start_datum, exmat_datum))
            conn.commit()

        repo = GebuehrRepository(str(test_db))
        repo.ensure_monthly_fees()

        # Pruefe ob Gebuehren nach Exmatrikulation existieren
        with sqlite3.connect(str(test_db)) as conn:
            # noinspection SqlResolve
            fees_after_exmat = conn.execute("""
                                            SELECT COUNT(*)
                                            FROM gebuehr
                                            WHERE einschreibung_id = 2
                                              AND faellig_am > ?
                                            """, (exmat_datum,)).fetchone()[0]

            # Keine Gebuehren nach Exmatrikulation (Status ist exmatrikuliert)
            # Das Repository sollte diese Einschreibung komplett ignorieren
            # noinspection SqlResolve
            fees_total = conn.execute("""
                                      SELECT COUNT(*)
                                      FROM gebuehr
                                      WHERE einschreibung_id = 2
                                      """).fetchone()[0]

        assert fees_total == 0  # Exmatrikulierte Einschreibungen bekommen keine Gebuehren


# ============================================================================
# GENERATE_FEES FUNCTION TESTS
# ============================================================================

# Versuche tasks.generate_fees zu importieren - skip wenn nicht vorhanden
try:
    import tasks.generate_fees as gf
    HAS_GENERATE_FEES_MODULE = True
except ImportError:
    HAS_GENERATE_FEES_MODULE = False


@pytest.mark.skipif(not HAS_GENERATE_FEES_MODULE, reason="tasks.generate_fees Modul nicht gefunden")
class TestGenerateFeesFunction:
    """Tests fuer die generate_monthly_fees Funktion"""

    def test_generate_monthly_fees_returns_count(self, tmp_path, monkeypatch):
        """Test: Funktion gibt Anzahl generierter Gebuehren zurueck"""
        # Erstelle Test-DB
        db_path = tmp_path / "test.db"

        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")

            # Minimales Schema
            # noinspection SqlResolve
            conn.execute("""
                CREATE TABLE student (
                    id INTEGER PRIMARY KEY,
                    vorname TEXT NOT NULL,
                    nachname TEXT NOT NULL,
                    matrikel_nr TEXT UNIQUE NOT NULL,
                    login_id INTEGER UNIQUE
                )
            """)
            # noinspection SqlResolve
            conn.execute("""
                CREATE TABLE studiengang (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    grad TEXT NOT NULL,
                    regel_semester INTEGER NOT NULL
                )
            """)
            # noinspection SqlResolve
            conn.execute("""
                CREATE TABLE zeitmodell (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    dauer_monate INTEGER NOT NULL,
                    kosten_monat DECIMAL(10,2) NOT NULL
                )
            """)
            # noinspection SqlResolve
            conn.execute("""
                CREATE TABLE einschreibung (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    studiengang_id INTEGER NOT NULL,
                    zeitmodell_id INTEGER NOT NULL,
                    start_datum DATE NOT NULL,
                    exmatrikulations_datum DATE,
                    status TEXT NOT NULL DEFAULT 'aktiv'
                        CHECK (status IN ('aktiv', 'pausiert', 'exmatrikuliert')),
                    FOREIGN KEY (student_id) REFERENCES student(id),
                    FOREIGN KEY (studiengang_id) REFERENCES studiengang(id),
                    FOREIGN KEY (zeitmodell_id) REFERENCES zeitmodell(id)
                )
            """)
            # noinspection SqlResolve
            conn.execute("""
                CREATE TABLE gebuehr (
                    id INTEGER PRIMARY KEY,
                    einschreibung_id INTEGER NOT NULL,
                    art TEXT NOT NULL,
                    betrag DECIMAL(10,2) NOT NULL,
                    faellig_am DATE NOT NULL,
                    bezahlt_am DATE,
                    FOREIGN KEY (einschreibung_id) REFERENCES einschreibung(id)
                )
            """)
            # noinspection SqlResolve
            conn.execute("""
                CREATE UNIQUE INDEX idx_gebuehr_einschreibung_faellig
                    ON gebuehr (einschreibung_id, faellig_am)
            """)

            # Testdaten
            # noinspection SqlResolve
            conn.execute("INSERT INTO student VALUES (1, 'Test', 'User', 'IU99999', NULL)")
            # noinspection SqlResolve
            conn.execute("INSERT INTO studiengang VALUES (1, 'Test', 'B.Sc.', 6)")
            # noinspection SqlResolve
            conn.execute("INSERT INTO zeitmodell VALUES (1, 'Vollzeit', 36, 199.00)")

            start_datum = (date.today() - timedelta(days=60)).isoformat()
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO einschreibung VALUES (1, 1, 1, 1, ?, NULL, 'aktiv')
            """, (start_datum,))
            conn.commit()

        # Patche DB_PATH im generate_fees Modul
        monkeypatch.setattr(gf, 'DB_PATH', db_path)

        # Funktion ausfuehren
        count = gf.generate_monthly_fees()

        # Sollte mindestens 1 Gebuehr generiert haben
        assert count >= 1

    def test_generate_monthly_fees_missing_db(self, tmp_path, monkeypatch):
        """Test: Funktion gibt 0 zurueck wenn DB nicht existiert"""
        # Setze nicht-existierenden Pfad
        monkeypatch.setattr(gf, 'DB_PATH', tmp_path / "nicht_vorhanden.db")

        count = gf.generate_monthly_fees()
        assert count == 0