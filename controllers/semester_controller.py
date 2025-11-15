# controllers/semester_controller.py
from __future__ import annotations
from typing import Optional
import logging
import sqlite3
from repositories import StudentRepository, EinschreibungRepository, ModulRepository, ModulbuchungRepository

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')


class SemesterController:
    """Controller fuer Semester-/Modulbuchungs-Logik

    Alle Methoden sind PUBLIC, da sie von Flask-Routes aufgerufen werden.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.__student_repo = StudentRepository(db_path)
        self.__einschreibung_repo = EinschreibungRepository(db_path)
        self.__modul_repo = ModulRepository(db_path)
        self.__modulbuchung_repo = ModulbuchungRepository(db_path)

    # ========== PUBLIC Methods ==========

    def get_modules_for_semester(
            self,
            login_id: int,
            semester_nr: int
    ) -> dict:
        """PUBLIC: Liefert alle Module eines Semesters mit Buchungsstatus

        Args:
            login_id: ID aus login-Tabelle (current_user.id)
            semester_nr: Semesternummer (1-7)

        Returns:
            Dictionary mit success, semester, modules
        """
        try:
            # 1. Student laden
            student = self.__student_repo.get_by_login_id(login_id)
            if not student:
                return {
                    'success': False,
                    'error': 'Kein Student zu diesem Login gefunden'
                }

            # 2. Aktive Einschreibung laden
            try:
                einschreibung = self.__einschreibung_repo.get_aktive_by_student(student.id)
                studiengang_id = einschreibung.studiengang_id
            except Exception:
                # Fallback: Studiengang 1
                studiengang_id = 1

            # 3. Module laden (vom Repository)
            module_buchungen = self.__modul_repo.get_modules_for_semester(
                studiengang_id=studiengang_id,
                semester=semester_nr,
                student_id=student.id
            )

            # 4. Fuege modulbuchung_id UND Pruefungsdaten hinzu
            modules_data = []
            for mb in module_buchungen:
                module_dict = mb.to_dict()

                # Wenn Modul gebucht ist, hole die modulbuchung_id UND Pruefungsdaten
                if mb.status == 'gebucht' or mb.status == 'bestanden' or mb.status == 'nicht_bestanden':
                    try:
                        with sqlite3.connect(self.db_path) as con:
                            con.row_factory = sqlite3.Row
                            result = con.execute(
                                """SELECT mb.id    as modulbuchung_id,
                                          pa.pruefungstermin_id,
                                          pt.datum as pruefungsdatum
                                   FROM modulbuchung mb
                                            JOIN einschreibung e ON mb.einschreibung_id = e.id
                                            LEFT JOIN pruefungsanmeldung pa ON pa.modulbuchung_id = mb.id
                                       AND pa.status = 'angemeldet'
                                            LEFT JOIN pruefungstermin pt ON pt.id = pa.pruefungstermin_id
                                   WHERE e.student_id = ?
                                     AND mb.modul_id = ?
                                   LIMIT 1""",
                                (student.id, mb.modul_id)
                            ).fetchone()

                            if result:
                                module_dict['modulbuchung_id'] = result['modulbuchung_id']
                                module_dict['pruefungsdatum'] = result['pruefungsdatum']

                                # Setze Status auf "angemeldet" wenn Pruefung existiert
                                if result['pruefungsdatum']:
                                    module_dict['status'] = 'angemeldet'
                                    logger.info(
                                        f"Modul {mb.name}: Pruefung am {result['pruefungsdatum']}")
                                else:
                                    logger.info(f"Modul {mb.name}: Gebucht, aber noch keine Pruefung angemeldet")
                            else:
                                module_dict['modulbuchung_id'] = None
                                module_dict['pruefungsdatum'] = None
                                logger.warning(f"Modul {mb.name}: Keine modulbuchung_id gefunden")
                    except Exception as e:
                        logger.error(f"Fehler beim Laden der Pruefungsdaten fuer Modul {mb.modul_id}: {e}")
                        module_dict['modulbuchung_id'] = None
                        module_dict['pruefungsdatum'] = None
                else:
                    module_dict['modulbuchung_id'] = None
                    module_dict['pruefungsdatum'] = None

                modules_data.append(module_dict)

            logger.info(f"Lade {len(modules_data)} Module fuer Semester {semester_nr}")

            return {
                'success': True,
                'semester': semester_nr,
                'modules': modules_data
            }

        except Exception as e:
            logger.exception(f"Fehler beim Laden von Semester {semester_nr}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def book_module(
            self,
            login_id: int,
            modul_id: int
    ) -> dict:
        """PUBLIC: Bucht ein Modul fuer den Studenten

        SEMESTERBASIERTE BUCHUNGSLOGIK:
        - Student kann NUR Module aus dem AKTUELLEN Semester buchen
        - Student kann auch Module aus dem VORHERIGEN Semester buchen (Nachholer)
        - Module aus ZUKUENFTIGEN Semestern sind GESPERRT
        - Um ins NAECHSTE Semester zu kommen, muss das AKTUELLE Semester komplett abgeschlossen sein

        Beispiel:
        - Student ist in Semester 2 (hat Semester 1 komplett)
        - Kann buchen: Module aus Semester 2 (aktuell) und Semester 1 (Nachholer)
        - NICHT buchen: Module aus Semester 3+ (zukuenftig)

        Args:
            login_id: ID aus login-Tabelle (current_user.id)
            modul_id: ID des zu buchenden Moduls

        Returns:
            Dictionary mit success, message
        """
        try:
            # 1. Student laden
            student = self.__student_repo.get_by_login_id(login_id)
            if not student:
                return {
                    'success': False,
                    'error': 'Kein Student zu diesem Login gefunden'
                }

            # 2. Aktive Einschreibung laden
            einschreibung = self.__einschreibung_repo.get_aktive_by_student(student.id)

            with sqlite3.connect(self.db_path) as con:
                con.execute("PRAGMA foreign_keys = ON;")

                # 3. Hole Semester des zu buchenden Moduls
                modul_semester_result = con.execute(
                    """SELECT sgm.semester
                       FROM studiengang_modul sgm
                       WHERE sgm.studiengang_id = ?
                         AND sgm.modul_id = ?
                       LIMIT 1""",
                    (einschreibung.studiengang_id, modul_id)
                ).fetchone()

                if not modul_semester_result:
                    return {
                        'success': False,
                        'error': 'Modul gehoert nicht zu deinem Studiengang'
                    }

                modul_semester = modul_semester_result[0]

                # 4. Berechne AKTUELLES Semester des Studenten (fortschrittsbasiert)
                # = Hoechstes KOMPLETT abgeschlossenes Semester + 1
                result = con.execute("""
                                     SELECT MAX(semester) as hoechstes_komplett
                                     FROM (SELECT sgm.semester,
                                                  COUNT(DISTINCT sgm.modul_id) as gesamt,
                                                  COUNT(DISTINCT CASE
                                                                     WHEN mb.status IN ('bestanden', 'anerkannt')
                                                                         THEN mb.modul_id
                                                      END)                     as abgeschlossen
                                           FROM studiengang_modul sgm
                                                    LEFT JOIN modulbuchung mb
                                                              ON mb.modul_id = sgm.modul_id
                                                                  AND mb.einschreibung_id = ?
                                           WHERE sgm.studiengang_id = ?
                                           GROUP BY sgm.semester
                                           HAVING gesamt = abgeschlossen)
                                     """, (einschreibung.id, einschreibung.studiengang_id)).fetchone()

                hoechstes_komplett = result[0] if result and result[0] else 0
                aktuelles_semester = hoechstes_komplett + 1

                logger.info(f"Student-Fortschritt: Semester {hoechstes_komplett} komplett -> "
                            f"aktuelles Semester: {aktuelles_semester}")

                # 5. NEUE VALIDIERUNG: Semesterbasiert
                if modul_semester > aktuelles_semester:
                    # Modul ist aus ZUKUENFTIGEM Semester
                    return {
                        'success': False,
                        'error': f'Dieses Modul ist aus Semester {modul_semester}. '
                                 f'Du befindest dich aktuell in Semester {aktuelles_semester}. '
                                 f'Schliesse erst alle Module des aktuellen Semesters ab, um ins naechste Semester zu gelangen.'
                    }

                elif modul_semester < aktuelles_semester - 1:
                    # Modul ist aus WEIT ZURUECKLIEGENDEM Semester (2+ Semester her)
                    # Das ist OK - erlaube Nachholer aus alten Semestern
                    logger.info(f"Nachholer-Modul aus Semester {modul_semester} (aktuell: {aktuelles_semester})")

                else:
                    # modul_semester == aktuelles_semester ODER aktuelles_semester - 1
                    # -> ERLAUBT! (aktuelles Semester oder Nachholer vom letzten Semester)
                    logger.info(f"Buchung erlaubt: Modul aus Semester {modul_semester}, "
                                f"Student in Semester {aktuelles_semester}")

                # 6. Pruefen ob bereits gebucht
                existing = con.execute(
                    """SELECT id
                       FROM modulbuchung
                       WHERE einschreibung_id = ?
                         AND modul_id = ?""",
                    (einschreibung.id, modul_id)
                ).fetchone()

                if existing:
                    return {
                        'success': False,
                        'error': 'Modul bereits gebucht'
                    }

                # 7. Modul buchen
                con.execute(
                    """INSERT INTO modulbuchung
                           (einschreibung_id, modul_id, buchungsdatum, status)
                       VALUES (?, ?, DATE('now'), 'gebucht')""",
                    (einschreibung.id, modul_id)
                )
                con.commit()

            logger.info(f"Modul {modul_id} (Semester {modul_semester}) erfolgreich gebucht fuer Student {student.id}")

            return {
                'success': True,
                'message': 'Modul erfolgreich gebucht'
            }

        except Exception as e:
            logger.exception(f"Fehler beim Buchen von Modul {modul_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }