# models/gebuehr.py
"""
Domain Model: Gebühr

AGGREGATION: Einschreibung 1 → * Gebuehr
→ Gebühren werden von Einschreibung ausgelöst
→ Gebühren leben unabhängig weiter (Buchhaltung, Archiv)
→ Gebühren bleiben nach Exmatrikulation bestehen
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')

# Erlaubte Gebührenarten
ALLOWED_ART = {"Monatsrate", "Semestergebühr", "Prüfungsgebühr", "Einschreibegebühr"}


@dataclass(slots=True)
class Gebuehr:
    """Domain Model: Gebühr

    Repräsentiert eine Studiengebühr (Monatsrate, Semestergebühr, etc.).

    OOP-BEZIEHUNGEN:
    - AGGREGATION zu Einschreibung (wird von Einschreibung erzeugt, lebt aber unabhängig)
    - Gebühren werden von der Buchhaltung separat verwaltet
    - Gebühren bleiben nach Student-Exmatrikulation bestehen

    Attributes:
        id: Primärschlüssel (None beim Insert)
        einschreibung_id: FK zur Einschreibung (AGGREGATION)
        art: Art der Gebühr (Monatsrate, Semestergebühr, etc.)
        betrag: Betrag in Euro
        faellig_am: Fälligkeitsdatum
        bezahlt_am: Zahlungsdatum (None = noch nicht bezahlt)
    """
    id: Optional[int]
    einschreibung_id: int  # AGGREGATION: gehört zu Einschreibung, lebt aber unabhängig
    art: str  # Monatsrate | Semestergebühr | Prüfungsgebühr | Einschreibegebühr
    betrag: Decimal
    faellig_am: date
    bezahlt_am: Optional[date] = None

    def __post_init__(self) -> None:
        """Validierung und Typ-Konvertierung nach Initialisierung"""
        # art validieren (Warnung, keine Exception)
        if self.art not in ALLOWED_ART:
            logger.warning(
                "Unbekannte Gebührenart: %r (erlaubt: %s)",
                self.art,
                ", ".join(sorted(ALLOWED_ART))
            )

        # betrag → Decimal, >= 0
        if not isinstance(self.betrag, Decimal):
            try:
                self.betrag = Decimal(str(self.betrag))
            except (InvalidOperation, ValueError, TypeError) as e:
                raise ValueError(f"Ungültiger Betrag: {self.betrag!r}") from e

        if self.betrag < Decimal("0"):
            raise ValueError("Betrag darf nicht negativ sein")

        # Datumsfelder aus ISO-String parsen falls nötig
        if isinstance(self.faellig_am, str):
            try:
                self.faellig_am = date.fromisoformat(self.faellig_am)
            except Exception as e:
                raise ValueError(f"Ungültiges Datum für faellig_am: {self.faellig_am!r}") from e

        if isinstance(self.bezahlt_am, str):
            try:
                self.bezahlt_am = date.fromisoformat(self.bezahlt_am)
            except Exception as e:
                raise ValueError(f"Ungültiges Datum für bezahlt_am: {self.bezahlt_am!r}") from e

    # ========== PUBLIC Methods ==========

    def is_paid(self) -> bool:
        """PUBLIC: Prüft ob die Gebühr bezahlt wurde"""
        return self.bezahlt_am is not None

    def is_overdue(self, reference_date: Optional[date] = None) -> bool:
        """PUBLIC: Prüft ob die Gebühr überfällig ist

        Args:
            reference_date: Referenzdatum (default: heute)

        Returns:
            True wenn überfällig (nicht bezahlt und Fälligkeitsdatum überschritten)
        """
        ref = reference_date or date.today()
        return not self.is_paid() and self.faellig_am < ref

    def is_due_soon(self, days_ahead: int = 7, reference_date: Optional[date] = None) -> bool:
        """PUBLIC: Prüft ob die Gebühr bald fällig wird

        Args:
            days_ahead: Anzahl Tage im Voraus (default: 7)
            reference_date: Referenzdatum (default: heute)

        Returns:
            True wenn innerhalb der nächsten N Tage fällig
        """
        if self.is_paid():
            return False

        ref = reference_date or date.today()
        return ref <= self.faellig_am <= (ref + timedelta(days=days_ahead))

    def get_days_overdue(self, reference_date: Optional[date] = None) -> int:
        """PUBLIC: Berechnet Anzahl Tage der Überfälligkeit

        Args:
            reference_date: Referenzdatum (default: heute)

        Returns:
            Anzahl Tage überfällig (0 wenn nicht überfällig)
        """
        if not self.is_overdue(reference_date):
            return 0

        ref = reference_date or date.today()
        return (ref - self.faellig_am).days

    def get_days_until_due(self, reference_date: Optional[date] = None) -> int:
        """PUBLIC: Berechnet Anzahl Tage bis zur Fälligkeit

        Args:
            reference_date: Referenzdatum (default: heute)

        Returns:
            Anzahl Tage bis fällig (negativ wenn überfällig)
        """
        ref = reference_date or date.today()
        return (self.faellig_am - ref).days

    def mark_as_paid(self, payment_date: Optional[date] = None) -> None:
        """PUBLIC: Markiert die Gebühr als bezahlt

        Args:
            payment_date: Zahlungsdatum (default: heute)
        """
        self.bezahlt_am = payment_date or date.today()

    def get_formatted_amount(self) -> str:
        """PUBLIC: Gibt Betrag formatiert zurück (z.B. '1.234,56 €')"""
        # Deutsch: Punkt als Tausender, Komma als Dezimal
        amount_str = f"{self.betrag:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{amount_str} €"

    def get_status_text(self, reference_date: Optional[date] = None) -> str:
        """PUBLIC: Gibt Status als Text zurück

        Returns:
            'Bezahlt' | 'Überfällig' | 'Fällig bald' | 'Offen'
        """
        if self.is_paid():
            return "Bezahlt"
        elif self.is_overdue(reference_date):
            days = self.get_days_overdue(reference_date)
            return f"Überfällig ({days} Tage)"
        elif self.is_due_soon(reference_date=reference_date):
            days = self.get_days_until_due(reference_date)
            return f"Fällig in {days} Tagen"
        else:
            return "Offen"

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary (für JSON/Templates)"""
        return {
            'id': self.id,
            'einschreibung_id': self.einschreibung_id,
            'art': self.art,
            'betrag': float(self.betrag),
            'betrag_formatted': self.get_formatted_amount(),
            'faellig_am': self.faellig_am.isoformat(),
            'bezahlt_am': self.bezahlt_am.isoformat() if self.bezahlt_am else None,
            'is_paid': self.is_paid(),
            'is_overdue': self.is_overdue(),
            'is_due_soon': self.is_due_soon(),
            'days_overdue': self.get_days_overdue(),
            'days_until_due': self.get_days_until_due(),
            'status_text': self.get_status_text()
        }

    @classmethod
    def from_row(cls, row) -> "Gebuehr":
        """PUBLIC: Factory Method - Erstellt Gebühr aus DB-Row"""
        # sqlite3.Row hat keine .get() Methode! Direkt auf Spalten zugreifen
        return cls(
            id=int(row['id']) if row['id'] is not None else None,
            einschreibung_id=int(row['einschreibung_id']),
            art=str(row['art']),
            betrag=Decimal(str(row['betrag'])),
            faellig_am=row['faellig_am'] if isinstance(row['faellig_am'], date)
            else date.fromisoformat(row['faellig_am']),
            bezahlt_am=row['bezahlt_am'] if isinstance(row['bezahlt_am'], date)
            else date.fromisoformat(row['bezahlt_am']) if row['bezahlt_am'] else None
        )

    # ========== String Representation ==========

    def __str__(self) -> str:
        status = "bezahlt" if self.is_paid() else "offen"
        return f"Gebuehr({self.art}, {self.get_formatted_amount()}, {status})"

    def __repr__(self) -> str:
        return (f"Gebuehr(id={self.id}, art='{self.art}', "
                f"betrag={self.betrag}, is_paid={self.is_paid()})")