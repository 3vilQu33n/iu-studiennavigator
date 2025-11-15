// static/dashboard.js
// Interaktionen für Dashboard: Auto-Click, Infotainment-Popup, Semester-Modal, Prüfungsanmeldung

document.addEventListener('DOMContentLoaded', function() {
    initCarClick();
    // Warte kurz, dann initialisiere Schilder mit SVG-Inline-Loading
    setTimeout(() => {
        initSemesterSigns();
    }, 300);
});

// ============================================================================
// AUTO-CLICK     Infotainment-Popup (Template-basiert)
// ============================================================================

function initCarClick() {
    const car = document.querySelector('.car-overlay');
    if (!car) {
        console.warn('Auto-Element nicht gefunden');
        return;
    }

    car.style.cursor = 'pointer';
    car.addEventListener('click', showInfotainmentPopup);
}

function showInfotainmentPopup() {
    console.log('Öffne Infotainment-Popup...');

    // Template klonen
    const template = document.getElementById('infotainment-popup-template');
    if (!template) {
        console.error(' Template nicht gefunden!');
        return;
    }

    const popup = template.content.cloneNode(true);

    // 1. Notendurchschnitt
    const gradeValue = popup.querySelector('#popup-grade-value');
    const safeGrade = (typeof progressGrade !== 'undefined') ? progressGrade : 'Keine Daten';
    const gradeClass = (typeof gradeCategory !== 'undefined') ? gradeCategory : 'medium';

    gradeValue.textContent = safeGrade;
    gradeValue.className = 'title-value ' + gradeClass;

    // 2. Zeit-Icon dynamisch
    const timeIcon = popup.querySelector('#popup-time-icon');
    const timeText = popup.querySelector('#popup-time-text');

    if (typeof timeStatus !== 'undefined') {
        if (timeStatus === 'ahead') {
            timeIcon.src = '/static/uploads/akku_voll.svg';
            timeIcon.className = 'progress-icon icon-green';
        } else if (timeStatus === 'minus') {
            timeIcon.src = '/static/uploads/dc_laden.svg';
            timeIcon.className = 'progress-icon icon-red';
        } else {
            timeIcon.src = '/static/uploads/ac_laden.svg';
            timeIcon.className = 'progress-icon icon-blue';
        }
    } else {
        timeIcon.src = '/static/uploads/ac_laden.svg';
        timeIcon.className = 'progress-icon icon-blue';
    }

    // 3. Zeit-Text
    const safeTimeText = (typeof progressTime !== 'undefined') ? progressTime : 'Keine Daten';
    timeText.textContent = safeTimeText;
    timeText.className = 'value ' + gradeClass;

    // 4. Geb  hren-Text
    const feeText = popup.querySelector('#popup-fee-text');
    const safeFeeText = (typeof progressFee !== 'undefined') ? progressFee : 'Keine Daten';
    feeText.textContent = safeFeeText;

    // 5. ✅ NEU: Prüfungsdaten dynamisch setzen
    const examText = popup.querySelector('#popup-exam-text');

    if (typeof nextExam !== 'undefined' && nextExam !== null) {
        const tage = nextExam.tage_bis_pruefung;
        const modulName = nextExam.modul_name;
        const datum = nextExam.datum;
        const modus = getPruefungsartLabel(nextExam.anmeldemodus);

        // Text formatieren
        if (tage === 0) {
            examText.innerHTML = `<strong>HEUTE!</strong><br>${modulName} (${modus})`;
        } else if (tage === 1) {
            examText.innerHTML = `<strong>MORGEN!</strong><br>${modulName} (${modus})`;
        } else if (tage < 0) {
            examText.innerHTML = `<strong>UEBERFAELLIG!</strong><br>${modulName}`;
        } else {
            examText.innerHTML = `Prüfung in <strong>${tage} Tagen</strong><br>${modulName} (${modus})<br><small>${formatDate(datum)}</small>`;
        }
    } else {
        examText.textContent = 'Keine Prüfung angemeldet';
    }

    // 6. Miniatur-Auto positionieren
    if (typeof carData !== 'undefined') {
        const miniCar = popup.querySelector('#popup-car');
        if (miniCar) {
            // Y-Offset um das Auto etwas zu verschieben (negativ = nach oben, positiv = nach unten)
            const Y_OFFSET = -3; // Passe diesen Wert an: -5 fuer mehr Abstand nach oben

            miniCar.style.left = (carData.x_percent * 100) + '%';
            miniCar.style.top = ((carData.y_percent * 100) + Y_OFFSET) + '%';
            const rotation = 'rotate(' + (carData.angle || 0) + 'deg)';
            const flip = carData.flip ? ' scaleX(-1)' : '';
            miniCar.style.transform = 'translate(-60%, -50%) ' + rotation + flip;

            console.log('Miniatur-Auto Position: X=' + (carData.x_percent * 100) + '%, Y=' + ((carData.y_percent * 100) + Y_OFFSET) + '%');
        } else {
            console.error('Miniatur-Auto nicht gefunden (#popup-car)');
        }
    }

    // Popup zum DOM hinzufuegen
    document.body.appendChild(popup);

    // Close-Button - WICHTIG: Nach dem Einfuegen ins DOM!
    setTimeout(() => {
        const closeBtn = document.querySelector('.close-popup-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeInfotainment);
            console.log('Close-Button Event Listener hinzugefuegt');
        } else {
            console.error('Close-Button nicht gefunden (.close-popup-btn)');
        }
    }, 10);

    setTimeout(function() {
        const popupElement = document.querySelector('.infotainment-popup');
        if (popupElement) popupElement.classList.add('show');
    }, 10);
}

function closeInfotainment() {
    const popup = document.querySelector('.infotainment-popup');
    if (popup) {
        popup.classList.remove('show');
        setTimeout(() => popup.remove(), 300);
    }
}

// ============================================================================
// SEMESTER-MODAL (MIT SVG-INLINE-LOADING F  R VERSCHACHTELTE IDs)
// ============================================================================

function initSemesterSigns() {
    console.log('     Initialisiere Semester-Schilder...');

    const pathOverlay = document.querySelector('.path-overlay');
    if (!pathOverlay) {
        console.warn(' Path-Overlay nicht gefunden');
        return;
    }

    // Lade SVG-Inhalt und ersetze img durch inline SVG
    fetch(pathOverlay.src)
        .then(response => response.text())
        .then(svgContent => {
            // Parse SVG
            const parser = new DOMParser();
            const svgDoc = parser.parseFromString(svgContent, 'image/svg+xml');
            const svgElement = svgDoc.querySelector('svg');

            if (!svgElement) {
                console.error(' Kein SVG-Element gefunden');
                return;
            }

            //   bertrage Styling vom img-Tag
            svgElement.classList.add('path-overlay');
            svgElement.style.position = 'absolute';
            svgElement.style.top = '12%';
            svgElement.style.left = '25%';
            svgElement.style.width = '70%';
            svgElement.style.height = '75%';
            svgElement.style.pointerEvents = 'auto'; // WICHTIG: Klicks aktivieren!

            // Ersetze img durch inline SVG
            pathOverlay.replaceWith(svgElement);

            console.log('OK: SVG erfolgreich inline geladen');

            // Jetzt k  nnen wir die IDs finden (auch wenn sie in <g> verschachtelt sind)
            for (let i = 1; i <= 7; i++) {
                const sign = document.getElementById('sign_sem' + i);
                if (sign) {
                    sign.style.cursor = 'pointer';
                    sign.style.pointerEvents = 'auto';

                    sign.addEventListener('click', (e) => {
                        e.stopPropagation();
                        console.log('KLICK: Klick auf Semester ' + i);
                        showSemesterModal(i);
                    });

                    // Hover-Effekt fuer besseres Feedback
                    sign.addEventListener('mouseenter', () => {
                        sign.style.opacity = '0.7';
                    });
                    sign.addEventListener('mouseleave', () => {
                        sign.style.opacity = '1';
                    });

                    console.log('OK: sign_sem' + i + ' ist jetzt klickbar');
                } else {
                    console.warn(' sign_sem' + i + ' nicht gefunden im SVG');
                }
            }

            // Bachelor-Schild (optional)
            const bachelorSign = document.getElementById('sign_bachelor');
            if (bachelorSign) {
                bachelorSign.style.cursor = 'pointer';
                bachelorSign.style.pointerEvents = 'auto';

                bachelorSign.addEventListener('click', (e) => {
                    e.stopPropagation();
                    console.log('     Klick auf Bachelor-Schild');
                    showNotification('Bachelor-Abschluss! ', 'success');
                });

                bachelorSign.addEventListener('mouseenter', () => {
                    bachelorSign.style.opacity = '0.7';
                });
                bachelorSign.addEventListener('mouseleave', () => {
                    bachelorSign.style.opacity = '1';
                });

                console.log('OK: sign_bachelor ist klickbar');
            }
        })
        .catch(error => {
            console.error(' Fehler beim Laden der SVG:', error);
        });
}

async function showSemesterModal(semesterNr) {
    console.log('📋 Öffne Modal für Semester ' + semesterNr);

    // Modal erstellen
    const modal = document.createElement('div');
    modal.className = 'semester-modal';
    modal.innerHTML = `
        <div class="semester-modal-content">
            <div class="modal-header">
                <h2>Semester ${semesterNr}</h2>
                <button class="close-modal" onclick="closeSemesterModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="loading">Lade Module...</div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('show'), 10);

    // Module laden
    try {
        const response = await fetch(`/semester/${semesterNr}`);
        const data = await response.json();

        if (data.success) {
            // OK: DEBUG: Module-Daten anzeigen
            console.log('     Module Data:', data.modules);
            renderModules(data.modules, modal, semesterNr);
        } else {
            showError(modal, data.error);
        }
    } catch (error) {
        console.error('Fehler beim Laden der Module:', error);
        showError(modal, 'Serverfehler beim Laden der Module');
    }
}

function renderModules(modules, modal, semesterNr) {
    const modalBody = modal.querySelector('.modal-body');

    if (!modules || modules.length === 0) {
        modalBody.innerHTML = '<p class="no-modules">Keine Module in diesem Semester.</p>';
        return;
    }

    const moduleList = modules.map(m => {
        // ✅ Formatiere Prüfungsdatum für Anzeige
        let examInfo = '';
        if (m.pruefungsdatum) {
            const datum = new Date(m.pruefungsdatum);
            const formattedDate = datum.toLocaleDateString('de-DE', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
            const modus = getPruefungsartLabel(m.anmeldemodus);
            examInfo = `
                <div class="exam-info">
                     Prüfung: ${formattedDate}<br>
                    ${modus}
                </div>
            `;
        }

        return `
            <div class="modul-card ${m.status}">
                <div class="modul-header">
                    <h3>${m.name}</h3>
                    <span class="ects-badge">${m.ects} ECTS</span>
                </div>
                
                <div class="modul-info">
                    <span class="pflichtgrad">${m.pflichtgrad}</span>
                    ${m.note ? `<span class="note">Note: ${m.note}</span>` : ''}
                    ${m.status === 'anerkannt' ? `<span class="note">Ohne Note</span>` : ''}
                </div>
                
                <div class="modul-status">
                    ${getStatusBadge(m.status)}
                    ${examInfo}
                </div>
                
                ${m.buchbar && m.status === 'offen' ? 
                    `<button class="book-btn" onclick="buchModul(${m.modul_id}, ${semesterNr})">
                        Modul buchen
                    </button>` : ''}
                
                ${m.status === 'gebucht' && !m.pruefungsdatum ? 
                    // PrÃ¼fe ob PrÃ¼fungsarten vorhanden sind
                    (m.erlaubte_pruefungsarten && m.erlaubte_pruefungsarten.length > 0 ?
                        `<button class="exam-btn" onclick='openExamModal(${m.modulbuchung_id}, "${m.name}", ${semesterNr}, ${JSON.stringify(m.erlaubte_pruefungsarten)})'>
                            Prüfung anmelden
                        </button>` :
                        `<div class="info-badge">â³ PrÃ¼fungsart wird noch festgelegt</div>`
                    ) : ''}
            </div>
        `;
    }).join('');

    modalBody.innerHTML = `<div class="module-grid">${moduleList}</div>`;
}

function getStatusBadge(status) {
    const badges = {
        'bestanden': '<span class="status-badge passed">Bestanden</span>',
        'anerkannt': '<span class="status-badge recognized">Anerkannt</span>',
        'gebucht': '<span class="status-badge booked">Gebucht</span>',
        'angemeldet': '<span class="status-badge registered">Angemeldet</span>',
        'offen': '<span class="status-badge open">Offen</span>',
        'nicht_bestanden': '<span class="status-badge failed">Nicht bestanden</span>'
    };
    return badges[status] || badges['offen'];
}

function getPruefungsartLabel(art) {
    const labels = {
        'online': 'Online-Klausur',
        'praesenz': 'Praesenz-Klausur',
        'workbook': 'Workbook',
        'projekt': 'Projekt',
        'portfolio': 'Portfolio',
        'fallstudie': 'Fallstudie',
        'praesentation': 'Fachpraesentation',
        'seminar': 'Seminararbeit',
        'hausarbeit': 'Hausarbeit',
        'abschlussarbeit': 'Abschlussarbeit',
        'kolloquium': 'Kolloquium'
    };
    return labels[art] || art;
}

function showError(modal, message) {
    const modalBody = modal.querySelector('.modal-body');
    modalBody.innerHTML = `<p class="error">${message}</p>`;
}

function closeSemesterModal() {
    const modal = document.querySelector('.semester-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
}

// ============================================================================
// MODUL BUCHEN
// ============================================================================

async function buchModul(modulId, semester) {
    console.log(`📚 Buche Modul ${modulId} für Semester ${semester}`);

    try {
        const response = await fetch('/api/book-module', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                modul_id: modulId,
                semester: semester
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('OK: Modul erfolgreich gebucht!', 'success');
            // Modal neu laden
            closeSemesterModal();
            setTimeout(() => showSemesterModal(semester), 400);
        } else {
            // OK: NEU: Spezielle Behandlung fuer Semester-Prerequisite-Fehler
            const errorMsg = data.error || 'Unbekannter Fehler';

            // L  ngere Anzeigedauer fuer wichtige Validierungsfehler
            if (errorMsg.includes('Semester') || errorMsg.includes('frher')) {
                showNotification(errorMsg, 'error', 6000);
            } else {
                showNotification('Fehler: ' + errorMsg, 'error');
            }

            console.error(' Buchung abgelehnt:', errorMsg);
        }
    } catch (error) {
        console.error(' Buchungsfehler:', error);
        showNotification('Verbindungsfehler', 'error');
    }
}

// ============================================================================
// OK: PR  FUNGSANMELDUNG
// ============================================================================

function openExamModal(modulbuchungId, modulName, semester, erlaubteArten = [{wert: 'klausur', anzeigename: 'Klausur', hat_unterteilung: true}]) {
    console.log('=== OPEN EXAM MODAL DEBUG ===');
    console.log('modulbuchungId:', modulbuchungId, typeof modulbuchungId);
    console.log('modulName:', modulName);
    console.log('semester:', semester);
    console.log('erlaubteArten:', erlaubteArten);

    if (!modulbuchungId || modulbuchungId === 'undefined' || modulbuchungId === 'null') {
        console.error('FEHLER: modulbuchung_id ist ungueltig!');
        showNotification('Fehler: Modul-ID fehlt', 'error');
        return;
    }

    console.log(`Öffne Prüfungsanmeldung für: ${modulName} (Buchung: ${modulbuchungId})`);

    // PrÃ¼fe ob Klausur dabei ist (hat_unterteilung = true)
    const hasKlausur = erlaubteArten.some(art => art.hat_unterteilung);

    // Erstelle Hauptauswahl
    let hauptOptionen = '<option value="">-- Bitte wählen --</option>';
    erlaubteArten.forEach(art => {
        hauptOptionen += `<option value="${art.wert}" data-hat-unterteilung="${art.hat_unterteilung}">${art.anzeigename}</option>`;
    });

    const examModal = document.createElement('div');
    examModal.className = 'exam-modal';
    examModal.innerHTML = `
        <div class="exam-modal-content">
            <div class="exam-modal-header">
<h3>Prüfung anmelden</h3>
                <button class="close-modal" onclick="closeExamModal()">&times;</button>
            </div>
            
            <div class="exam-modal-body">
                <p class="exam-modul-name">${modulName}</p>
                
                <form id="exam-form">
                    <div class="form-group">
                        <label for="exam-date">
                            Prüfungsdatum:
                        </label>
                        <input 
                            type="date" 
                            id="exam-date" 
                            name="exam_date" 
                            required
                            min="${getTodayDate()}"
                        >
                    </div>
                    
                    <div class="form-group">
                        <label for="exam-mode">
                            Prüfungsform:
                        </label>
                        <select id="exam-mode" name="exam_mode" required>
                            ${hauptOptionen}
                        </select>
                    </div>
                    
                    <div class="form-group" id="klausur-typ-gruppe" style="display: none;">
                        <label for="klausur-typ">
                            Klausur-Art:
                        </label>
                        <select id="klausur-typ" name="klausur_typ">
                            <option value="">-- Bitte wählen --</option>
                            <option value="online">Online</option>
                            <option value="praesenz">Praesenz</option>
                        </select>
                    </div>
                    
                    <div class="exam-modal-buttons">
                        <button type="button" class="exam-submit-btn" onclick="submitExamRegistration(${modulbuchungId}, ${semester})">
                            Anmelden
                        </button>
                        <button type="button" class="exam-cancel-btn" onclick="closeExamModal()">
                            Abbrechen
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;

    document.body.appendChild(examModal);
    setTimeout(() => examModal.classList.add('show'), 10);

    // Event-Listener fÃ¼r PrÃ¼fungsart-Wechsel
    const examModeSelect = document.getElementById('exam-mode');
    const klausurTypGruppe = document.getElementById('klausur-typ-gruppe');
    const klausurTypSelect = document.getElementById('klausur-typ');

    examModeSelect.addEventListener('change', function() {
        // Finde die ausgewählte Prüfungsart aus erlaubteArten
        const selectedArt = erlaubteArten.find(art => art.wert === this.value);

        // Prüfe ob diese Prüfungsart eine Unterteilung hat (z.B. Klausur → online/präsenz)
        if (selectedArt && selectedArt.hat_unterteilung) {
            // Zeige Klausur-Typ Dropdown
            klausurTypGruppe.style.display = 'block';
            klausurTypSelect.required = true;
        } else {
            // Verstecke Klausur-Typ Dropdown
            klausurTypGruppe.style.display = 'none';
            klausurTypSelect.required = false;
            klausurTypSelect.value = '';
        }
    });
}

function closeExamModal() {
    const modal = document.querySelector('.exam-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
}

async function submitExamRegistration(modulbuchungId, semester) {
    // Hole Daten direkt aus dem Form
    const examDate = document.getElementById('exam-date').value;
    const examMode = document.getElementById('exam-mode').value;
    const klausurTyp = document.getElementById('klausur-typ').value;

    // OK: DEBUG
    console.log('=== PR  FUNGSANMELDUNG DEBUG ===');
    console.log('modulbuchungId:', modulbuchungId, typeof modulbuchungId);
    console.log('examDate:', examDate, typeof examDate);
    console.log('examMode:', examMode, typeof examMode);
    console.log('klausurTyp:', klausurTyp, typeof klausurTyp);

    // Validierung
    if (!examDate || !examMode) {
        showNotification('Bitte alle Felder ausfüllen', 'error');
        return;
    }

    // Bei Klausur muss auch der Typ gewÃ¤hlt sein
    const selectedArt = document.getElementById('exam-mode');
    const selectedValue = selectedArt.value;

    // Hole die komplette Prüfungsart-Info aus dem Modal-Kontext (über data-attribute)
    const hatUnterteilung = selectedArt.selectedOptions[0]?.dataset.hatUnterteilung === 'true';

    if (hatUnterteilung && !klausurTyp) {
        showNotification('Bitte Klausur-Art wählen (Online oder Präsenz)', 'error');
        return;
    }

    // Bestimme den finalen Anmeldemodus
    let finalMode = examMode;
    if (hatUnterteilung && klausurTyp) {
        finalMode = klausurTyp;  // 'online' oder 'praesenz'
    }

    const payload = {
        modulbuchung_id: parseInt(modulbuchungId),
        pruefungsdatum: examDate,
        anmeldemodus: finalMode
    };

    console.log('     Payload:', JSON.stringify(payload));

    try {
        const response = await fetch('/api/register-exam', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        console.log('     Response Status:', response.status);

        const data = await response.json();
        console.log('     Response Data:', data);

        if (data.success) {
            showNotification('✅ Prüfung erfolgreich angemeldet!', 'success');
            closeExamModal();
            closeSemesterModal();
            setTimeout(() => showSemesterModal(semester), 400);
        } else {
            showNotification('Fehler: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('❌ Fehler bei Prüfungsanmeldung:', error);
        showNotification('Verbindungsfehler', 'error');
    }
}

function getTodayDate() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// ============================================================================
// HELPER: Datum formatieren
// ============================================================================

function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
    return date.toLocaleDateString('de-DE', options);
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}