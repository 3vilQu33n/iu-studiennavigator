#!/usr/bin/env python3
"""
Setzt Prüfungstermine in die Vergangenheit für Testing
+ Trägt Noten/Prüfungsleistungen ein
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, date

# Fix für DeprecationWarning in Python 3.12+
sqlite3.register_adapter(date, lambda val: val.isoformat())
sqlite3.register_converter("date", lambda val: date.fromisoformat(val.decode()))

DB_PATH = Path(__file__).parent / 'data' / 'dashboard.db'


def list_termine():
    """Zeigt alle Prüfungstermine"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT pt.id,
                              pt.modul_id,
                              pt.datum,
                              pt.beginn,
                              pt.art,
                              m.name  AS modul_name,
                              CASE
                                  WHEN pt.datum < date('now') THEN 'Vergangenheit'
                                  WHEN pt.datum = date('now') THEN 'Heute'
                                  ELSE 'Zukunft'
                                  END AS zeitstatus
                       FROM pruefungstermin pt
                                JOIN modul m ON m.id = pt.modul_id
                       ORDER BY pt.datum DESC
                       """)

        termine = cursor.fetchall()

        print("\n" + "=" * 80)
        print("PRÜFUNGSTERMINE")
        print("=" * 80)

        for t in termine:
            print(f"ID: {t['id']:3d} | {t['datum']} | {t['modul_name']:40s} | {t['art']:10s} | {t['zeitstatus']}")

        print("=" * 80 + "\n")
        return termine


def move_termin_to_past(termin_id, days_ago=7):
    """Verschiebt einen Termin in die Vergangenheit"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Neues Datum berechnen
        new_date = (datetime.now() - timedelta(days=days_ago)).date()

        # ERST prüfen ob Einschreibedatum angepasst werden muss
        if not check_and_fix_einschreibung(termin_id, new_date):
            print("❌ Vorgang abgebrochen - Einschreibedatum wurde nicht angepasst")
            return False

        # DANN erst den Termin verschieben
        cursor.execute("""
                       UPDATE pruefungstermin
                       SET datum = ?
                       WHERE id = ?
                       """, (new_date, termin_id))

        conn.commit()

        print(f"✅ Termin {termin_id} auf {new_date} gesetzt ({days_ago} Tage in der Vergangenheit)")
        return True


def move_all_future_to_past(days_ago=7):
    """Verschiebt ALLE zukünftigen Termine in die Vergangenheit"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        # Zähle zukünftige Termine
        cursor.execute("SELECT COUNT(*) FROM pruefungstermin WHERE datum > date('now')")
        count = cursor.fetchone()[0]

        if count == 0:
            print("ℹ️  Keine zukünftigen Termine gefunden")
            return

        print(f"⚠️  {count} zukünftige Termine gefunden")

        # Berechne neues Datum
        new_date = (datetime.now() - timedelta(days=days_ago)).date()

        # Prüfe frühestes Einschreibedatum VORHER
        cursor.execute("SELECT MIN(start_datum) FROM einschreibung")
        min_einschreibung = cursor.fetchone()[0]

        if min_einschreibung:
            min_einschreibung_date = datetime.strptime(min_einschreibung, '%Y-%m-%d').date()

            if new_date < min_einschreibung_date:
                print()
                print("⚠️  " + "=" * 70)
                print("⚠️  FEHLER: Termine würden VOR der frühesten Einschreibung liegen!")
                print("⚠️  " + "=" * 70)
                print(f"   📅 Früheste Einschreibung: {min_einschreibung}")
                print(f"   📅 Neue Prüfungstermine:   {new_date}")
                print(f"   ⏰ Differenz:              {(min_einschreibung_date - new_date).days} Tage!")
                print()
                print("❌ Das ist nicht möglich - Studierende können keine Prüfungen")
                print("   ablegen, BEVOR sie überhaupt eingeschrieben sind!")
                print()
                print("💡 Lösung:")
                print("   1) Wähle Option 7 um Einschreibedaten anzuzeigen")
                print("   2) Wähle Option 8 um Einschreibedaten zurückzusetzen")
                print(f"   3) Setze sie auf ein Datum VOR {new_date}")
                print("   4) Dann kannst du die Prüfungstermine verschieben")
                print()
                return

        print()
        response = input(f"Alle {count} Termine {days_ago} Tage zurücksetzen? (ja/nein): ")

        if response.lower() not in ['ja', 'j', 'yes', 'y']:
            print("❌ Abgebrochen")
            return

        # Verschiebe alle Termine
        cursor.execute("""
                       UPDATE pruefungstermin
                       SET datum = ?
                       WHERE datum > date('now')
                       """, (new_date,))

        conn.commit()

        print(f"✅ {count} Termine auf {new_date} gesetzt")


def check_and_fix_einschreibung(termin_id, exam_date):
    """
    Prüft ob Prüfungstermin vor Einschreibung liegen würde.
    MUSS VOR dem Verschieben des Termins aufgerufen werden!

    Returns:
        True: Weitermachen ist OK (kein Konflikt)
        False: Abbrechen (Prüfung würde vor Einschreibung liegen)
    """
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Finde Einschreibung über pruefungsanmeldung
        cursor.execute("""
                       SELECT e.id    as einschreibung_id,
                              e.start_datum,
                              s.vorname,
                              s.nachname,
                              sg.name as studiengang,
                              m.name  as modul_name
                       FROM pruefungsanmeldung pa
                                JOIN modulbuchung mb ON mb.id = pa.modulbuchung_id
                                JOIN einschreibung e ON e.id = mb.einschreibung_id
                                JOIN student s ON s.id = e.student_id
                                JOIN studiengang sg ON sg.id = e.studiengang_id
                                JOIN pruefungstermin pt ON pt.id = pa.pruefungstermin_id
                                JOIN modul m ON m.id = pt.modul_id
                       WHERE pa.pruefungstermin_id = ?
                       """, (termin_id,))

        result = cursor.fetchone()
        if not result:
            # Keine Anmeldung gefunden - kein Problem
            return True

        einschreibung_id = result['einschreibung_id']
        start_datum = result['start_datum']

        # Parse Datum
        if isinstance(start_datum, str):
            start_datum = datetime.strptime(start_datum, '%Y-%m-%d').date()

        # Prüfe ob Prüfungstermin VOR Einschreibung liegen würde
        if exam_date < start_datum:
            print()
            print("⚠️  " + "=" * 70)
            print("⚠️  FEHLER: Prüfungstermin würde VOR der Einschreibung liegen!")
            print("⚠️  " + "=" * 70)
            print(f"   Modul:             {result['modul_name']}")
            print(f"   Student:           {result['vorname']} {result['nachname']}")
            print(f"   Studiengang:       {result['studiengang']}")
            print(f"   Einschreibungs-ID: {einschreibung_id}")
            print()
            print(f"   📅 Aktuelles Einschreibedatum:  {start_datum}")
            print(f"   📅 Gewünschter Prüfungstermin:  {exam_date}")
            print(f"   ⏰ Differenz:                   {(start_datum - exam_date).days} Tage!")
            print()
            print("❌ Das ist nicht möglich - Studierende können keine Prüfungen")
            print("   ablegen, BEVOR sie überhaupt eingeschrieben sind!")
            print()
            print("💡 Lösung:")
            print("   1) Wähle Option 7 um das Einschreibedatum anzuzeigen")
            print("   2) Wähle Option 8 um das Einschreibedatum zurückzusetzen")
            print(f"   3) Setze es auf ein Datum VOR {exam_date}")
            print("   4) Dann kannst du den Prüfungstermin verschieben")
            print()

            return False

        return True


def show_einschreibungen():
    """Zeigt alle Einschreibedaten an"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Zeige alle Einschreibungen
        cursor.execute("""
                       SELECT e.id,
                              e.start_datum,
                              s.vorname,
                              s.nachname,
                              sg.name as studiengang,
                              zm.name as zeitmodell
                       FROM einschreibung e
                                JOIN student s ON s.id = e.student_id
                                JOIN studiengang sg ON sg.id = e.studiengang_id
                                JOIN zeitmodell zm ON zm.id = e.zeitmodell_id
                       ORDER BY e.start_datum DESC
                       """)

        einschreibungen = cursor.fetchall()

        print("\n" + "=" * 80)
        print("EINSCHREIBUNGEN")
        print("=" * 80)
        for e in einschreibungen:
            print(
                f"ID: {e['id']:3d} | {e['start_datum']} | {e['vorname']} {e['nachname']:20s} | {e['studiengang']:30s} | {e['zeitmodell']}")
        print("=" * 80 + "\n")

        return einschreibungen


def set_start_datum(student_id=None, days_ago=None):
    """Setzt Einschreibedatum manuell"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Zeige alle Einschreibungen
        einschreibungen = show_einschreibungen()

        if not student_id:
            einschreibung_id = input("Einschreibungs-ID: ").strip()
            if not einschreibung_id.isdigit():
                print("❌ Ungültige ID")
                return
            einschreibung_id = int(einschreibung_id)
        else:
            einschreibung_id = student_id

        # Frage nach Anzahl der Tage
        if days_ago is None:
            days_input = input("Wie viele Tage zurücksetzen? (Standard: 60): ").strip()
            if days_input == "":
                days_ago = 60
            elif days_input.isdigit():
                days_ago = int(days_input)
            else:
                print("❌ Ungültige Eingabe")
                return

        # Neues Datum
        new_date = (datetime.now() - timedelta(days=days_ago)).date()

        cursor.execute("""
                       UPDATE einschreibung
                       SET start_datum = ?
                       WHERE id = ?
                       """, (new_date, einschreibung_id))

        conn.commit()
        print(f"✅ Einschreibedatum auf {new_date} gesetzt ({days_ago} Tage zurück)")


def show_noten_uebersicht():
    """Zeigt eine Übersicht aller Noten für Module"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hole alle Modulbuchungen mit Prüfungsleistungen
        cursor.execute("""
                       SELECT m.name    AS modul_name,
                              m.ects,
                              mb.status AS modulbuchung_status,
                              pl.note,
                              pl.pruefungsdatum,
                              pl.versuch,
                              pl.max_versuche,
                              s.vorname,
                              s.nachname,
                              CASE
                                  WHEN mb.status = 'bestanden' THEN '✅ Bestanden'
                                  WHEN mb.status = 'anerkannt' THEN '✅ Anerkannt'
                                  WHEN mb.status = 'nicht_bestanden' THEN '❌ Nicht bestanden'
                                  WHEN mb.status = 'gebucht' THEN '📚 Gebucht'
                                  ELSE mb.status
                                  END   AS status_icon
                       FROM modulbuchung mb
                                JOIN modul m ON m.id = mb.modul_id
                                JOIN einschreibung e ON e.id = mb.einschreibung_id
                                JOIN student s ON s.id = e.student_id
                                LEFT JOIN pruefungsleistung pl ON pl.modulbuchung_id = mb.id
                       ORDER BY s.nachname, s.vorname, m.name, pl.versuch
                       """)

        ergebnisse = cursor.fetchall()

        if not ergebnisse:
            print("\n❌ Keine Modulbuchungen gefunden\n")
            return

        print("\n" + "=" * 100)
        print("NOTEN-ÜBERSICHT FÜR MODULE")
        print("=" * 100)

        current_student = None
        current_modul = None

        for row in ergebnisse:
            student_name = f"{row['vorname']} {row['nachname']}"

            # Neuer Student?
            if current_student != student_name:
                current_student = student_name
                current_modul = None
                print(f"\n👤 Student: {student_name}")
                print("-" * 100)

            # Neues Modul?
            if current_modul != row['modul_name']:
                current_modul = row['modul_name']
                print(f"\n📖 {row['modul_name']} ({row['ects']} ECTS) - {row['status_icon']}")

            # Prüfungsleistung vorhanden?
            if row['note'] is not None:
                datum = row['pruefungsdatum'] if row['pruefungsdatum'] else 'Kein Datum'
                print(f"   📝 Versuch {row['versuch']}/{row['max_versuche']}: Note {row['note']} | Datum: {datum}")
            else:
                print(f"   ℹ️  Noch keine Prüfungsleistung eingetragen")

        print("\n" + "=" * 100 + "\n")


def add_pruefungsleistung(termin_id, note, versuch=1):
    """Trägt eine Note/Prüfungsleistung ein"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Hole Termin-Infos
        cursor.execute("""
                       SELECT pt.*, m.name as modul_name
                       FROM pruefungstermin pt
                                JOIN modul m ON m.id = pt.modul_id
                       WHERE pt.id = ?
                       """, (termin_id,))

        termin = cursor.fetchone()
        if not termin:
            print(f"❌ Termin {termin_id} nicht gefunden")
            return

        # 2. Finde modulbuchung_id über pruefungsanmeldung
        cursor.execute("""
                       SELECT modulbuchung_id
                       FROM pruefungsanmeldung
                       WHERE pruefungstermin_id = ?
                       """, (termin_id,))

        anmeldung = cursor.fetchone()
        if not anmeldung:
            print(f"❌ Keine Prüfungsanmeldung für Termin {termin_id} gefunden!")
            print(f"   Du musst dich erst für die Prüfung anmelden!")
            return

        modulbuchung_id = anmeldung['modulbuchung_id']

        # 3. Prüfe ob schon eine Leistung existiert
        cursor.execute("""
                       SELECT id
                       FROM pruefungsleistung
                       WHERE modulbuchung_id = ?
                         AND versuch = ?
                       """, (modulbuchung_id, versuch))

        existing = cursor.fetchone()
        if existing:
            print(f"⚠️  Es existiert bereits eine Prüfungsleistung für Versuch {versuch}")
            response = input("Überschreiben? (ja/nein): ")
            if response.lower() not in ['ja', 'j', 'yes', 'y']:
                print("❌ Abgebrochen")
                return

            # Update
            cursor.execute("""
                           UPDATE pruefungsleistung
                           SET note           = ?,
                               pruefungsdatum = ?
                           WHERE id = ?
                           """, (note, termin['datum'], existing['id']))

            print(f"✅ Prüfungsleistung aktualisiert!")
        else:
            # Insert
            cursor.execute("""
                           INSERT INTO pruefungsleistung
                               (modulbuchung_id, note, pruefungsdatum, versuch, anmeldemodus)
                           VALUES (?, ?, ?, ?, ?)
                           """, (modulbuchung_id, note, termin['datum'], versuch, termin['art']))

            print(f"✅ Prüfungsleistung eingetragen!")

        # 4. Update modulbuchung status
        if note <= 4.0:
            new_status = 'bestanden'
        else:
            new_status = 'nicht_bestanden'

        cursor.execute("""
                       UPDATE modulbuchung
                       SET status = ?
                       WHERE id = ?
                       """, (new_status, modulbuchung_id))

        conn.commit()

        print()
        print(f"📝 Modul: {termin['modul_name']}")
        print(f"📅 Datum: {termin['datum']}")
        print(f"📊 Note: {note}")
        print(f"🔢 Versuch: {versuch}")
        print(f"✅ Status: {new_status}")


def quick_test_flow(termin_id, days_ago=30, note=2.0):
    """Schnelltest: Termin zurücksetzen + Note eintragen"""
    print(f"\n🚀 SCHNELLTEST-MODUS")
    print(f"   Termin-ID: {termin_id}")
    print(f"   Tage zurück: {days_ago}")
    print(f"   Note: {note}")
    print()

    # 1. Termin zurücksetzen
    print("1️⃣  Setze Termin zurück...")
    if not move_termin_to_past(termin_id, days_ago):
        print("\n❌ SCHNELLTEST ABGEBROCHEN!")
        return

    # 2. Note eintragen
    print("\n2️⃣  Trage Note ein...")
    add_pruefungsleistung(termin_id, note, versuch=1)

    print("\n✅ SCHNELLTEST ABGESCHLOSSEN!")


def interactive_menu():
    """Interaktives Menü"""
    print("\n" + "=" * 80)
    print("PRÜFUNGSTERMIN ZEIT-MANIPULATION & NOTEN-EINTRAGUNG")
    print("=" * 80)
    print()
    print("Optionen:")
    print("  1) Liste alle Prüfungstermine")
    print("  2) Setze einen Termin 7 Tage zurück")
    print("  3) Setze einen Termin X Tage zurück (eigene Anzahl)")
    print("  4) Setze ALLE zukünftigen Termine 7 Tage zurück")
    print("  5) Liste Noten für Module")
    print("  6) Trage Note für einen Termin ein")
    print("  7) SCHNELLTEST: Termin zurück + Note eintragen (alles in einem!)")
    print("  8) Einschreibedatum anzeigen")
    print("  9) Setze Einschreibedatum zurück (manuell)")
    print(" 10) Beenden")
    print()

    while True:
        choice = input("Wähle Option (1-10): ").strip()

        if choice == '1':
            list_termine()

        elif choice == '2':
            list_termine()
            termin_id = input("Termin-ID: ").strip()
            if termin_id.isdigit():
                if move_termin_to_past(int(termin_id), 7):
                    print()
                    list_termine()
            else:
                print("❌ Ungültige ID")

        elif choice == '3':
            list_termine()
            termin_id = input("Termin-ID: ").strip()
            days = input("Wie viele Tage zurück? ").strip()
            if termin_id.isdigit() and days.isdigit():
                if move_termin_to_past(int(termin_id), int(days)):
                    print()
                    list_termine()
            else:
                print("❌ Ungültige Eingabe")

        elif choice == '4':
            list_termine()
            move_all_future_to_past(7)
            print()
            list_termine()

        elif choice == '5':
            show_noten_uebersicht()

        elif choice == '6':
            list_termine()
            termin_id = input("Termin-ID: ").strip()
            note = input("Note (1.0 - 5.0): ").strip()
            versuch = input("Versuch (1, 2, 3, ...): ").strip() or "1"

            if termin_id.isdigit() and versuch.isdigit():
                try:
                    note_float = float(note.replace(',', '.'))
                    if 1.0 <= note_float <= 5.0:
                        add_pruefungsleistung(int(termin_id), note_float, int(versuch))
                    else:
                        print("❌ Note muss zwischen 1.0 und 5.0 liegen")
                except ValueError:
                    print("❌ Ungültige Note")
            else:
                print("❌ Ungültige Eingabe")

        elif choice == '7':
            list_termine()
            termin_id = input("Termin-ID: ").strip()
            days = input("Wie viele Tage zurück? (Standard: 30): ").strip() or "30"
            note = input("Note (1.0 - 5.0, Standard: 2.0): ").strip() or "2.0"

            if termin_id.isdigit() and days.isdigit():
                try:
                    note_float = float(note.replace(',', '.'))
                    if 1.0 <= note_float <= 5.0:
                        quick_test_flow(int(termin_id), int(days), note_float)
                        print()
                        list_termine()
                    else:
                        print("❌ Note muss zwischen 1.0 und 5.0 liegen")
                except ValueError:
                    print("❌ Ungültige Note")
            else:
                print("❌ Ungültige Eingabe")

        elif choice == '8':
            show_einschreibungen()

        elif choice == '9':
            set_start_datum()

        elif choice == '10':
            print("\n👋 Tschüss!")
            break

        else:
            print("❌ Ungültige Option")

        print()


if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"❌ Datenbank nicht gefunden: {DB_PATH}")
        exit(1)

    interactive_menu()