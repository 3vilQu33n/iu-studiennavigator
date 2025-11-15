# models/pruefungsleistung.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
from models import Modulbuchung


@dataclass
class Pruefungsleistung(Modulbuchung):
    """Domain Model: Prüfungsleistung

    VERERBUNG: IST-EINE Modulbuchung mit zusätzlichen Prüfungsdaten
    POLYMORPHIE: Überschreibt to_dict() und fügt prüfungsspezifische Daten hinzu
    """
    # Zusätzliche Attribute (erweitern die Basisklasse)
    note: Optional[Decimal] = None
    pruefungsdatum: Optional[date] = None
    versuch: int = 1
    max_versuche: int = 3
    anmeldemodus: str = 'online'  # 'online' oder 'praesenz'
    thema: Optional[str] = None  # Bei mündlichen Prüfungen oder Bachelorarbeit

    def __post_init__(self):
        """Typ-Konvertierung"""
        super().__post_init__()  # Ruft Basisklassen-Methode auf

        if self.note is not None and not isinstance(self.note, Decimal):
            self.note = Decimal(str(self.note))

        if isinstance(self.pruefungsdatum, str):
            self.pruefungsdatum = date.fromisoformat(self.pruefungsdatum)

    # ========== PUBLIC Methods (POLYMORPHIE) ==========

    def has_grade(self) -> bool:
        """PUBLIC: Prüft ob eine Note vorhanden ist"""
        return self.note is not None

    def is_passed(self) -> bool:
        """PUBLIC: Überschreibt Basisklassen-Methode (POLYMORPHIE)

        Prüfungsleistung ist bestanden wenn Note <= 4.0
        """
        if self.note is None:
            return False
        return self.note <= Decimal('4.0')

    def can_retry(self) -> bool:
        """PUBLIC: Prüft ob Wiederholungsversuch möglich"""
        return self.versuch < self.max_versuche

    def get_grade_category(self) -> str:
        """PUBLIC: Kategorisiert Note für UI"""
        if self.note is None:
            return 'keine_note'
        elif self.note <= Decimal('2.0'):
            return 'sehr_gut'
        elif self.note <= Decimal('3.0'):
            return 'gut'
        elif self.note <= Decimal('4.0'):
            return 'bestanden'
        else:
            return 'nicht_bestanden'

    def to_dict(self) -> dict:
        """PUBLIC: Überschreibt Basisklassen-Methode (POLYMORPHIE)

        Erweitert die Basis-Dictionary um prüfungsspezifische Felder
        """
        # Hole Basis-Dictionary von Modulbuchung
        base_dict = super().to_dict()

        # Ergänze prüfungsspezifische Felder
        base_dict.update({
            'note': float(self.note) if self.note else None,
            'note_formatted': f"{self.note:.2f}" if self.note else "—",
            'pruefungsdatum': self.pruefungsdatum.isoformat() if self.pruefungsdatum else None,
            'versuch': self.versuch,
            'max_versuche': self.max_versuche,
            'anmeldemodus': self.anmeldemodus,
            'thema': self.thema,
            'has_grade': self.has_grade(),
            'can_retry': self.can_retry(),
            'grade_category': self.get_grade_category()
        })

        return base_dict

    @classmethod
    def from_row(cls, row) -> "Pruefungsleistung":
        """PUBLIC: Factory Method - Erstellt Prüfungsleistung aus DB-Row

        Verwendet try/except für alle optionalen Felder da sqlite3.Row kein .get() hat.
        """
        # Alle optionalen Felder mit try/except behandeln
        try:
            einschreibung_id = int(row['einschreibung_id'])
        except (KeyError, TypeError):
            einschreibung_id = 0

        try:
            modul_id = int(row['modul_id'])
        except (KeyError, TypeError):
            modul_id = 0

        try:
            if isinstance(row['buchungsdatum'], date):
                buchungsdatum = row['buchungsdatum']
            elif row['buchungsdatum']:
                buchungsdatum = date.fromisoformat(row['buchungsdatum'])
            else:
                buchungsdatum = None
        except (KeyError, TypeError, ValueError):
            buchungsdatum = None

        try:
            status = str(row['status'])
        except (KeyError, TypeError):
            status = 'gebucht'

        try:
            note = Decimal(str(row['note'])) if row['note'] else None
        except (KeyError, TypeError, ValueError):
            note = None

        try:
            if isinstance(row['pruefungsdatum'], date):
                pruefungsdatum = row['pruefungsdatum']
            elif row['pruefungsdatum']:
                pruefungsdatum = date.fromisoformat(row['pruefungsdatum'])
            else:
                pruefungsdatum = None
        except (KeyError, TypeError, ValueError):
            pruefungsdatum = None

        try:
            versuch = int(row['versuch'])
        except (KeyError, TypeError):
            versuch = 1

        try:
            max_versuche = int(row['max_versuche'])
        except (KeyError, TypeError):
            max_versuche = 3

        try:
            anmeldemodus = str(row['anmeldemodus'])
        except (KeyError, TypeError):
            anmeldemodus = 'online'

        try:
            thema = row['thema'] if row['thema'] else None
        except (KeyError, TypeError):
            thema = None

        return cls(
            id=int(row['id']),
            einschreibung_id=einschreibung_id,
            modul_id=modul_id,
            buchungsdatum=buchungsdatum,
            status=status,
            note=note,
            pruefungsdatum=pruefungsdatum,
            versuch=versuch,
            max_versuche=max_versuche,
            anmeldemodus=anmeldemodus,
            thema=thema
        )

    # ========== String Representation ==========

    def __str__(self) -> str:
        note_str = f"{self.note:.2f}" if self.note else "keine Note"
        versuch_str = f"(Versuch {self.versuch})" if self.versuch > 1 else ""
        return f"Pruefungsleistung(Modul {self.modul_id}, Note: {note_str} {versuch_str})"

    def __repr__(self) -> str:
        return (f"Pruefungsleistung(id={self.id}, modul_id={self.modul_id}, "
                f"note={self.note}, versuch={self.versuch})")