# models/pruefungsanmeldung.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Pruefungsanmeldung:
    """Domain Model: Prüfungsanmeldung

    Verknüpft Student (via modulbuchung) mit Prüfungstermin.
    Verwaltet den Status der Anmeldung (angemeldet, storniert, absolviert).
    """
    id: int
    modulbuchung_id: int
    pruefungstermin_id: int
    status: str = 'angemeldet'  # 'angemeldet', 'storniert', 'absolviert'
    angemeldet_am: Optional[datetime] = None

    def __post_init__(self):
        """Typ-Konvertierung"""
        if self.angemeldet_am and isinstance(self.angemeldet_am, str):
            self.angemeldet_am = datetime.fromisoformat(self.angemeldet_am)

        # Setze angemeldet_am auf jetzt, falls nicht gesetzt
        if not self.angemeldet_am:
            self.angemeldet_am = datetime.now()

    # ========== PUBLIC Methods ==========

    def ist_aktiv(self) -> bool:
        """PUBLIC: Prüft ob Anmeldung aktiv ist"""
        return self.status == 'angemeldet'

    def ist_storniert(self) -> bool:
        """PUBLIC: Prüft ob Anmeldung storniert wurde"""
        return self.status == 'storniert'

    def ist_absolviert(self) -> bool:
        """PUBLIC: Prüft ob Prüfung bereits absolviert wurde"""
        return self.status == 'absolviert'

    def kann_storniert_werden(self) -> bool:
        """PUBLIC: Prüft ob Anmeldung noch storniert werden kann

        Nur aktive Anmeldungen können storniert werden.
        """
        return self.ist_aktiv()

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary für JSON"""
        return {
            'id': self.id,
            'modulbuchung_id': self.modulbuchung_id,
            'pruefungstermin_id': self.pruefungstermin_id,
            'status': self.status,
            'angemeldet_am': self.angemeldet_am.isoformat() if self.angemeldet_am else None,
            'ist_aktiv': self.ist_aktiv(),
            'ist_storniert': self.ist_storniert(),
            'ist_absolviert': self.ist_absolviert(),
            'kann_storniert_werden': self.kann_storniert_werden()
        }

    @classmethod
    def from_row(cls, row) -> "Pruefungsanmeldung":
        """PUBLIC: Factory Method - Erstellt Pruefungsanmeldung aus DB-Row

        Verwendet try/except für alle optionalen Felder da sqlite3.Row kein .get() hat.
        """
        try:
            status = str(row['status'])
        except (KeyError, TypeError):
            status = 'angemeldet'

        try:
            if row['angemeldet_am']:
                angemeldet_am = datetime.fromisoformat(row['angemeldet_am']) if isinstance(row['angemeldet_am'],
                                                                                           str) else row[
                    'angemeldet_am']
            else:
                angemeldet_am = None
        except (KeyError, TypeError, ValueError):
            angemeldet_am = None

        return cls(
            id=int(row['id']),
            modulbuchung_id=int(row['modulbuchung_id']),
            pruefungstermin_id=int(row['pruefungstermin_id']),
            status=status,
            angemeldet_am=angemeldet_am
        )

    # ========== String Representation ==========

    def __str__(self) -> str:
        return f"Pruefungsanmeldung({self.status}, MB {self.modulbuchung_id} → Termin {self.pruefungstermin_id})"

    def __repr__(self) -> str:
        return (f"Pruefungsanmeldung(id={self.id}, modulbuchung_id={self.modulbuchung_id}, "
                f"termin_id={self.pruefungstermin_id}, status={self.status})")