#!/usr/bin/env python3
# migration_cleanup_only.py
"""
Vereinfachte Migration: Nur Daten-Bereinigung

REGEL: Module aus Semester N können nur gebucht werden,
       wenn ALLE vorherigen Semester (1 bis N-1) komplett abgeschlossen sind.

WICHTIG: Innerhalb eines Semesters ist die Reihenfolge egal!
         Teresa kann in Semester 2 Modul 7 buchen, auch wenn Modul 6 fehlt.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'dashboard.db'


def cleanup_invalid_bookings(conn):
    """Entferne nur wirklich ungültige Buchungen"""

    # Finde Buchungen die gegen die Regel verstoßen:
    # Module aus Semester N gebucht, aber Semester N-1 nicht komplett

    invalid_bookings = conn.execute("""
        WITH semester_status AS (
            -- Berechne für jeden Student und jedes Semester den Status
            SELECT 
                e.id as einschreibung_id,
                e.student_id,
                sgm.semester,
                COUNT(DISTINCT sgm.modul_id) as module_gesamt,
                COUNT(DISTINCT CASE 
                    WHEN mb.status = 'bestanden' THEN mb.modul_id 
                END) as module_bestanden,
                CASE 
                    WHEN COUNT(DISTINCT sgm.modul_id) = COUNT(DISTINCT CASE 
                        WHEN mb.status = 'bestanden' THEN mb.modul_id 
                    END)
                    THEN 1
                    ELSE 0
                END as ist_komplett
            FROM einschreibung e
            JOIN studiengang_modul sgm ON sgm.studiengang_id = e.studiengang_id
            LEFT JOIN modulbuchung mb ON mb.modul_id = sgm.modul_id 
                AND mb.einschreibung_id = e.id
            WHERE e.status = 'aktiv'
            GROUP BY e.id, sgm.semester
        ),
        invalid AS (
            -- Finde gebuchte Module deren vorheriges Semester nicht komplett ist
            SELECT DISTINCT
                mb.id,
                s.vorname || ' ' || s.nachname as student_name,
                m.name as modul_name,
                sgm.semester as modul_semester,
                mb.status,
                ss.semester as unvollstaendiges_semester,
                ss.module_bestanden || '/' || ss.module_gesamt as fortschritt
            FROM modulbuchung mb
            JOIN einschreibung e ON mb.einschreibung_id = e.id
            JOIN student s ON e.student_id = s.id
            JOIN modul m ON mb.modul_id = m.id
            JOIN studiengang_modul sgm ON sgm.modul_id = m.id 
                AND sgm.studiengang_id = e.studiengang_id
            JOIN semester_status ss ON ss.einschreibung_id = e.id
            WHERE mb.status = 'gebucht'
              AND sgm.semester > 1  -- Nur Semester 2+
              AND ss.semester < sgm.semester  -- Vorheriges Semester
              AND ss.ist_komplett = 0  -- Nicht komplett!
        )
        SELECT * FROM invalid
        ORDER BY student_name, modul_semester
    """).fetchall()

    if not invalid_bookings:
        print("✅ Keine ungültigen Buchungen gefunden")
        return

    print(f"\n⚠️  Gefunden: {len(invalid_bookings)} ungültige Buchungen:")
    print(f"{'ID':<4} {'Student':<20} {'Modul':<50} {'Sem':<4} {'Blockiert durch':<20}")
    print("-" * 110)

    for booking in invalid_bookings:
        blockiert = f"Semester {booking[5]} ({booking[6]})"
        print(f"{booking[0]:<4} {booking[1]:<20} {booking[2]:<50} {booking[3]:<4} {blockiert:<20}")

    print("\n💡 Erklärung:")
    print("   Diese Buchungen sind aus höheren Semestern, aber ein vorheriges")
    print("   Semester ist noch nicht komplett abgeschlossen.")
    print("\n   Beispiel: Tamara hat Semester 3 Module gebucht,")
    print("             aber Semester 1 ist nur zu 33% abgeschlossen.")

    # Frage User
    print("\n❓ Sollen diese ungültigen Buchungen gelöscht werden?")
    response = input("   (ja/nein): ").lower().strip()

    if response in ['ja', 'j', 'yes', 'y']:
        booking_ids = [b[0] for b in invalid_bookings]

        # Lösche zugehörige Prüfungsleistungen zuerst
        conn.execute(f"""
            DELETE FROM pruefungsleistung 
            WHERE modulbuchung_id IN ({','.join('?' * len(booking_ids))})
        """, booking_ids)

        # Lösche Buchungen
        conn.execute(f"""
            DELETE FROM modulbuchung 
            WHERE id IN ({','.join('?' * len(booking_ids))})
        """, booking_ids)

        conn.commit()
        print(f"✅ {len(booking_ids)} ungültige Buchungen gelöscht")
    else:
        print("⏭️  Übersprungen - Buchungen bleiben bestehen")


def show_semester_progress(conn):
    """Zeige Fortschritt pro Student und Semester"""

    print("\n" + "="*100)
    print("📊 SEMESTER-FORTSCHRITT ALLER STUDENTEN")
    print("="*100)

    students = conn.execute("""
        SELECT DISTINCT s.id, s.vorname, s.nachname, e.id as einschreibung_id
        FROM student s
        JOIN einschreibung e ON s.id = e.student_id
        WHERE e.status = 'aktiv'
        ORDER BY s.nachname
    """).fetchall()

    for student in students:
        print(f"\n👤 {student[1]} {student[2]} (Student ID: {student[0]})")

        # Fortschritt pro Semester
        progress = conn.execute("""
            SELECT 
                sgm.semester,
                COUNT(DISTINCT sgm.modul_id) as gesamt,
                COUNT(DISTINCT CASE WHEN mb.status = 'bestanden' THEN mb.modul_id END) as bestanden,
                COUNT(DISTINCT CASE WHEN mb.status = 'gebucht' THEN mb.modul_id END) as gebucht,
                CASE 
                    WHEN COUNT(DISTINCT sgm.modul_id) = 
                         COUNT(DISTINCT CASE WHEN mb.status = 'bestanden' THEN mb.modul_id END)
                    THEN '✅ KOMPLETT'
                    ELSE '⏳ Unvollständig'
                END as status
            FROM studiengang_modul sgm
            LEFT JOIN modulbuchung mb ON mb.modul_id = sgm.modul_id 
                AND mb.einschreibung_id = ?
            WHERE sgm.studiengang_id = (
                SELECT studiengang_id FROM einschreibung WHERE id = ?
            )
            GROUP BY sgm.semester
            ORDER BY sgm.semester
        """, (student[3], student[3])).fetchall()

        for sem in progress:
            prozent = (sem[2] / sem[1] * 100) if sem[1] > 0 else 0
            print(f"   Semester {sem[0]}: {sem[2]}/{sem[1]} bestanden ({prozent:.0f}%), "
                  f"{sem[3]} gebucht → {sem[4]}")


def main():
    print("="*100)
    print("🧹 DATEN-BEREINIGUNG: Entferne ungültige Semester-Buchungen")
    print("="*100)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Schritt 1: Zeige aktuellen Zustand
        print("\n📊 VORHER:")
        show_semester_progress(conn)

        # Schritt 2: Bereinige ungültige Daten
        print("\n" + "="*100)
        print("🔍 SUCHE NACH UNGÜLTIGEN BUCHUNGEN")
        print("="*100)
        cleanup_invalid_bookings(conn)

        # Schritt 3: Zeige neuen Zustand
        print("\n📊 NACHHER:")
        show_semester_progress(conn)

        print("\n" + "="*100)
        print("✅ Bereinigung abgeschlossen!")
        print("="*100)
        print("\nHinweis:")
        print("  • Die Backend-Validierung verhindert zukünftig ungültige Buchungen")
        print("  • Innerhalb eines Semesters können Module frei gebucht werden")
        print("  • Höhere Semester nur wenn alle vorherigen Semester komplett sind")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Fehler: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()