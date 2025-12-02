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
    """Controller für Semester-/Modulbuchungs-Logik

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

        Für Semester 5 und 6 werden Wahlmodule separat gruppiert zurückgegeben.

        Args:
            login_id: ID aus login-Tabelle (current_user.id)
            semester_nr: Semesternummer (1-7)

        Returns:
            Dictionary mit success, semester, modules, wahlmodule (für Sem 5+6)
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

            # 4. Trenne Pflichtmodule von Wahlmodulen
            pflicht_modules = []
            wahlmodule_dict = {'A': [], 'B': [], 'C': []}

            for mb in module_buchungen:
                module_dict = mb.to_dict()

                # Füge modulbuchung_id und Prüfungsdaten hinzu
                module_dict = self.__enrich_module_data(module_dict, mb, student.id)

                if mb.wahlbereich:
                    # Wahlmodul -> in entsprechenden Bereich sortieren
                    if mb.wahlbereich in wahlmodule_dict:
                        wahlmodule_dict[mb.wahlbereich].append(module_dict)
                else:
                    # Pflichtmodul
                    pflicht_modules.append(module_dict)

            # 5. Hole bereits gebuchte Wahlmodule (für Filter in Wahlbereich C)
            gebuchte_wahlmodule = self.__modul_repo.get_gebuchte_wahlmodule(
                studiengang_id=studiengang_id,
                student_id=student.id
            )

            # 6. Filtere Wahlbereich C: Entferne bereits in A gebuchtes Modul
            if gebuchte_wahlmodule.get('A'):
                gebuchtes_a_id = gebuchte_wahlmodule['A']['modul_id']
                wahlmodule_dict['C'] = [
                    m for m in wahlmodule_dict['C']
                    if m['modul_id'] != gebuchtes_a_id
                ]

            logger.info(f"Lade {len(pflicht_modules)} Pflichtmodule und "
                        f"{sum(len(v) for v in wahlmodule_dict.values())} Wahlmodule "
                        f"für Semester {semester_nr}")

            return {
                'success': True,
                'semester': semester_nr,
                'modules': pflicht_modules,
                'wahlmodule': wahlmodule_dict,
                'gebuchte_wahlmodule': gebuchte_wahlmodule
            }

        except Exception as e:
            logger.exception(f"Fehler beim Laden von Semester {semester_nr}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_wahlmodul_status(self, login_id: int) -> dict:
        """PUBLIC: Liefert Status aller Wahlmodule eines Studenten

        Returns:
            Dictionary mit:
            {
                'success': True,
                'wahlmodule': {
                    'A': {'modul_id': 123, 'name': '...', 'status': 'bestanden'} oder None,
                    'B': {...} oder None,
                    'C': {...} oder None
                },
                'complete': True/False  # Alle 3 Wahlmodule gewählt?
            }
        """
        try:
            student = self.__student_repo.get_by_login_id(login_id)
            if not student:
                return {'success': False, 'error': 'Kein Student gefunden'}

            einschreibung = self.__einschreibung_repo.get_aktive_by_student(student.id)

            gebuchte = self.__modul_repo.get_gebuchte_wahlmodule(
                studiengang_id=einschreibung.studiengang_id,
                student_id=student.id
            )

            complete = all(gebuchte.get(b) is not None for b in ['A', 'B', 'C'])

            return {
                'success': True,
                'wahlmodule': gebuchte,
                'complete': complete
            }

        except Exception as e:
            logger.exception("Fehler beim Laden des Wahlmodul-Status")
            return {'success': False, 'error': str(e)}

    def book_module(
            self,
            login_id: int,
            modul_id: int
    ) -> dict:
        """PUBLIC: Bucht ein Modul für den Studenten

        SEMESTERBASIERTE BUCHUNGSLOGIK:
        - Student kann NUR Module aus dem AKTUELLEN Semester buchen
        - Student kann auch Module aus dem VORHERIGEN Semester buchen (Nachholer)
        - Module aus ZUKÜNFTIGEN Semestern sind GESPERRT
        - Um ins NÄCHSTE Semester zu kommen, muss das AKTUELLE Semester komplett abgeschlossen sein

        WAHLMODUL-VALIDIERUNG:
        - Pro Wahlbereich (A, B, C) nur 1 Modul erlaubt
        - In Wahlbereich C darf nicht dasselbe Modul wie in A gebucht werden

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

                # 3. Hole Semester und Wahlbereich des zu buchenden Moduls
                modul_info = con.execute(
                    """SELECT sgm.semester, sgm.wahlbereich, m.name
                       FROM studiengang_modul sgm
                       JOIN modul m ON m.id = sgm.modul_id
                       WHERE sgm.studiengang_id = ?
                         AND sgm.modul_id = ?
                       LIMIT 1""",
                    (einschreibung.studiengang_id, modul_id)
                ).fetchone()

                if not modul_info:
                    return {
                        'success': False,
                        'error': 'Modul gehört nicht zu deinem Studiengang'
                    }

                modul_semester = modul_info[0]
                wahlbereich = modul_info[1]
                modul_name = modul_info[2]

                # 4. WAHLMODUL-VALIDIERUNG (wenn es ein Wahlmodul ist)
                if wahlbereich:
                    validation_result = self.__validate_wahlmodul_booking(
                        con, einschreibung.id, einschreibung.studiengang_id,
                        modul_id, wahlbereich, modul_semester
                    )
                    if not validation_result['success']:
                        return validation_result

                # 5. Berechne AKTUELLES Semester des Studenten (fortschrittsbasiert)
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

                # 6. SEMESTER-VALIDIERUNG
                if modul_semester > aktuelles_semester:
                    return {
                        'success': False,
                        'error': f'Dieses Modul ist aus Semester {modul_semester}. '
                                 f'Du befindest dich aktuell in Semester {aktuelles_semester}. '
                                 f'Schließe erst alle Module des aktuellen Semesters ab, um ins nächste Semester zu gelangen.'
                    }

                elif modul_semester < aktuelles_semester - 1:
                    logger.info(f"Nachholer-Modul aus Semester {modul_semester} (aktuell: {aktuelles_semester})")

                else:
                    logger.info(f"Buchung erlaubt: Modul aus Semester {modul_semester}, "
                                f"Student in Semester {aktuelles_semester}")

                # 7. Prüfen ob bereits gebucht
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

                # 8. Modul buchen
                con.execute(
                    """INSERT INTO modulbuchung
                           (einschreibung_id, modul_id, buchungsdatum, status)
                       VALUES (?, ?, DATE('now'), 'gebucht')""",
                    (einschreibung.id, modul_id)
                )
                con.commit()

            wahlbereich_info = f" (Wahlbereich {wahlbereich})" if wahlbereich else ""
            logger.info(f"Modul {modul_id} '{modul_name}'{wahlbereich_info} "
                        f"(Semester {modul_semester}) erfolgreich gebucht für Student {student.id}")

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

    # ========== PRIVATE Methods ==========

    def __enrich_module_data(self, module_dict: dict, mb, student_id: int) -> dict:
        """PRIVATE: Fügt modulbuchung_id und Prüfungsdaten zu Modul-Dict hinzu"""
        if mb.status in ('gebucht', 'bestanden', 'nicht_bestanden'):
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
                        (student_id, mb.modul_id)
                    ).fetchone()

                    if result:
                        module_dict['modulbuchung_id'] = result['modulbuchung_id']
                        module_dict['pruefungsdatum'] = result['pruefungsdatum']

                        if result['pruefungsdatum']:
                            module_dict['status'] = 'angemeldet'
                            logger.info(f"Modul {mb.name}: Prüfung am {result['pruefungsdatum']}")
                        else:
                            logger.info(f"Modul {mb.name}: Gebucht, aber noch keine Prüfung angemeldet")
                    else:
                        module_dict['modulbuchung_id'] = None
                        module_dict['pruefungsdatum'] = None
                        logger.warning(f"Modul {mb.name}: Keine modulbuchung_id gefunden")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Prüfungsdaten für Modul {mb.modul_id}: {e}")
                module_dict['modulbuchung_id'] = None
                module_dict['pruefungsdatum'] = None
        else:
            module_dict['modulbuchung_id'] = None
            module_dict['pruefungsdatum'] = None

        return module_dict

    def __validate_wahlmodul_booking(
            self,
            con: sqlite3.Connection,
            einschreibung_id: int,
            studiengang_id: int,
            modul_id: int,
            wahlbereich: str,
            semester: int
    ) -> dict:
        """PRIVATE: Validiert ob Wahlmodul gebucht werden darf

        Regeln:
        - Pro Wahlbereich nur 1 Modul
        - Modul aus C darf nicht identisch mit bereits gebuchtem aus A sein
        """
        # 1. Prüfe ob im Wahlbereich bereits ein Modul gebucht ist
        bereits_gebucht = con.execute(
            """SELECT m.name
               FROM modulbuchung mb
               JOIN studiengang_modul sgm ON sgm.modul_id = mb.modul_id
                                         AND sgm.studiengang_id = ?
               JOIN modul m ON m.id = mb.modul_id
               WHERE mb.einschreibung_id = ?
                 AND sgm.wahlbereich = ?
                 AND sgm.semester = ?""",
            (studiengang_id, einschreibung_id, wahlbereich, semester)
        ).fetchone()

        if bereits_gebucht:
            return {
                'success': False,
                'error': f"Im Wahlbereich {wahlbereich} (Semester {semester}) "
                         f"wurde bereits '{bereits_gebucht[0]}' gebucht. "
                         f"Pro Wahlbereich ist nur 1 Modul erlaubt."
            }

        # 2. Für Wahlbereich C: Prüfe ob Modul bereits in A gebucht wurde
        if wahlbereich == 'C':
            modul_in_a = con.execute(
                """SELECT mb.id
                   FROM modulbuchung mb
                   JOIN studiengang_modul sgm ON sgm.modul_id = mb.modul_id
                                             AND sgm.studiengang_id = ?
                   WHERE mb.einschreibung_id = ?
                     AND mb.modul_id = ?
                     AND sgm.wahlbereich = 'A'""",
                (studiengang_id, einschreibung_id, modul_id)
            ).fetchone()

            if modul_in_a:
                return {
                    'success': False,
                    'error': "Dieses Modul wurde bereits in Wahlbereich A gebucht. "
                             "Im Wahlbereich C muss ein anderes Modul gewählt werden."
                }

        return {'success': True}