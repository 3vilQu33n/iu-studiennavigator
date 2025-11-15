# controllers/dashboard_controller.py
from __future__ import annotations
from typing import Optional
import logging
import sqlite3
from datetime import datetime, date
from repositories import StudentRepository, EinschreibungRepository, ProgressRepository
from services import ProgressTextService

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')


class DashboardController:
    """Controller fuer Dashboard-Logik

    Koordiniert Repositories und Services fuer die Dashboard-Ansicht.
    Alle Methoden sind PUBLIC, da sie von Flask-Routes aufgerufen werden.
    """

    # Semester-Positionen (aus Phase 1)
    SEMESTER_POSITIONS = {
        1: {"x_percent": 0.364, "y_percent": 0.279, "angle": -7, "flip": False},
        2: {"x_percent": 0.800, "y_percent": 0.318, "angle": 10, "flip": False},
        3: {"x_percent": 0.647, "y_percent": 0.425, "angle": 0, "flip": True},
        4: {"x_percent": 0.277, "y_percent": 0.512, "angle": -10, "flip": True},
        5: {"x_percent": 0.208, "y_percent": 0.715, "angle": 0, "flip": False},
        6: {"x_percent": 0.531, "y_percent": 0.706, "angle": 0, "flip": False},
        7: {"x_percent": 0.729, "y_percent": 0.720, "angle": 0, "flip": False},
    }

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.__student_repo = StudentRepository(db_path)
        self.__einschreibung_repo = EinschreibungRepository(db_path)
        self.__progress_repo = ProgressRepository(db_path)
        self.__progress_text_service = ProgressTextService()

    # ========== PUBLIC Methods ==========

    def get_student_by_auth_user(self, login_id: int) -> Optional[dict]:
        """PUBLIC: Holt Student-Daten fuer eingeloggten User

        Args:
            login_id: ID des auth_user (aus Flask-Login)

        Returns:
            Dictionary mit Student-Daten oder None
        """
        try:
            student = self.__student_repo.get_by_login_id(login_id)
            if not student:
                return None

            return student.to_dict()
        except Exception as e:
            logger.exception(f"Fehler beim Laden des Students: {e}")
            return None

    def get_dashboard_data(self, login_id: int) -> dict:
        """PUBLIC: Liefert alle Daten fuer die Dashboard-Ansicht

        Args:
            login_id: ID des auth_user (aus Flask-Login)

        Returns:
            Dictionary mit allen Template-Variablen
        """
        try:
            # 1. Student laden
            student = self.__student_repo.get_by_login_id(login_id)
            if not student:
                raise ValueError("Kein Student zu diesem Login gefunden")

            # 2. Aktive Einschreibung laden
            try:
                einschreibung = self.__einschreibung_repo.get_aktive_by_student(student.id)
                einschreibung_id = einschreibung.id
            except ValueError:
                # Keine aktive Einschreibung - Progress mit Nullwerten
                einschreibung = None
                einschreibung_id = None
                logger.warning(f"Keine aktive Einschreibung fuer Student {student.id}")

            # 3. Aktuelles Semester berechnen (FORTSCHRITTSBASIERT)
            if einschreibung:
                # âœ… NEU: Fortschrittsbasiert (hoechstes gebuchtes/bestandenes Semester)
                current_semester = self.__calculate_semester_by_progress(student.id, einschreibung_id)

                # Fuer Progress-Anzeige: Zeit-basiert (SOLL-Semester)
                expected_semester = student.calculate_semester(einschreibung)
                logger.info(
                    f"ðŸ“Š IST-Semester (Fortschritt): {current_semester:.1f}, SOLL-Semester (Zeit): {expected_semester:.1f}")
            else:
                current_semester = 1.0  # Fallback: Position 1
                expected_semester = 1
                logger.warning(f"Verwende Fallback-Semester 1.0 fuer Student {student.id}")

            # Berechne max_semester basierend auf Zeitmodell
            try:
                if einschreibung:
                    with sqlite3.connect(self.db_path) as conn:
                        zeitmodell_row = conn.execute(
                            "SELECT dauer_monate FROM zeitmodell WHERE id = ?",
                            (einschreibung.zeitmodell_id,)
                        ).fetchone()

                        if zeitmodell_row:
                            dauer_monate = zeitmodell_row[0]
                            max_semester = int(dauer_monate / 6) + 1
                        else:
                            max_semester = 7  # Fallback
                else:
                    max_semester = 7  # Fallback wenn keine Einschreibung
            except Exception as e:
                logger.error(f"Fehler beim Berechnen max_semester: {e}")
                max_semester = 7

            # 4. Auto-Position berechnen (âœ… FESTE Position, keine Interpolation)
            car_pos = self.__calculate_car_position(current_semester)

            logger.info(
                f"ðŸš— Auto-Position: Semester {current_semester:.1f} â†’ Position {car_pos['x_percent']:.3f}, {car_pos['y_percent']:.3f}")

            # 5. Progress-Daten laden (falls Einschreibung vorhanden)
            time_status = 'plus'  # Default

            if einschreibung_id:
                # ProgressRepository gibt bereits ein Progress-Objekt zurueck!
                progress_obj = self.__progress_repo.get_progress_for_student(student, einschreibung_id)

                # Progress-Texte direkt aus Objekt generieren
                try:
                    progress_texts = self.__progress_text_service.get_all_texts(progress_obj, lang='de')

                    # NEU: Zeit-Status aus Progress-Dict berechnen
                    try:
                        progress_dict = progress_obj.to_dict()
                        days_delta = progress_dict['tage_differenz']

                        logger.info(f"â±ï¸ Zeitdifferenz: {days_delta} Tage")

                        if days_delta > 20:
                            time_status = 'ahead'  # Gruen - Akku voll (>20 Tage voraus)
                        elif days_delta >= 0:
                            time_status = 'plus'  # Blau - AC-Laden (0-20 Tage Puffer)
                        else:
                            time_status = 'minus'  # Rot - DC-Schnellladen (Verzug!)

                        logger.info(f"ðŸ”‹ time_status = '{time_status}' (days_delta = {days_delta})")
                    except Exception as e:
                        logger.warning(f"Zeit-Status konnte nicht berechnet werden: {e}")
                        time_status = 'plus'

                except Exception as e:
                    logger.warning(f"Progress-Texte konnten nicht generiert werden: {e}")
                    progress_texts = {
                        'grade': 'Keine Daten',
                        'time': 'Keine Daten',
                        'fee': 'Keine Gebuehren',
                        'category': 'medium'
                    }
            else:
                # Fallback ohne Einschreibung
                progress_texts = {
                    'grade': 'Noch keine Noten',
                    'time': 'Gerade gestartet',
                    'fee': 'Keine Gebuehren',
                    'category': 'medium'
                }

            # âœ… Naechste Pruefung laden
            next_exam = self.get_next_exam(login_id)

            return {
                'student_name': student.get_full_name(),
                'student_id': student.id,
                'current_semester': current_semester,
                'max_semester': max_semester,
                'car_x_percent': car_pos['x_percent'],
                'car_y_percent': car_pos['y_percent'],
                'car_rotation': car_pos['rotation'],
                'car_flip': car_pos['flip'],
                'progress_grade': progress_texts['grade'],
                'progress_time': progress_texts['time'],
                'progress_fee': progress_texts['fee'],
                'grade_category': progress_texts['category'],
                'time_status': time_status,
                'next_exam': next_exam,
                'image_svg': 'Infotainment.svg',
                'original_image': 'Infotainment.svg'
            }

        except Exception as e:
            logger.exception(f"Fehler beim Laden der Dashboard-Daten: {e}")
            # Fallback-Daten
            return {
                'student_name': 'Unbekannt',
                'student_id': None,
                'current_semester': 1.0,
                'max_semester': 7,
                'car_x_percent': 0.364,
                'car_y_percent': 0.279,
                'car_rotation': -7,
                'car_flip': False,
                'progress_grade': 'Keine Daten',
                'progress_time': 'Keine Daten',
                'progress_fee': 'Keine Gebuehren',
                'grade_category': 'medium',
                'time_status': 'plus',
                'next_exam': None,
                'image_svg': 'Infotainment.svg',
                'original_image': 'Infotainment.svg',
                'error': str(e)
            }

    def get_next_exam(self, login_id: int) -> Optional[dict]:
        """PUBLIC: Holt die naechste anstehende Pruefung

        Nutzt die neuen Tabellen: pruefungstermin und pruefungsanmeldung

        Args:
            login_id: ID aus login-Tabelle

        Returns:
            Dictionary mit {
                'modul_name': str,
                'datum': str (YYYY-MM-DD),
                'tage_bis_pruefung': int,
                'art': str,
                'beginn': str oder None,
                'ende': str oder None,
                'ort': str oder None
            } oder None wenn keine Pruefung ansteht
        """
        try:
            # Student laden
            student = self.__student_repo.get_by_login_id(login_id)
            if not student:
                return None

            # Aktive Einschreibung
            try:
                einschreibung = self.__einschreibung_repo.get_aktive_by_student(student.id)
            except ValueError:
                return None

            # Naechste Pruefung aus neuen Tabellen laden
            with sqlite3.connect(self.db_path) as con:
                con.row_factory = sqlite3.Row

                result = con.execute(
                    """
                    SELECT m.name as modul_name,
                           pt.datum,
                           pt.beginn,
                           pt.ende,
                           pt.art,
                           pt.ort
                    FROM pruefungsanmeldung pa
                             JOIN pruefungstermin pt ON pa.pruefungstermin_id = pt.id
                             JOIN modulbuchung mb ON pa.modulbuchung_id = mb.id
                             JOIN modul m ON mb.modul_id = m.id
                    WHERE mb.einschreibung_id = ?
                      AND pa.status = 'angemeldet'
                      AND pt.datum >= DATE('now')
                    ORDER BY pt.datum ASC, pt.beginn ASC
                    LIMIT 1
                    """,
                    (einschreibung.id,)
                ).fetchone()

                if not result:
                    return None

                # Tage bis Pruefung berechnen
                pruefungsdatum = datetime.strptime(result['datum'], '%Y-%m-%d').date()
                heute = date.today()
                tage_bis = (pruefungsdatum - heute).days

                # Zeitfenster formatieren (falls vorhanden)
                beginn_str = None
                ende_str = None
                if result['beginn']:
                    try:
                        beginn_str = datetime.strptime(result['beginn'], '%H:%M:%S').strftime('%H:%M')
                    except ValueError:
                        beginn_str = result['beginn']
                if result['ende']:
                    try:
                        ende_str = datetime.strptime(result['ende'], '%H:%M:%S').strftime('%H:%M')
                    except ValueError:
                        ende_str = result['ende']

                return {
                    'modul_name': result['modul_name'],
                    'datum': result['datum'],
                    'tage_bis_pruefung': tage_bis,
                    'art': result['art'],
                    'beginn': beginn_str,
                    'ende': ende_str,
                    'ort': result['ort']
                }

        except Exception as e:
            logger.exception(f"Fehler beim Laden der naechsten Pruefung: {e}")
            return None

    def get_car_position_for_semester(self, semester: float) -> dict:
        """PUBLIC: Berechnet Auto-Position fuer gegebenes Semester

        Args:
            semester: Semester als Float (z.B. 3.5)

        Returns:
            Dictionary mit x_percent, y_percent, angle, flip
        """
        return self.__calculate_car_position(semester)

    def get_current_semester_by_progress(self, login_id: int) -> Optional[int]:
        """PUBLIC: Ermittelt das aktuelle Semester basierend auf Fortschritt

        Diese Methode kann vom Frontend genutzt werden, um zu validieren,
        welche Semester fuer Modulbuchungen erlaubt sind.

        Args:
            login_id: ID aus login-Tabelle (current_user.id)

        Returns:
            Aktuelle Semesternummer (1-7) oder None bei Fehler
        """
        try:
            # Student laden
            student = self.__student_repo.get_by_login_id(login_id)
            if not student:
                return None

            # Aktive Einschreibung laden
            try:
                einschreibung = self.__einschreibung_repo.get_aktive_by_student(student.id)
            except ValueError:
                return 1  # Fallback: Semester 1

            # Berechne aktuelles Semester
            current_semester_float = self.__calculate_semester_by_progress(student.id, einschreibung.id)

            # Runde auf ganze Zahl
            current_semester = int(round(current_semester_float))

            logger.info(f"ðŸ“Š Aktuelles Semester fuer Student {student.id}: {current_semester}")

            return current_semester

        except Exception as e:
            logger.exception(f"Fehler beim Ermitteln des aktuellen Semesters: {e}")
            return None

    # ========== PRIVATE Helper Methods ==========

    def __calculate_semester_by_progress(self, student_id: int, einschreibung_id: int) -> float:
        """PRIVATE: Berechnet Semester basierend auf hoechstem KOMPLETT abgeschlossenen Semester

        Die Berechnung findet das hoechste Semester, das zu 100% abgeschlossen ist.
        Das Auto steht dann auf dem NAeCHSTEN Semester (= aktuell laufend).

        Rueckgabe: Ganzzahl-Semester (nutzt feste SEMESTER_POSITIONS)
        - Kein Semester komplett â†’ 1.0 (Position 1, Start)
        - Semester 1 komplett â†’ 2.0 (Position 2, aktuell in Semester 2)
        - Semester 2 komplett â†’ 3.0 (Position 3, aktuell in Semester 3)

        Args:
            student_id: Student ID
            einschreibung_id: Einschreibungs ID

        Returns:
            Semester als Float (1.0 - 7.0)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Finde hoechstes KOMPLETT abgeschlossenes Semester
                result = conn.execute("""
                                      SELECT MAX(semester) as hoechstes_komplett
                                      FROM (SELECT sgm.semester,
                                                   COUNT(DISTINCT sgm.modul_id)                 as gesamt,
                                                   COUNT(DISTINCT CASE
                                                                      WHEN mb.status IN ('bestanden', 'anerkannt')
                                                                          THEN mb.modul_id END) as abgeschlossen
                                            FROM studiengang_modul sgm
                                                     LEFT JOIN modulbuchung mb ON mb.modul_id = sgm.modul_id
                                                AND mb.einschreibung_id = ?
                                            WHERE sgm.studiengang_id = (SELECT studiengang_id
                                                                        FROM einschreibung
                                                                        WHERE id = ?)
                                            GROUP BY sgm.semester
                                            HAVING gesamt = abgeschlossen -- Nur komplett abgeschlossene Semester
                                           )
                                      """, (einschreibung_id, einschreibung_id)).fetchone()

                hoechstes_komplett = result[0] if result and result[0] else 0

                # Aktuelles Semester = Hoechstes komplett + 1
                semester = float(hoechstes_komplett + 1)

                # Max: Position 7
                semester = min(semester, 7.0)

                logger.info(
                    f"ðŸ“ˆ Semester {hoechstes_komplett} komplett abgeschlossen â†’ "
                    f"Auto bei Position {semester:.0f} (aktuell laufend)")

                return semester

        except Exception as e:
            logger.error(f"Fehler bei Fortschrittsberechnung: {e}")
            return 1.0  # Fallback: Position 1

    def __calculate_car_position(self, semester: float) -> dict:
        """PRIVATE: Gibt die FESTE Position fuer ein Semester zurueck

        âœ… KEINE INTERPOLATION MEHR - nutzt nur die festen SEMESTER_POSITIONS

        Args:
            semester: Semester als Float (z.B. 3.0)

        Returns:
            Dictionary mit x_percent, y_percent, rotation, flip
        """
        # âœ… Runde auf ganze Zahl
        semester_int = int(round(semester))

        # âœ… Nutze die feste Position
        position = self.SEMESTER_POSITIONS.get(semester_int, self.SEMESTER_POSITIONS[1])

        logger.info(f"ðŸš— Auto-Position: Semester {semester:.1f} â†’ Position {semester_int} ({position})")

        return {
            "x_percent": position["x_percent"],
            "y_percent": position["y_percent"],
            "rotation": position["angle"],
            "flip": position["flip"]
        }