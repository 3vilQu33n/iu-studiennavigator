# Test-Script: Prüfungstermine & Noten-Manipulation

## 🎯 Zweck

Dieses Script (`set_exam_date_past.py`) ermöglicht es Dozenten und Prüfern, die Dashboard-Funktionalität **ohne Code-Änderungen** zu testen. Hauptziel: Das Auto auf der Roadmap "fahren" zu lassen, indem Module als bestanden markiert werden.

## 🚀 Schnellstart (für Demo)

### 1. Script starten
```bash
python3 set_exam_date_past.py
```

### 2. Empfohlener Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  SCHRITT 1: Einschreibedatum anpassen                       │
└─────────────────────────────────────────────────────────────┘
Option 8 wählen
→ Einschreibungs-ID: 1
→ Wie viele Tage zurücksetzen? 90
✅ Einschreibedatum auf 2024-10-11 gesetzt (90 Tage zurück)

┌─────────────────────────────────────────────────────────────┐
│  SCHRITT 2: Erstes Modul abschließen (SCHNELLTEST)         │
└─────────────────────────────────────────────────────────────┘
Option 7 wählen (SCHNELLTEST)
→ Termin-ID: 1
→ Wie viele Tage zurück? 30
→ Note: 2.0
✅ Termin zurückgesetzt + Note eingetragen

┌─────────────────────────────────────────────────────────────┐
│  SCHRITT 3: Dashboard neu laden & Auto bewegt sich!        │
└─────────────────────────────────────────────────────────────┘
Browser: http://localhost:5050
→ Dashboard neu laden (F5)
→ 🚗 Auto hat sich auf der Roadmap bewegt!
→ Fortschrittsbalken aktualisiert

┌─────────────────────────────────────────────────────────────┐
│  SCHRITT 4: Weitere Module abschließen (optional)          │
└─────────────────────────────────────────────────────────────┘
Option 7 erneut wählen für weitere Prüfungen
→ Verschiedene Noten testen (1.0, 2.3, 4.0)
→ Jedes Mal Dashboard neu laden
→ Auto bewegt sich weiter!

┌─────────────────────────────────────────────────────────────┐
│  SCHRITT 5: Noten-Übersicht anzeigen                        │
└─────────────────────────────────────────────────────────────┘
Option 5 wählen
→ Zeigt alle Module mit Noten & Status
→ Übersicht über Fortschritt
```

## 📋 Alle verfügbaren Optionen

| Option | Funktion | Verwendung |
|--------|----------|------------|
| **1** | Liste alle Prüfungstermine | Übersicht über verfügbare Termine |
| **2** | Setze Termin 7 Tage zurück | Schnell einen einzelnen Termin verschieben |
| **3** | Setze Termin X Tage zurück | Flexibel eigene Anzahl Tage wählen |
| **4** | Setze ALLE Termine zurück | Alle zukünftigen Termine auf einmal |
| **5** | Liste Noten für Module | Übersicht aller Prüfungsleistungen |
| **6** | Trage Note für Termin ein | Manuell Note für bestimmten Termin |
| **7** | **SCHNELLTEST** | **Empfohlen für Demo!** Termin + Note in einem |
| **8** | Einschreibedatum anzeigen | Alle Einschreibungen ansehen |
| **9** | Einschreibedatum zurücksetzen | Manuell Einschreibedatum anpassen |
| **10** | Beenden | Script beenden |

## 🎓 Notensystem

Das Script verwendet das deutsche Hochschul-Notensystem:

| Note | Bewertung | Status |
|------|-----------|--------|
| 1.0 - 1.3 | Sehr gut | ✅ Bestanden |
| 1.7 - 2.3 | Gut | ✅ Bestanden |
| 2.7 - 3.3 | Befriedigend | ✅ Bestanden |
| 3.7 - 4.0 | Ausreichend | ✅ Bestanden |
| 4.1 - 5.0 | Nicht ausreichend | ❌ Nicht bestanden |

## ⚠️ Wichtige Hinweise

### Logische Validierung
Das Script verhindert automatisch logische Fehler:

```
❌ FEHLER: Prüfungstermin würde VOR der Einschreibung liegen!
   
   📅 Aktuelles Einschreibedatum:  2024-10-01
   📅 Gewünschter Prüfungstermin:  2024-09-15
   ⏰ Differenz:                   16 Tage!
   
💡 Lösung:
   1) Wähle Option 8 um das Einschreibedatum anzuzeigen
   2) Wähle Option 9 um das Einschreibedatum zurückzusetzen
   3) Setze es auf ein Datum VOR 2024-09-15
   4) Dann kannst du den Prüfungstermin verschieben
```

### Reihenfolge beachten
1. **Zuerst** Einschreibedatum zurücksetzen (Option 9)
2. **Dann** Prüfungstermine zurücksetzen (Option 2/3/7)

Das Script erzwingt diese Reihenfolge automatisch!

## 💡 Demo-Tipps

### Für eindrucksvolle Demo:

1. **Mehrere Module hintereinander abschließen**
   - Option 7 (SCHNELLTEST) 3-4 Mal ausführen
   - Verschiedene Noten verwenden (1.0, 2.3, 3.7, 4.0)
   - Nach jedem Modul Dashboard neu laden
   - Auto bewegt sich sichtbar weiter auf der Roadmap

2. **Noten-Übersicht zeigen** (Option 5)
   - Zeigt professionelle Übersicht
   - Status-Icons (✅ Bestanden, ❌ Nicht bestanden)
   - Versuchszähler (z.B. Versuch 1/3)

3. **"Durchgefallene" Prüfung simulieren**
   - Note 5.0 eingeben
   - Auto bewegt sich NICHT
   - Modul bleibt offen
   - Zeigt Fehlerbehandlung

## 🔍 Beispiel-Session

```bash
$ python3 set_exam_date_past.py

================================================================================
PRÜFUNGSTERMIN ZEIT-MANIPULATION & NOTEN-EINTRAGUNG
================================================================================

Optionen:
  1) Liste alle Prüfungstermine
  2) Setze einen Termin 7 Tage zurück
  3) Setze einen Termin X Tage zurück (eigene Anzahl)
  4) Setze ALLE zukünftigen Termine 7 Tage zurück
  5) Liste Noten für Module
  6) Trage Note für einen Termin ein
  7) SCHNELLTEST: Termin zurück + Note eintragen (alles in einem!)
  8) Einschreibedatum anzeigen
  9) Setze Einschreibedatum zurück (manuell)
 10) Beenden

Wähle Option (1-10): 9

================================================================================
EINSCHREIBUNGEN
================================================================================
ID:   1 | 2025-11-10 | Demo Student | Angewandte Künstliche Intelligenz | Teilzeit I
================================================================================

Einschreibungs-ID: 1
Wie viele Tage zurücksetzen? (Standard: 60): 90
✅ Einschreibedatum auf 2024-10-12 gesetzt (90 Tage zurück)

Wähle Option (1-10): 7

================================================================================
PRÜFUNGSTERMINE
================================================================================
ID:   1 | 2025-11-10 | Artificial Intelligence              | online    | Vergangenheit
================================================================================

🚀 SCHNELLTEST-MODUS
   Termin-ID: 1
   Tage zurück: 30
   Note: 2.0

1️⃣  Setze Termin zurück...
✅ Termin 1 auf 2024-12-10 gesetzt (30 Tage in der Vergangenheit)

2️⃣  Trage Note ein...
✅ Prüfungsleistung eingetragen!

📝 Modul: Artificial Intelligence
📅 Datum: 2024-12-10
📊 Note: 2.0
🔢 Versuch: 1
✅ Status: bestanden

✅ SCHNELLTEST ABGESCHLOSSEN!

Wähle Option (1-10): 10

👋 Tschüss!
```

## 🎬 Was passiert im Hintergrund?

Wenn du den SCHNELLTEST ausführst:

1. ✅ Prüfungstermin wird in die Vergangenheit verschoben
2. ✅ Note wird in Datenbank eingetragen
3. ✅ Modulbuchung-Status wird auf "bestanden" gesetzt
4. ✅ Prüfungsanmeldung wird auf "absolviert" gesetzt
5. ✅ Dashboard berechnet neuen Fortschritt
6. ✅ Auto-Position wird neu berechnet
7. 🚗 Beim nächsten Laden: Auto ist weiter gefahren!

## 📞 Support

Bei Fragen oder Problemen:
- **E-Mail:** teresa@ignatzek.de
- **GitHub Issues:** [github.com/3vilQu33n/iu-studiennavigator/issues](https://github.com/3vilQu33n/iu-studiennavigator/issues)

---

**Viel Erfolg bei der Demo! 🚀**