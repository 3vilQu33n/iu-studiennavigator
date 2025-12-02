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

    Auto-Positionierung erfolgt clientseitig via JavaScript aus SVG-Pfaden.
    """

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
                # Position basierend auf Fortschritt
                current_semester = self.__calculate_semester_by_progress(student.id, einschreibung_id)

                # Fuer Progress-Anzeige: Zeit-basiert (SOLL-Semester)
                expected_semester = student.calculate_semester(einschreibung)
                logger.info(
                    f"📊 Auto-Position: {current_semester:.1f}, SOLL-Semester (Zeit): {expected_semester:.1f}")
            else:
                current_semester = 1.0  # Fallback: Position 1
                expected_semester = 1
                logger.warning(f"Verwende Fallback-Position 1.0 fuer Student {student.id}")

            # Berechne max_semester basierend auf Zeitmodell
            if einschreibung:
                # Zeitmodell aus DB laden
                with sqlite3.connect(self.db_path) as con:
                    con.row_factory = sqlite3.Row
                    zeitmodell_result = con.execute(
                        "SELECT name FROM zeitmodell WHERE id = ?",
                        (einschreibung.zeitmodell_id,)
                    ).fetchone()

                    if zeitmodell_result:
                        zeitmodell_name = zeitmodell_result['name']
                        if zeitmodell_name == 'Teilzeit I':
                            max_semester = 8
                        elif zeitmodell_name == 'Teilzeit II':
                            max_semester = 10
                        else:
                            max_semester = 7
                    else:
                        max_semester = 7
            else:
                max_semester = 7

            # 4. Progress-Daten laden (optional - Fehler hier sollten nicht kritisch sein)
            try:
                if einschreibung:
                    progress = self.__progress_repo.get_progress_for_student(student, einschreibung.id)
                else:
                    progress = None
            except Exception as e:
                logger.warning(f"Konnte Progress nicht laden: {e}")
                progress = None  # Fahre ohne Progress fort

            # 5. Progress-Texte generieren
            if progress:
                progress_texts = self.__progress_text_service.get_all_texts(progress)
                grade_text = progress_texts['grade']
                time_text = progress_texts['time']
                fee_text = progress_texts['fee']
                grade_category = progress_texts['category']
                time_status = progress_texts['time_status']
            else:
                grade_text = 'Keine Daten'
                time_text = 'Keine Daten'
                fee_text = 'Keine Gebuehren'
                grade_category = 'medium'
                time_status = 'plus'

            # 6. Naechste Pruefung
            next_exam = self.get_next_exam(login_id)

            # Template-Variablen
            return {
                # Student-Daten
                'student': student.to_dict(),
                'student_id': student.id,
                'student_name': f"{student.vorname} {student.nachname}",

                # Semester-Position (Auto-Positionierung erfolgt clientseitig via JS)
                'current_semester': current_semester,
                'max_semester': max_semester,

                # Progress-Texte
                'progress_grade': grade_text,
                'progress_time': time_text,
                'progress_fee': fee_text,
                'grade_category': grade_category,
                'time_status': time_status,

                # Naechste Pruefung
                'next_exam': next_exam,

                # Dashboard-Bild (statisch)
                'image_svg': 'Infotainment.svg',
                'original_image': 'Infotainment.svg',

                # Debug-Info
                'debug_info': {
                    'actual_semester': current_semester,
                    'expected_semester': expected_semester,
                    'semester_diff': current_semester - expected_semester if expected_semester else 0,
                    'progress_available': progress is not None
                }
            }

        except Exception as e:
            logger.exception(f"Fehler beim Laden der Dashboard-Daten: {e}")

            # Fallback-Daten
            return {
                'student': None,
                'student_id': None,
                'student_name': 'Unbekannt',
                'current_semester': 1,
                'max_semester': 7,
                'progress_grade': 'Fehler',
                'progress_time': 'Fehler',
                'progress_fee': 'Fehler',
                'grade_category': 'medium',
                'time_status': 'plus',
                'next_exam': None,
                'image_svg': 'Infotainment.svg',
                'original_image': 'Infotainment.svg',
                'debug_info': {
                    'error': str(e)
                }
            }

    def get_next_exam(self, login_id: int) -> Optional[dict]:
        """PUBLIC: Liefert die naechste anstehende Pruefung

        Args:
            login_id: ID aus login-Tabelle (current_user.id)

        Returns:
            Dictionary mit Pruefungsdaten oder None
        """
        try:
            student = self.__student_repo.get_by_login_id(login_id)
            if not student:
                return None

            with sqlite3.connect(self.db_path) as con:
                con.row_factory = sqlite3.Row

                result = con.execute("""
                                     SELECT m.name as modul_name,
                                            pt.datum,
                                            pt.beginn,
                                            pt.ende,
                                            pt.ort,
                                            pt.art
                                     FROM pruefungsanmeldung pa
                                              JOIN pruefungstermin pt ON pt.id = pa.pruefungstermin_id
                                              JOIN modulbuchung mb ON mb.id = pa.modulbuchung_id
                                              JOIN modul m ON m.id = mb.modul_id
                                              JOIN einschreibung e ON e.id = mb.einschreibung_id
                                     WHERE e.student_id = ?
                                       AND pa.status = 'angemeldet'
                                       AND pt.datum >= DATE('now')
                                     ORDER BY pt.datum ASC
                                     LIMIT 1
                                     """, (student.id,)).fetchone()

                if not result:
                    return None

                # Tage bis zur Pruefung berechnen
                pruefungsdatum = datetime.strptime(result['datum'], '%Y-%m-%d').date()
                heute = date.today()
                tage_bis = (pruefungsdatum - heute).days

                # Zeit formatieren
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

    def get_current_semester(self, login_id: int) -> Optional[int]:
        """PUBLIC: Liefert das aktuelle Semester basierend auf Fortschritt

        Args:
            login_id: ID aus login-Tabelle (current_user.id)

        Returns:
            Semester als Integer (1-7) oder None bei Fehler
        """
        try:
            # Student laden
            student = self.__student_repo.get_by_login_id(login_id)
            if not student:
                return None

            # Aktive Einschreibung laden
            einschreibung = self.__einschreibung_repo.get_aktive_by_student(student.id)
            if not einschreibung:
                return 1  # Fallback: Semester 1

            # Verwende die Positions-Logik um das Semester zu bestimmen
            position = self.__calculate_semester_by_progress(student.id, einschreibung.id)

            # Position zu Semester umrechnen (grob)
            if position < 2:
                return 1
            elif position < 3:
                return 2
            elif position < 4:
                return 3
            elif position < 5:
                return 4
            elif position < 6:
                return 5
            elif position < 6.5:
                return 6
            else:
                return 7

        except Exception as e:
            logger.exception(f"Fehler beim Ermitteln des aktuellen Semesters: {e}")
            return None

    # ========== PRIVATE Helper Methods ==========

    def __calculate_semester_by_progress(self, student_id: int, einschreibung_id: int) -> float:
        """PRIVATE: Berechnet die AUTO-POSITION basierend auf Fortschritt

        KORREKTE LOGIK (laut User-Zeichnung):
        - Position 1 = arbeitet an Semester 1
        - Position 2 = arbeitet an Semester 2 (Semester 1 komplett)
        - Position 3 = arbeitet an Semester 3 (Semester 2 komplett)
        - etc.

        Teresa: Semester 1 komplett + 1/4 aus Sem 2 = Position 2.25

        Args:
            student_id: Student ID
            einschreibung_id: Einschreibungs ID

        Returns:
            Position als Float (1.0 - 7.0)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Hole detaillierten Fortschritt pro Semester
                semester_progress = conn.execute("""
                                                 SELECT sgm.semester,
                                                        COUNT(DISTINCT sgm.modul_id) as gesamt,
                                                        COUNT(DISTINCT CASE
                                                                           WHEN mb.status IN ('bestanden', 'anerkannt')
                                                                               THEN mb.modul_id
                                                            END)                     as abgeschlossen
                                                 FROM studiengang_modul sgm
                                                          JOIN einschreibung e ON e.id = ?
                                                          LEFT JOIN modulbuchung mb
                                                                    ON mb.modul_id = sgm.modul_id
                                                                        AND mb.einschreibung_id = e.id
                                                 WHERE sgm.studiengang_id = e.studiengang_id
                                                 GROUP BY sgm.semester
                                                 ORDER BY sgm.semester
                                                 """, (einschreibung_id,)).fetchall()

                # Start bei Position 1 (arbeitet an Semester 1)
                position = 1.0

                for row in semester_progress:
                    semester_nr = row[0]
                    gesamt = row[1]
                    abgeschlossen = row[2]

                    if gesamt == 0:
                        continue

                    fortschritt = abgeschlossen / gesamt

                    # Spezialbehandlung für Wahlmodule
                    if semester_nr == 5:
                        # Nur 1 Wahlmodul nötig
                        if abgeschlossen >= 1:
                            fortschritt = 1.0
                    elif semester_nr == 6:
                        # Nur 2 Wahlmodule nötig
                        if abgeschlossen >= 2:
                            fortschritt = 1.0

                    logger.info(f"  Semester {semester_nr}: {abgeschlossen}/{gesamt} "
                                f"({fortschritt * 100:.0f}%)")

                    if fortschritt >= 1.0:
                        # Semester komplett → Auto springt zur nächsten Position
                        # Semester 1 komplett → Position 2
                        # Semester 2 komplett → Position 3, etc.
                        position = float(semester_nr + 1)
                    else:
                        # Teilfortschritt im aktuellen Semester
                        # Position = Semester-Nummer + Fortschritt
                        position = float(semester_nr) + fortschritt
                        break  # Stoppe beim ersten unvollständigen Semester

                # Begrenze auf gültigen Bereich (max Position 7)
                position = min(position, 7.0)

                logger.info(
                    f"📊 Auto-Position für Student {student_id}: {position:.2f}\n"
                    f"  (Position = aktuelles Arbeitssemester)"
                )

                return position

        except Exception as e:
            logger.error(f"Fehler bei Positionsberechnung: {e}")
            return 1.0  # Fallback: Start-Position