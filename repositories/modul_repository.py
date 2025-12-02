# -*- coding: utf-8 -*-
# repositories/modul_repository.py
from __future__ import annotations
import sqlite3
import logging
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModulDTO:
    """Data Transfer Object: Modul mit Buchungsstatus fuer View-Ebene

    HINWEIS: Dies ist KEIN Domain Model, sondern ein DTO fuer die API/View!
    Kombiniert Modul-Daten mit dem Buchungsstatus fuer ein Semester.
    """
    modul_id: int
    name: str
    ects: int
    pflichtgrad: str  # 'Pflicht' oder 'Wahl'
    semester: int
    status: str  # 'offen', 'gebucht', 'bestanden', 'nicht_bestanden', 'anerkannt'
    buchbar: bool
    note: float | None = None
    wahlbereich: str | None = None  # 'A', 'B', 'C' oder None fuer Pflichtmodule
    erlaubte_pruefungsarten: List[dict] | None = None  # [{wert, anzeigename, hat_unterteilung}]

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary fuer JSON"""
        return {
            'modul_id': self.modul_id,
            'name': self.name,
            'ects': self.ects,
            'pflichtgrad': self.pflichtgrad,
            'semester': self.semester,
            'status': self.status,
            'buchbar': self.buchbar,
            'note': float(self.note) if self.note else None,
            'wahlbereich': self.wahlbereich,
            'erlaubte_pruefungsarten': self.erlaubte_pruefungsarten or []
        }

    def is_wahlmodul(self) -> bool:
        """Prueft ob es sich um ein Wahlmodul handelt"""
        return self.wahlbereich is not None


class ModulRepository:
    """Repository fÃƒÂ¼r Modul-Datenbankzugriff

    Verantwortlich fÃƒÂ¼r:
    - Laden von Modulen mit Buchungsstatus pro Student
    - Aggregation von Daten aus modul, modulbuchung, pruefungsleistung
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    # ========== PUBLIC Methods ==========

    def get_modules_for_semester(
            self,
            studiengang_id: int,
            semester: int,
            student_id: int
    ) -> List[ModulDTO]:
        """PUBLIC: Holt alle Module eines Semesters mit Buchungsstatus

        Args:
            studiengang_id: ID des Studiengangs
            semester: Semesternummer (1-7)
            student_id: ID des Studenten (fÃƒÂ¼r Buchungsstatus)

        Returns:
            Liste von ModulDTO-Objekten (fÃƒÂ¼r View-Ebene)
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                # Ã¢Å“â€¦ KORRIGIERT: pl.modulbuchung_id = mb.id statt pl.id = mb.id
                rows = con.execute("""
                                   SELECT m.id    as modul_id,
                                          m.name,
                                          m.ects,
                                          sgm.pflichtgrad,
                                          sgm.wahlbereich,
                                          sgm.semester,
                                          CASE
                                              WHEN pl.note IS NOT NULL AND pl.note <= 4.0 THEN 'bestanden'
                                              WHEN pl.note IS NOT NULL THEN 'nicht_bestanden'
                                              WHEN mb.status IS NOT NULL THEN mb.status
                                              ELSE 'offen'
                                              END as status,
                                          pl.note,
                                          CASE
                                              WHEN pl.id IS NOT NULL THEN 0
                                              WHEN mb.id IS NOT NULL THEN 0
                                              ELSE 1
                                              END as buchbar
                                   FROM modul m
                                            JOIN studiengang_modul sgm ON sgm.modul_id = m.id
                                            LEFT JOIN (SELECT mb.*
                                                       FROM modulbuchung mb
                                                                JOIN einschreibung e ON mb.einschreibung_id = e.id
                                                       WHERE e.student_id = ?) mb ON mb.modul_id = m.id
                                            LEFT JOIN pruefungsleistung pl ON pl.modulbuchung_id = mb.id
                                   WHERE sgm.studiengang_id = ?
                                     AND sgm.semester = ?
                                   ORDER BY sgm.pflichtgrad DESC, sgm.wahlbereich, m.name
                                   """, (student_id, studiengang_id, semester)).fetchall()

                # Konvertiere Rows und fÃƒÂ¼ge PrÃƒÂ¼fungsarten hinzu
                modules = []
                for row in rows:
                    module = self.__row_to_modul_dto(row)
                    # Lade erlaubte PrÃƒÂ¼fungsarten fÃƒÂ¼r dieses Modul
                    module.erlaubte_pruefungsarten = self.__get_erlaubte_pruefungsarten(module.modul_id, con)
                    modules.append(module)

                return modules

        except sqlite3.Error as e:
            logger.exception("DB-Fehler beim Laden der Module")
            raise

    def get_gebuchte_wahlmodule(
            self,
            student_id: int,
            studiengang_id: int
    ) -> dict:
        """PUBLIC: Holt alle bereits gebuchten/bestandenen Wahlmodule eines Studenten

        Returns:
            Dictionary mit Struktur:
            {
                'A': {'modul_id': 123, 'name': 'Modulname', 'status': 'bestanden', 'note': 1.7} oder None,
                'B': {'modul_id': 456, 'name': 'Modulname', 'status': 'gebucht', 'note': None} oder None,
                'C': {'modul_id': 789, 'name': 'Modulname', 'status': 'bestanden', 'note': 2.0} oder None,
                'gebuchte_modul_ids': [123, 456, 789]
            }
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                rows = con.execute("""
                                   SELECT sgm.wahlbereich,
                                          m.id as modul_id,
                                          m.name,
                                          mb.status,
                                          pl.note
                                   FROM modulbuchung mb
                                            JOIN einschreibung e ON mb.einschreibung_id = e.id
                                            JOIN modul m ON m.id = mb.modul_id
                                            JOIN studiengang_modul sgm ON sgm.modul_id = m.id
                                       AND sgm.studiengang_id = e.studiengang_id
                                            LEFT JOIN pruefungsleistung pl ON pl.modulbuchung_id = mb.id
                                   WHERE e.student_id = ?
                                     AND e.studiengang_id = ?
                                     AND sgm.wahlbereich IS NOT NULL
                                   ORDER BY sgm.wahlbereich
                                   """, (student_id, studiengang_id)).fetchall()

                result = {
                    'A': None,
                    'B': None,
                    'C': None,
                    'gebuchte_modul_ids': []
                }

                for row in rows:
                    wahlbereich = row['wahlbereich']
                    modul_info = {
                        'modul_id': row['modul_id'],
                        'name': row['name'],
                        'status': row['status'],
                        'note': float(row['note']) if row['note'] else None
                    }

                    if wahlbereich in result and result[wahlbereich] is None:
                        result[wahlbereich] = modul_info

                    result['gebuchte_modul_ids'].append(row['modul_id'])

                return result

        except sqlite3.Error as e:
            logger.exception("DB-Fehler beim Laden der gebuchten Wahlmodule")
            raise

    def get_available_wahlmodule(
            self,
            studiengang_id: int,
            wahlbereich: str,
            exclude_modul_ids: List[int] = None
    ) -> List[dict]:
        """PUBLIC: Holt verfuegbare Wahlmodule fuer einen Wahlbereich

        Args:
            studiengang_id: ID des Studiengangs
            wahlbereich: 'A', 'B' oder 'C'
            exclude_modul_ids: Liste von Modul-IDs die ausgeschlossen werden sollen

        Returns:
            Liste von Dictionaries mit {modul_id, name, ects}
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                query = """
                        SELECT m.id as modul_id, m.name, m.ects
                        FROM modul m
                                 JOIN studiengang_modul sgm ON sgm.modul_id = m.id
                        WHERE sgm.studiengang_id = ?
                          AND sgm.wahlbereich = ? \
                        """
                params = [studiengang_id, wahlbereich]

                if exclude_modul_ids:
                    placeholders = ','.join(['?' for _ in exclude_modul_ids])
                    query += f" AND m.id NOT IN ({placeholders})"
                    params.extend(exclude_modul_ids)

                query += " ORDER BY m.name"

                rows = con.execute(query, params).fetchall()

                return [
                    {
                        'modul_id': row['modul_id'],
                        'name': row['name'],
                        'ects': row['ects']
                    }
                    for row in rows
                ]

        except sqlite3.Error as e:
            logger.exception(f"DB-Fehler beim Laden der Wahlmodule fuer Bereich {wahlbereich}")
            raise

    # ========== PRIVATE Methods ==========

    @staticmethod
    def __row_to_modul_dto(row) -> ModulDTO:
        """PRIVATE: Konvertiert DB-Row zu ModulDTO"""
        return ModulDTO(
            modul_id=int(row['modul_id']),
            name=str(row['name']),
            ects=int(row['ects']),
            pflichtgrad=str(row['pflichtgrad']),
            semester=int(row['semester']),
            status=str(row['status']),
            buchbar=bool(row['buchbar']),
            note=float(row['note']) if row['note'] else None,
            wahlbereich=str(row['wahlbereich']) if row['wahlbereich'] else None
        )

    def __get_erlaubte_pruefungsarten(self, modul_id: int, con: sqlite3.Connection) -> List[dict]:
        """PRIVATE: Holt erlaubte PrÃƒÂ¼fungsarten fÃƒÂ¼r ein Modul

        Args:
            modul_id: ID des Moduls
            con: Aktive Datenbankverbindung

        Returns:
            Liste von Dictionaries mit {wert, anzeigename, hat_unterteilung, ist_standard}
        """
        try:
            con.row_factory = sqlite3.Row
            rows = con.execute("""
                               SELECT LOWER(pa.kuerzel) as wert,
                                      pa.anzeigename,
                                      pa.hat_unterteilung,
                                      mpa.ist_standard
                               FROM modul_pruefungsart mpa
                                        JOIN pruefungsart pa ON pa.id = mpa.pruefungsart_id
                               WHERE mpa.modul_id = ?
                               ORDER BY mpa.reihenfolge, mpa.ist_standard DESC
                               """, (modul_id,)).fetchall()

            if rows:
                return [
                    {
                        'wert': row['wert'],
                        'anzeigename': row['anzeigename'],
                        'hat_unterteilung': bool(row['hat_unterteilung']),
                        'ist_standard': bool(row['ist_standard'])
                    }
                    for row in rows
                ]
            else:
                # Fallback: Wenn keine PrÃƒÂ¼fungsarten definiert, nehme Klausur als Standard
                logger.warning(
                    f"Keine PrÃƒÂ¼fungsarten fÃƒÂ¼r Modul {modul_id} gefunden - verwende Klausur als Fallback")
                return [{
                    'wert': 'klausur',
                    'anzeigename': 'Klausur',
                    'hat_unterteilung': True,
                    'ist_standard': True
                }]

        except Exception as e:
            logger.error(f"Fehler beim Laden der PrÃƒÂ¼fungsarten fÃƒÂ¼r Modul {modul_id}: {e}")
            # Bei Fehler: Fallback auf Klausur
            return [{
                'wert': 'klausur',
                'anzeigename': 'Klausur',
                'hat_unterteilung': True,
                'ist_standard': True
            }]

    def __get_connection(self) -> sqlite3.Connection:
        """PRIVATE: Erstellt Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn