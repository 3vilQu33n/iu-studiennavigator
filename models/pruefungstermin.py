# models/pruefungstermin.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, time, datetime
from typing import Optional


@dataclass
class Pruefungstermin:
    """Domain Model: Prüfungstermin

    Repräsentiert einen Prüfungstermin für ein Modul.
    Verschiedene Arten: online, praesenz, projekt, workbook
    """
    id: int
    modul_id: int
    datum: date
    beginn: Optional[time] = None
    ende: Optional[time] = None
    art: str = 'online'  # 'online', 'praesenz', 'projekt', 'workbook'
    ort: Optional[str] = None
    anmeldeschluss: Optional[datetime] = None
    kapazitaet: Optional[int] = None
    beschreibung: Optional[str] = None

    def __post_init__(self):
        """Typ-Konvertierung"""
        if isinstance(self.datum, str):
            self.datum = date.fromisoformat(self.datum)

        if self.beginn and isinstance(self.beginn, str):
            # Zeit kann im Format "HH:MM" oder "HH:MM:SS" kommen
            self.beginn = time.fromisoformat(self.beginn)

        if self.ende and isinstance(self.ende, str):
            self.ende = time.fromisoformat(self.ende)

        if self.anmeldeschluss and isinstance(self.anmeldeschluss, str):
            self.anmeldeschluss = datetime.fromisoformat(self.anmeldeschluss)

    # ========== PUBLIC Methods ==========

    def ist_online_pruefung(self) -> bool:
        """PUBLIC: Prüft ob es eine Online-Prüfung ist"""
        return self.art == 'online'

    def ist_praesenz_pruefung(self) -> bool:
        """PUBLIC: Prüft ob es eine Präsenz-Prüfung ist"""
        return self.art == 'praesenz'

    def ist_projekt(self) -> bool:
        """PUBLIC: Prüft ob es ein Projekt/Workbook ist"""
        return self.art in ('projekt', 'workbook')

    def hat_zeitfenster(self) -> bool:
        """PUBLIC: Prüft ob Termin ein festes Zeitfenster hat"""
        return self.beginn is not None and self.ende is not None

    def hat_kapazitaet(self) -> bool:
        """PUBLIC: Prüft ob Termin Kapazitätsbeschränkung hat"""
        return self.kapazitaet is not None

    def ist_anmeldeschluss_vorbei(self) -> bool:
        """PUBLIC: Prüft ob Anmeldeschluss vorbei ist"""
        if not self.anmeldeschluss:
            return False
        return datetime.now() > self.anmeldeschluss

    def ist_in_zukunft(self) -> bool:
        """PUBLIC: Prüft ob Termin in der Zukunft liegt"""
        return self.datum >= date.today()

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary für JSON"""
        return {
            'id': self.id,
            'modul_id': self.modul_id,
            'datum': self.datum.isoformat(),
            'beginn': self.beginn.isoformat() if self.beginn else None,
            'ende': self.ende.isoformat() if self.ende else None,
            'art': self.art,
            'ort': self.ort,
            'anmeldeschluss': self.anmeldeschluss.isoformat() if self.anmeldeschluss else None,
            'kapazitaet': self.kapazitaet,
            'beschreibung': self.beschreibung,
            'ist_online': self.ist_online_pruefung(),
            'ist_praesenz': self.ist_praesenz_pruefung(),
            'ist_projekt': self.ist_projekt(),
            'hat_zeitfenster': self.hat_zeitfenster(),
            'anmeldeschluss_vorbei': self.ist_anmeldeschluss_vorbei(),
            'ist_in_zukunft': self.ist_in_zukunft()
        }

    @classmethod
    def from_row(cls, row) -> "Pruefungstermin":
        """PUBLIC: Factory Method - Erstellt Pruefungstermin aus DB-Row

        Verwendet try/except für alle optionalen Felder da sqlite3.Row kein .get() hat.
        """
        try:
            datum = date.fromisoformat(row['datum']) if isinstance(row['datum'], str) else row['datum']
        except (KeyError, TypeError, ValueError):
            datum = date.today()

        try:
            if row['beginn']:
                beginn = time.fromisoformat(row['beginn']) if isinstance(row['beginn'], str) else row['beginn']
            else:
                beginn = None
        except (KeyError, TypeError, ValueError):
            beginn = None

        try:
            if row['ende']:
                ende = time.fromisoformat(row['ende']) if isinstance(row['ende'], str) else row['ende']
            else:
                ende = None
        except (KeyError, TypeError, ValueError):
            ende = None

        try:
            art = str(row['art'])
        except (KeyError, TypeError):
            art = 'online'

        try:
            ort = row['ort'] if row['ort'] else None
        except (KeyError, TypeError):
            ort = None

        try:
            if row['anmeldeschluss']:
                anmeldeschluss = datetime.fromisoformat(row['anmeldeschluss']) if isinstance(row['anmeldeschluss'],
                                                                                             str) else row[
                    'anmeldeschluss']
            else:
                anmeldeschluss = None
        except (KeyError, TypeError, ValueError):
            anmeldeschluss = None

        try:
            kapazitaet = int(row['kapazitaet']) if row['kapazitaet'] else None
        except (KeyError, TypeError, ValueError):
            kapazitaet = None

        try:
            beschreibung = row['beschreibung'] if row['beschreibung'] else None
        except (KeyError, TypeError):
            beschreibung = None

        return cls(
            id=int(row['id']),
            modul_id=int(row['modul_id']),
            datum=datum,
            beginn=beginn,
            ende=ende,
            art=art,
            ort=ort,
            anmeldeschluss=anmeldeschluss,
            kapazitaet=kapazitaet,
            beschreibung=beschreibung
        )

    # ========== String Representation ==========

    def __str__(self) -> str:
        zeit_str = f"{self.beginn.strftime('%H:%M')}-{self.ende.strftime('%H:%M')}" if self.hat_zeitfenster() else "ohne Zeit"
        return f"Pruefungstermin({self.art}, {self.datum}, {zeit_str})"

    def __repr__(self) -> str:
        return (f"Pruefungstermin(id={self.id}, modul_id={self.modul_id}, "
                f"datum={self.datum}, art={self.art})")