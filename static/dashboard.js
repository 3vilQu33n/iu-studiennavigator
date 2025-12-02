// static/dashboard.js
// Interaktionen fuer Dashboard: Auto-Click, Infotainment-Popup, Semester-Modal, Pruefungsanmeldung
// NEU: SVG-Pfad-basierte Auto-Positionierung

document.addEventListener('DOMContentLoaded', function() {
    initCarClick();
    // Warte kurz, dann initialisiere Schilder mit SVG-Inline-Loading
    setTimeout(() => {
        initSemesterSigns();
    }, 300);
});

// ============================================================================
// SVG-PFAD-BASIERTE AUTO-POSITIONIERUNG
// ============================================================================

/**
 * Positioniert das Auto entlang der SVG-Pfade
 * Wird aufgerufen nachdem die SVG inline geladen wurde
 */
function initCarPositioning(svgElement) {
    console.log('Initialisiere Auto-Positionierung...');

    // Pfade sammeln (path1_2, path2_3, etc.)
    const paths = {};
    const pathLengths = {};

    for (let i = 1; i <= 7; i++) {
        // Suche nach dem Mittellinienpfad (bevorzugt _center)
        let pathElement = svgElement.getElementById(`path${i}_${i+1}_center`) ||
                          svgElement.getElementById(`path${i}_center`);

        // Fallback: Suche in der Gruppe nach dem Pfad
        if (!pathElement) {
            let pathGroup = svgElement.getElementById(`path${i}_${i+1}`) ||
                            svgElement.getElementById(`path${i}`) ||
                            svgElement.querySelector(`[id*="path${i}"]`);

            if (pathGroup) {
                pathElement = pathGroup.querySelector('path') || pathGroup;
            }
        }

        if (pathElement && pathElement.getTotalLength) {
            paths[i] = pathElement;
            pathLengths[i] = pathElement.getTotalLength();
            console.log(`  Pfad ${i} geladen: Laenge = ${pathLengths[i].toFixed(2)}`);
        } else {
            console.warn(`  Pfad ${i} nicht gefunden`);
        }
    }

    // Pruefe ob genug Pfade gefunden wurden
    const foundPaths = Object.keys(paths).length;
    if (foundPaths === 0) {
        console.warn('Keine Pfade gefunden - verwende Fallback-Positionierung');
        return null;
    }

    console.log(`${foundPaths} Pfade geladen`);

    // Positioner-Objekt zurueckgeben
    return {
        paths: paths,
        pathLengths: pathLengths,

        /**
         * Berechnet Position und Rotation fuer eine Semester-Position
         * Auto wird auf dem Pfad zwischen zwei Schildern positioniert
         * @param {number} semester - 1 bis 7
         */
        calculatePosition: function(semester) {
            semester = Math.max(1, Math.min(7, Math.floor(semester)));

            // Pfad fuer dieses Semester (Pfad zwischen Semester N und N+1)
            var path = this.paths[semester];
            if (!path) {
                console.warn('Pfad ' + semester + ' nicht verfuegbar');
                return this._getFallbackPosition(semester);
            }

            // Individuelle Position auf jedem Pfad (angepasst an Pfadverlauf)
            var pathPositions = {
                1: 0.50,  // Pfad 1->2: Mitte
                2: 0.45,  // Pfad 2->3: Mitte
                3: 0.60,  // Pfad 3->4: Weiter unten (60% statt 50%)
                4: 0.50,  // Pfad 4->5: Mitte
                5: 0.50,  // Pfad 5->6: Mitte
                6: 0.79,  // Pfad 6->7: Mitte
                7: 0.05   // Pfad 7->Bachelor: Weiter links (30%) weil Pfad sehr kurz
            };

            var positionOnPath = pathPositions[semester] || 0.5;
            var pathLength = this.pathLengths[semester];
            var lengthOnPath = pathLength * positionOnPath;

            return this._getPointWithRotation(path, lengthOnPath);
        },

        /**
         * Holt Punkt und berechnet Rotation aus Tangente
         */
        _getPointWithRotation: function(path, length) {
            var point = path.getPointAtLength(length);

            // Tangente berechnen
            var delta = 0.5;
            var maxLength = path.getTotalLength();

            var p1 = path.getPointAtLength(Math.max(0, length - delta));
            var p2 = path.getPointAtLength(Math.min(maxLength, length + delta));

            var dx = p2.x - p1.x;
            var dy = p2.y - p1.y;
            var rotation = Math.atan2(dy, dx) * (180 / Math.PI);

            return {
                x: point.x,
                y: point.y,
                rotation: rotation
            };
        },

        /**
         * Fallback wenn Pfad nicht gefunden
         */
        _getFallbackPosition: function(position) {
            // ViewBox der SVG: 0 0 1435.7 858.6
            const FALLBACK = {
                1: {x: 303, y: 130, rotation: 0},    // Bei sign_sem1
                2: {x: 700, y: 230, rotation: 5},
                3: {x: 1000, y: 280, rotation: -5},
                4: {x: 800, y: 400, rotation: 180},
                5: {x: 500, y: 500, rotation: 0},
                6: {x: 700, y: 550, rotation: 0},
                7: {x: 900, y: 600, rotation: 0}
            };

            const pos = Math.round(position);
            return FALLBACK[pos] || FALLBACK[1];
        }
    };
}

/**
 * Positioniert das Auto-Overlay basierend auf SVG-Koordinaten
 */
function positionCarOnPath(svgElement, positioner, semesterPosition) {
    if (!positioner) {
        console.warn('Kein Positioner verfuegbar - verwende CSS-Fallback');
        return;
    }

    const pos = positioner.calculatePosition(semesterPosition);

    // ViewBox fuer Prozent-Umrechnung
    const viewBox = svgElement.viewBox.baseVal;

    // Position innerhalb des SVG (0-100%)
    const xPercentInSvg = (pos.x / viewBox.width) * 100;
    const yPercentInSvg = (pos.y / viewBox.height) * 100;

    // SVG-Offset und -Groesse im Container
    const svgLeft = 25;   // %
    const svgTop = 12;    // %
    const svgWidth = 70;  // %
    const svgHeight = 75; // %

    // Umrechnung in Container-Koordinaten
    const xPercentInContainer = svgLeft + (xPercentInSvg * svgWidth / 100);
    const yPercentInContainer = svgTop + (yPercentInSvg * svgHeight / 100);

    // Auto-Overlay finden
    const carOverlay = document.querySelector('.car-overlay');
    if (!carOverlay) {
        console.warn('Car-Overlay nicht gefunden');
        return;
    }

    // CSS-Position setzen (relativ zum Container)
    carOverlay.style.left = `${xPercentInContainer}%`;
    carOverlay.style.top = `${yPercentInContainer}%`;
    carOverlay.style.transform = `translate(-50%, -50%) rotate(${pos.rotation}deg)`;

    // Flip-Logik: Wenn Rotation > 90° oder < -90°, Auto spiegeln
    if (Math.abs(pos.rotation) > 90) {
        carOverlay.style.transform += ' scaleY(-1)';
    }

    console.log(`🚗 Auto positioniert:`);
    console.log(`  - SVG-Position: (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)})`);
    console.log(`  - SVG-Prozent: (${xPercentInSvg.toFixed(1)}%, ${yPercentInSvg.toFixed(1)}%)`);
    console.log(`  - Container-Prozent: (${xPercentInContainer.toFixed(1)}%, ${yPercentInContainer.toFixed(1)}%)`);
    console.log(`  - Rotation: ${pos.rotation.toFixed(1)}°`);
}

// ============================================================================
// AUTO-CLICK â†’ Infotainment-Popup (Template-basiert)
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
    console.log('Oeffne Infotainment-Popup...');

    // Template klonen
    const template = document.getElementById('infotainment-popup-template');
    if (!template) {
        console.error('Template nicht gefunden!');
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

    // 4. Gebuehren-Text
    const feeText = popup.querySelector('#popup-fee-text');
    const safeFeeText = (typeof progressFee !== 'undefined') ? progressFee : 'Keine Daten';
    feeText.textContent = safeFeeText;

    // 5. Pruefungsdaten dynamisch setzen
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
            examText.innerHTML = `Pruefung in <strong>${tage} Tagen</strong><br>${modulName} (${modus})<br><small>${formatDate(datum)}</small>`;
        }
    } else {
        examText.textContent = 'Keine Pruefung angemeldet';
    }

    // Popup zum DOM hinzufuegen
    document.body.appendChild(popup);

    // Close-Button
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

        // Popup-SVG inline laden und Auto positionieren
        initPopupCarPositioning();
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
// POPUP AUTO-POSITIONIERUNG
// ============================================================================

function initPopupCarPositioning() {
    const miniaturePfad = document.querySelector('.miniature-pfad');
    const miniatureCar = document.querySelector('.miniature-car');

    if (!miniaturePfad || !miniatureCar) {
        console.warn('Popup-Elemente nicht gefunden');
        return;
    }

    // Lade SVG inline (mit Cache-Busting)
    var cacheBuster = '?t=' + Date.now();
    var fetchUrl = miniaturePfad.src + cacheBuster;
    console.log('🔗 Popup SVG URL:', fetchUrl);
    fetch(fetchUrl)
        .then(response => response.text())
        .then(svgContent => {
            const parser = new DOMParser();
            const svgDoc = parser.parseFromString(svgContent, 'image/svg+xml');
            const svgElement = svgDoc.querySelector('svg');

            if (!svgElement) {
                console.error('Popup SVG nicht gefunden');
                return;
            }

            // Styling uebertragen - WICHTIG: Transform beibehalten
            svgElement.classList.add('miniature-pfad');
            svgElement.style.position = 'absolute';
            svgElement.style.top = '50%';
            svgElement.style.left = '50%';
            svgElement.style.width = '100%';
            svgElement.style.height = '100%';
            svgElement.style.objectFit = 'contain';
            svgElement.style.transform = 'translate(-50%, -50%) scale(1.08)';
            svgElement.style.transformOrigin = 'center center';

            // Ersetze img durch inline SVG
            miniaturePfad.replaceWith(svgElement);

            console.log('Popup-SVG inline geladen');

            // Positioner erstellen
            const positioner = initPopupPathPositioner(svgElement);

            if (positioner) {
                // Semester-Position holen
                const semesterPosition = typeof currentSemesterPosition !== 'undefined'
                    ? currentSemesterPosition
                    : 1.0;

                // Position berechnen
                const pos = positioner.calculatePosition(semesterPosition);

                if (pos) {
                    console.log(`📍 Semester ${semesterPosition}: Pfad-Koordinaten x=${pos.x.toFixed(1)}, y=${pos.y.toFixed(1)}, rot=${pos.rotation.toFixed(1)}°`);

                    // ViewBox fuer Prozent-Umrechnung
                    const viewBox = svgElement.viewBox.baseVal;
                    const xPercent = (pos.x / viewBox.width) * 100;
                    const yPercent = (pos.y / viewBox.height) * 100;

                    // Auto positionieren
                    miniatureCar.style.left = xPercent + '%';
                    miniatureCar.style.top = yPercent + '%';
                    miniatureCar.style.transform = `translate(-50%, -50%) rotate(${pos.rotation}deg)`;

                    // Flip-Logik
                    if (Math.abs(pos.rotation) > 90) {
                        miniatureCar.style.transform += ' scaleY(-1)';
                    }

                    console.log(`Popup-Auto positioniert: ${xPercent.toFixed(1)}%, ${yPercent.toFixed(1)}%`);
                }
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Popup-SVG:', error);
        });
}

function initPopupPathPositioner(svgElement) {
    const paths = {};
    const pathLengths = {};

    console.log('🔍 Popup: Suche Pfade...');

    for (let i = 1; i <= 7; i++) {
        // Suche nach dem Mittellinienpfad mit querySelector (zuverlaessiger als getElementById)
        let pathElement = svgElement.querySelector(`#path${i}_${i+1}_center`) ||
                          svgElement.querySelector(`#path${i}_center`);

        if (pathElement && pathElement.getTotalLength) {
            paths[i] = pathElement;
            pathLengths[i] = pathElement.getTotalLength();
            console.log(`  ✓ Pfad ${i}: ${pathElement.id} (Laenge: ${pathLengths[i].toFixed(1)})`);
        } else {
            console.warn(`  ✗ Pfad ${i}: nicht gefunden oder keine getTotalLength`);
        }
    }

    if (Object.keys(paths).length === 0) {
        console.warn('Keine Pfade in Popup-SVG gefunden');
        return null;
    }

    console.log(`📍 Popup: ${Object.keys(paths).length} Pfade geladen`);

    return {
        paths: paths,
        pathLengths: pathLengths,

        calculatePosition: function(position) {
            position = Math.max(1.0, Math.min(7.0, position));

            var segmentIndex = Math.floor(position);

            // Individuelle Position auf jedem Pfad im POPUP (unabhaengig anpassbar)
            var pathPositionsPopup = {
                1: 0.50,  // Pfad 1->2: Mitte
                2: 0.40,  // Pfad 2->3: Mitte-Links
                3: 0.60,  // Pfad 3->4: Weiter unten (60% statt 50%)
                4: 0.50,  // Pfad 4->5: Mitte
                5: 0.50,  // Pfad 5->6: Mitte
                6: 0.50,  // Pfad 6->7: Mitte
                7: 0.05   // Pfad 7->Bachelor: Weiter links (5%) weil Pfad sehr kurz
            };

            // Sonderfall: Semester 7 oder hoeher -> Pfad 7 verwenden
            if (segmentIndex >= 7) {
                segmentIndex = 7;
            }

            var path = this.paths[segmentIndex];
            if (!path) {
                return null;
            }

            var pathLength = this.pathLengths[segmentIndex];
            var positionOnPath = pathPositionsPopup[segmentIndex] || 0.5;
            var lengthOnPath = pathLength * positionOnPath;

            return this._getPointWithRotation(path, lengthOnPath);
        },

        _getPointWithRotation: function(path, length) {
            const point = path.getPointAtLength(length);

            const delta = 0.5;
            const maxLength = path.getTotalLength();

            const p1 = path.getPointAtLength(Math.max(0, length - delta));
            const p2 = path.getPointAtLength(Math.min(maxLength, length + delta));

            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const rotation = Math.atan2(dy, dx) * (180 / Math.PI);

            return {
                x: point.x,
                y: point.y,
                rotation: rotation
            };
        }
    };
}

// ============================================================================
// SEMESTER-MODAL (MIT SVG-INLINE-LOADING + AUTO-POSITIONIERUNG)
// ============================================================================
// ============================================================================

function initSemesterSigns() {
    console.log('Initialisiere Semester-Schilder...');

    const pathOverlay = document.querySelector('.path-overlay');
    if (!pathOverlay) {
        console.warn('Path-Overlay nicht gefunden');
        return;
    }

    // Lade SVG-Inhalt und ersetze img durch inline SVG (mit Cache-Busting)
    var cacheBuster = '?t=' + Date.now();
    fetch(pathOverlay.src + cacheBuster)
        .then(response => response.text())
        .then(svgContent => {
            // Parse SVG
            const parser = new DOMParser();
            const svgDoc = parser.parseFromString(svgContent, 'image/svg+xml');
            const svgElement = svgDoc.querySelector('svg');

            if (!svgElement) {
                console.error('Kein SVG-Element gefunden');
                return;
            }

            // Uebertrage Styling vom img-Tag
            svgElement.classList.add('path-overlay');
            svgElement.style.position = 'absolute';
            svgElement.style.pointerEvents = 'auto';
            // Behalte die urspruenglichen Dimensionen bei
            svgElement.style.top = '12%';
            svgElement.style.left = '25%';
            svgElement.style.width = '70%';
            svgElement.style.height = '75%';

            // Ersetze img durch inline SVG
            pathOverlay.replaceWith(svgElement);

            console.log('SVG erfolgreich inline geladen');

            // ========== NEU: Auto-Positionierung initialisieren ==========
            const positioner = initCarPositioning(svgElement);

            // Semester-Position vom Server holen
            // Option 1: Aus data-Attribut
            let semesterPosition = parseFloat(document.body.dataset.semesterPosition);

            // Option 2: Aus globaler Variable (falls vom Template gesetzt)
            if (isNaN(semesterPosition) && typeof currentSemesterPosition !== 'undefined') {
                semesterPosition = currentSemesterPosition;
            }

            // Fallback
            if (isNaN(semesterPosition)) {
                semesterPosition = 1.0;
            }

            console.log(`Semester-Position: ${semesterPosition}`);

            // Auto positionieren
            positionCarOnPath(svgElement, positioner, semesterPosition);

            // Positioner global verfuegbar machen (fuer spaetere Updates)
            window.carPositioner = positioner;
            window.roadmapSvg = svgElement;
            // =============================================================

            // Semester-Schilder klickbar machen
            for (let i = 1; i <= 7; i++) {
                // Versuche verschiedene ID-Formate
                const sign = document.getElementById('sign_sem_' + i) ||
                             document.getElementById('sign_sem' + i) ||
                             document.getElementById('sign_sem_' + i + '_') ||
                             document.getElementById('sing_sem_' + i) ||  // Tippfehler in Screenshot
                             document.querySelector(`[id*="sem_${i}"]`) ||
                             document.querySelector(`[id*="sem${i}"]`);

                if (sign) {
                    sign.style.cursor = 'pointer';
                    sign.style.pointerEvents = 'auto';

                    sign.addEventListener('click', (e) => {
                        e.stopPropagation();
                        console.log('Klick auf Semester ' + i);
                        showSemesterModal(i);
                    });

                    // Hover-Effekt
                    sign.addEventListener('mouseenter', () => {
                        sign.style.opacity = '0.7';
                    });
                    sign.addEventListener('mouseleave', () => {
                        sign.style.opacity = '1';
                    });

                    console.log('Schild Semester ' + i + ' ist jetzt klickbar (ID: ' + sign.id + ')');
                } else {
                    console.warn('Schild fuer Semester ' + i + ' nicht gefunden! Gesuchte IDs: sign_sem_' + i + ', sign_sem' + i);
                }
            }

            // Bachelor-Schild (optional)
            const bachelorSign = document.getElementById('sign_bachelor');
            if (bachelorSign) {
                bachelorSign.style.cursor = 'pointer';
                bachelorSign.style.pointerEvents = 'auto';

                bachelorSign.addEventListener('click', (e) => {
                    e.stopPropagation();
                    console.log('Klick auf Bachelor-Schild');
                    showNotification('Bachelor-Abschluss! ðŸŽ‰', 'success');
                });

                bachelorSign.addEventListener('mouseenter', () => {
                    bachelorSign.style.opacity = '0.7';
                });
                bachelorSign.addEventListener('mouseleave', () => {
                    bachelorSign.style.opacity = '1';
                });
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der SVG:', error);
        });
}

// ============================================================================
// SEMESTER-MODAL ANZEIGEN
// ============================================================================

async function showSemesterModal(semester) {
    console.log('Lade Module fuer Semester ' + semester + '...');

    try {
        const response = await fetch(`/api/semester/${semester}/modules`);
        if (!response.ok) {
            throw new Error('Fehler beim Laden der Module');
        }

        const data = await response.json();
        console.log('Module geladen:', data);

        // Template klonen
        const template = document.getElementById('semester-modal-template');
        if (!template) {
            console.error('Semester-Modal-Template nicht gefunden!');
            return;
        }

        const modalFragment = template.content.cloneNode(true);

        // Titel setzen
        modalFragment.querySelector('#semester-modal-title').textContent = 'Semester ' + semester;

        // Close-Button Event
        modalFragment.querySelector('#close-semester-modal').addEventListener('click', closeSemesterModal);

        // Module-Grid finden
        const moduleGrid = modalFragment.querySelector('#semester-modal-modules');
        const moduleTemplate = document.getElementById('module-item-template');
        const wahlmodulTemplate = document.getElementById('wahlmodul-card-template');

        // DEBUG: Zeige was vom Server kommt
        console.log('=== DEBUG SEMESTER MODAL ===');
        console.log('Semester:', semester);
        console.log('data:', data);

        // Entscheide Anzeige-Modus basierend auf Semester
        // Server gibt 'wahlmodule' zurueck (nicht 'wahlmodul_optionen')
        const wahlmodulOptionen = data.wahlmodul_optionen || data.wahlmodule || {};
        const wahlmoduleStatus = data.wahlmodule_status || data.gebuchte_wahlmodule || {};

        const hasWahlmodule = (semester === 5 || semester === 6) &&
                              wahlmodulOptionen &&
                              Object.keys(wahlmodulOptionen).length > 0;

        console.log('hasWahlmodule:', hasWahlmodule);
        console.log('wahlmodulOptionen:', wahlmodulOptionen);
        console.log('wahlmoduleStatus:', wahlmoduleStatus);

        if (hasWahlmodule) {
            // NEUER MODUS: Pflichtmodule + Wahlmodul-Dropdowns
            console.log('Semester mit Wahlmodulen - zeige Dropdown-Modus');

            // 1. Pflichtmodule anzeigen (aus modules filtern falls pflichtmodule leer)
            let pflichtmodule = data.pflichtmodule || [];

            // Fallback: Wenn pflichtmodule leer, filtere aus modules
            if (pflichtmodule.length === 0 && data.modules && data.modules.length > 0) {
                pflichtmodule = data.modules.filter(m => !m.wahlbereich);
                console.log('Pflichtmodule aus modules gefiltert:', pflichtmodule.length);
            }

            console.log('Pflichtmodule zu rendern:', pflichtmodule.length, pflichtmodule);

            pflichtmodule.forEach(modul => {
                console.log('Erstelle Karte fuer Pflichtmodul:', modul.name);
                const card = createPflichtmodulCard(modul, moduleTemplate, semester);
                if (card) moduleGrid.appendChild(card);
            });

            // 2. Wahlmodul-Karten mit Dropdowns anzeigen
            if (semester === 5 && wahlmodulOptionen.A && wahlmodulOptionen.A.length > 0) {
                const wahlmodulCardA = createWahlmodulCard(
                    'A',
                    wahlmodulOptionen.A,
                    wahlmoduleStatus.A,
                    wahlmodulTemplate,
                    semester
                );
                if (wahlmodulCardA) moduleGrid.appendChild(wahlmodulCardA);
            }

            if (semester === 6) {
                if (wahlmodulOptionen.B && wahlmodulOptionen.B.length > 0) {
                    const wahlmodulCardB = createWahlmodulCard(
                        'B',
                        wahlmodulOptionen.B,
                        wahlmoduleStatus.B,
                        wahlmodulTemplate,
                        semester
                    );
                    if (wahlmodulCardB) moduleGrid.appendChild(wahlmodulCardB);
                }

                if (wahlmodulOptionen.C && wahlmodulOptionen.C.length > 0) {
                    const wahlmodulCardC = createWahlmodulCard(
                        'C',
                        wahlmodulOptionen.C,
                        wahlmoduleStatus.C,
                        wahlmodulTemplate,
                        semester
                    );
                    if (wahlmodulCardC) moduleGrid.appendChild(wahlmodulCardC);
                }
            }

        } else {
            // STANDARD-MODUS: Alle Module als Karten (fuer Semester 1-4, 7)
            if (!data.modules || data.modules.length === 0) {
                moduleGrid.innerHTML = '<p class="no-modules">Keine Module gefunden</p>';
            } else {
                data.modules.forEach(modul => {
                    const card = createPflichtmodulCard(modul, moduleTemplate, semester);
                    if (card) moduleGrid.appendChild(card);
                });
            }
        }

        document.body.appendChild(modalFragment);

        // Animation starten
        setTimeout(function() {
            document.querySelector('.semester-modal').classList.add('show');
        }, 10);

    } catch (error) {
        console.error('Fehler:', error);
        showNotification('Fehler beim Laden der Module', 'error');
    }
}

/**
 * Erstellt eine Pflichtmodul-Karte (Standard)
 */
function createPflichtmodulCard(modul, template, semester) {
    const moduleFragment = template.content.cloneNode(true);
    const modulCard = moduleFragment.querySelector('.modul-card');

    // Status ermitteln
    const status = modul.status || 'offen';
    modulCard.classList.add(status);

    // Modul-Name
    moduleFragment.querySelector('.modul-name').textContent = modul.name;

    // ECTS Badge
    moduleFragment.querySelector('.ects-badge').textContent = modul.ects + ' ECTS';

    // Pflichtgrad
    moduleFragment.querySelector('.pflichtgrad').textContent = modul.pflichtgrad || 'Pflicht';

    // Note (nur wenn vorhanden)
    const noteElement = moduleFragment.querySelector('.note');
    if (modul.note) {
        noteElement.textContent = 'Note: ' + modul.note;
        noteElement.style.display = 'inline';
    } else {
        noteElement.style.display = 'none';
    }

    // Status-Badge
    const statusBadge = moduleFragment.querySelector('.status-badge');
    statusBadge.textContent = getStatusBadgeText(status);
    statusBadge.classList.add(getStatusBadgeClass(status));

    // Buttons - alle erstmal verstecken
    const bookBtn = moduleFragment.querySelector('.book-btn');
    const examBtn = moduleFragment.querySelector('.exam-btn');
    const examInfo = moduleFragment.querySelector('.exam-info');

    bookBtn.style.display = 'none';
    examBtn.style.display = 'none';
    examInfo.style.display = 'none';

    // Buchungs-Button (nur wenn Modul offen ist)
    if (status === 'offen') {
        bookBtn.style.display = 'block';
        bookBtn.addEventListener('click', function() {
            bookModule(modul.modul_id, semester);
        });
    }

    // Pruefungsanmeldung-Button (nur wenn gebucht und noch keine Pruefung)
    if (modul.kann_pruefung_anmelden) {
        examBtn.style.display = 'block';
        examBtn.addEventListener('click', function() {
            showExamModal(modul.modulbuchung_id, modul.name, semester, modul.erlaubte_pruefungsarten);
        });
    }

    // Pruefungsinfo (wenn bereits angemeldet)
    if (modul.pruefung_angemeldet && modul.pruefung_info) {
        examInfo.style.display = 'block';
        examInfo.innerHTML = '<strong>Pruefung angemeldet:</strong><br>' +
            'Datum: ' + formatDate(modul.pruefung_info.datum) + '<br>' +
            'Art: ' + getPruefungsartLabel(modul.pruefung_info.art);
    }

    return moduleFragment;
}

/**
 * Erstellt eine Wahlmodul-Karte mit Dropdown
 */
function createWahlmodulCard(wahlbereich, optionen, gebuchterStatus, template, semester) {
    if (!template) {
        console.error('Wahlmodul-Template nicht gefunden!');
        return null;
    }

    const moduleFragment = template.content.cloneNode(true);
    const modulCard = moduleFragment.querySelector('.modul-card');

    // Wahlbereich-Label
    const wahlbereichLabels = {
        'A': 'Wahlbereich A (Sem. 5)',
        'B': 'Wahlbereich B (Sem. 6)',
        'C': 'Wahlbereich C (Sem. 6)'
    };

    moduleFragment.querySelector('.modul-name').textContent = 'Wahlmodul ' + wahlbereich;
    moduleFragment.querySelector('.wahlbereich-label').textContent = wahlbereichLabels[wahlbereich] || 'Wahlbereich ' + wahlbereich;

    // Elemente holen
    const selectWrapper = moduleFragment.querySelector('.wahlmodul-select-wrapper');
    const select = moduleFragment.querySelector('.wahlmodul-select');
    const statusBadge = moduleFragment.querySelector('.status-badge');
    const gewaehltInfo = moduleFragment.querySelector('.gewaehlt-info');
    const gewaehltName = moduleFragment.querySelector('.gewaehlt-name');
    const bookBtn = moduleFragment.querySelector('.book-btn');
    const examBtn = moduleFragment.querySelector('.exam-btn');
    const examInfo = moduleFragment.querySelector('.exam-info');

    // Buttons erstmal verstecken
    bookBtn.style.display = 'none';
    examBtn.style.display = 'none';
    examInfo.style.display = 'none';

    // Pruefen ob bereits ein Wahlmodul gebucht ist
    if (gebuchterStatus && gebuchterStatus.modul_id) {
        // Bereits gebucht -> Dropdown verstecken, Info anzeigen
        selectWrapper.style.display = 'none';

        gewaehltInfo.style.display = 'block';
        gewaehltName.textContent = gebuchterStatus.name;

        // Status-Badge setzen
        const status = gebuchterStatus.status || 'gebucht';
        modulCard.classList.add(status);
        statusBadge.textContent = getStatusBadgeText(status);
        statusBadge.classList.add(getStatusBadgeClass(status));

        // DEBUG: Zeige was im gebuchterStatus ist
        console.log('DEBUG Wahlmodul ' + wahlbereich + ' gebuchterStatus:', gebuchterStatus);

        // Note anzeigen wenn vorhanden (bei bestanden)
        const noteElement = moduleFragment.querySelector('.note');
        console.log('DEBUG noteElement:', noteElement, 'note value:', gebuchterStatus.note);

        if (noteElement && gebuchterStatus.note) {
            noteElement.textContent = 'Note: ' + gebuchterStatus.note;
            noteElement.style.display = 'inline';
            console.log('DEBUG Note gesetzt:', gebuchterStatus.note);
        }

        console.log('Wahlbereich ' + wahlbereich + ': Bereits gebucht - ' + gebuchterStatus.name + (gebuchterStatus.note ? ' (Note: ' + gebuchterStatus.note + ')' : ''));

    } else {
        // Noch nicht gebucht -> Dropdown mit Optionen anzeigen
        modulCard.classList.add('offen');
        statusBadge.textContent = 'Offen';
        statusBadge.classList.add('open');

        // Dropdown befuellen
        optionen.forEach(option => {
            const optionEl = document.createElement('option');
            optionEl.value = option.modul_id;
            optionEl.textContent = option.name;
            select.appendChild(optionEl);
        });

        // Buchen-Button aktivieren
        bookBtn.style.display = 'block';
        bookBtn.addEventListener('click', function() {
            const selectedModulId = select.value;
            if (!selectedModulId) {
                showNotification('Bitte waehle zuerst ein Modul aus', 'error');
                return;
            }
            bookModule(parseInt(selectedModulId), semester);
        });

        console.log('Wahlbereich ' + wahlbereich + ': ' + optionen.length + ' Optionen verfuegbar');
    }

    return moduleFragment;
}

// Status-Badge Text
function getStatusBadgeText(status) {
    var texts = {
        'bestanden': 'Bestanden',
        'anerkannt': 'Anerkannt',
        'gebucht': 'Gebucht',
        'angemeldet': 'Angemeldet',
        'offen': 'Offen',
        'nicht_bestanden': 'Nicht bestanden'
    };
    return texts[status] || status;
}

// Status-Badge CSS-Klasse
function getStatusBadgeClass(status) {
    var classes = {
        'bestanden': 'passed',
        'anerkannt': 'recognized',
        'gebucht': 'booked',
        'angemeldet': 'registered',
        'offen': 'open',
        'nicht_bestanden': 'failed'
    };
    return classes[status] || 'open';
}

// Modul buchen
async function bookModule(modulId, semester) {
    console.log('Buche Modul ' + modulId + ' fuer Semester ' + semester);

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
            showNotification(data.message || 'Modul erfolgreich gebucht!', 'success');
            closeSemesterModal();
            // Modal neu laden um aktualisierten Status zu zeigen
            setTimeout(function() {
                showSemesterModal(semester);
            }, 400);
        } else {
            showNotification('Fehler: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Fehler beim Buchen:', error);
        showNotification('Verbindungsfehler beim Buchen', 'error');
    }
}

function closeSemesterModal() {
    const modal = document.querySelector('.semester-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
}

function getStatusText(status) {
    var statusMap = {
        'bestanden': 'Bestanden',
        'anerkannt': 'Anerkannt',
        'gebucht': 'Gebucht',
        'offen': 'Offen',
        'nicht_bestanden': 'Nicht bestanden'
    };
    return statusMap[status] || status;
}

function getPruefungsartLabel(art) {
    var labels = {
        'klausur': 'Klausur',
        'online': 'Online-Klausur',
        'praesenz': 'Praesenz-Klausur',
        'hausarbeit': 'Hausarbeit',
        'portfolio': 'Portfolio',
        'muendlich': 'Muendliche Pruefung',
        'projekt': 'Projektarbeit',
        'bachelorarbeit': 'Bachelorarbeit',
        'fallstudie': 'Fallstudie',
        'fachpraesentation': 'Fachpraesentation',
        'creative_workbook': 'Creative Workbook',
        'K': 'Klausur',
        'PO': 'Portfolio',
        'HA': 'Hausarbeit',
        'FA': 'Fallstudie',
        'FP': 'Fachpraesentation',
        'AW': 'Advanced Workbook'
    };
    return labels[art] || art;
}

// ============================================================================
// PRUEFUNGSANMELDUNG MODAL
// ============================================================================

function showExamModal(modulbuchungId, modulName, semester, erlaubteArten) {
    console.log('Oeffne Pruefungsanmeldung fuer:', modulName);
    console.log('Erlaubte Arten:', erlaubteArten);

    // Template klonen
    var template = document.getElementById('exam-modal-template');
    if (!template) {
        console.error('Exam-Modal-Template nicht gefunden!');
        return;
    }

    var modal = template.content.cloneNode(true);

    // Modul-Name setzen
    modal.querySelector('#exam-modul-name').textContent = modulName;

    // Datum min-Attribut setzen
    modal.querySelector('#exam-date').setAttribute('min', getTodayDate());

    // Pruefungsarten-Dropdown befuellen
    var examModeSelect = modal.querySelector('#exam-mode');
    erlaubteArten.forEach(function(art) {
        var option = document.createElement('option');
        option.value = art.wert;
        option.textContent = art.anzeigename;
        option.dataset.hatUnterteilung = art.hat_unterteilung;
        examModeSelect.appendChild(option);
    });

    // Close-Button Events
    modal.querySelector('#close-exam-modal').addEventListener('click', closeExamModal);
    modal.querySelector('#exam-cancel-btn').addEventListener('click', closeExamModal);

    // Submit-Button Event
    modal.querySelector('#exam-submit-btn').addEventListener('click', function() {
        submitExamRegistration(modulbuchungId, semester);
    });

    // Zum DOM hinzufuegen
    document.body.appendChild(modal);

    // Event-Listener fuer Pruefungsart-Wechsel (nach dem Einfuegen ins DOM)
    setTimeout(function() {
        var examModeSelectDOM = document.getElementById('exam-mode');
        var klausurTypGruppe = document.getElementById('klausur-typ-gruppe');
        var klausurTypSelect = document.getElementById('klausur-typ');

        examModeSelectDOM.addEventListener('change', function() {
            var selectedArt = erlaubteArten.find(function(art) {
                return art.wert === examModeSelectDOM.value;
            });

            if (selectedArt && selectedArt.hat_unterteilung) {
                klausurTypGruppe.style.display = 'block';
                klausurTypSelect.required = true;
            } else {
                klausurTypGruppe.style.display = 'none';
                klausurTypSelect.required = false;
                klausurTypSelect.value = '';
            }
        });

        // Animation starten
        document.querySelector('.exam-modal').classList.add('show');
    }, 10);
}

function closeExamModal() {
    const modal = document.querySelector('.exam-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
}

async function submitExamRegistration(modulbuchungId, semester) {
    var examDate = document.getElementById('exam-date').value;
    var examMode = document.getElementById('exam-mode').value;
    var klausurTyp = document.getElementById('klausur-typ').value;

    console.log('=== PRUEFUNGSANMELDUNG DEBUG ===');
    console.log('modulbuchungId:', modulbuchungId);
    console.log('examDate:', examDate);
    console.log('examMode:', examMode);
    console.log('klausurTyp:', klausurTyp);

    // Validierung
    if (!examDate || !examMode) {
        showNotification('Bitte alle Felder ausfuellen', 'error');
        return;
    }

    var selectedArt = document.getElementById('exam-mode');
    var hatUnterteilung = selectedArt.selectedOptions[0] &&
                          selectedArt.selectedOptions[0].dataset.hatUnterteilung === 'true';

    if (hatUnterteilung && !klausurTyp) {
        showNotification('Bitte Klausur-Art waehlen (Online oder Praesenz)', 'error');
        return;
    }

    var finalMode = examMode;
    if (hatUnterteilung && klausurTyp) {
        finalMode = klausurTyp;
    }

    var payload = {
        modulbuchung_id: parseInt(modulbuchungId),
        pruefungsdatum: examDate,
        anmeldemodus: finalMode
    };

    console.log('Payload:', JSON.stringify(payload));

    try {
        var response = await fetch('/api/register-exam', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        console.log('Response Status:', response.status);

        var data = await response.json();
        console.log('Response Data:', data);

        if (data.success) {
            showNotification('Pruefung erfolgreich angemeldet!', 'success');
            closeExamModal();
            closeSemesterModal();
            setTimeout(function() { showSemesterModal(semester); }, 400);
        } else {
            showNotification('Fehler: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Fehler bei Pruefungsanmeldung:', error);
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