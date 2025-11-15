'use strict';

// State
const positions = {};
let currentSemester = 1;
const MAX_SEMESTER = 7;

// DOM Elements
let container, img, marker, positionsDiv, currentSemSpan, copyBtn, resetBtn;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    try {
        container = document.getElementById('container');
        img = document.getElementById('svg-image');
        marker = document.getElementById('marker');
        positionsDiv = document.getElementById('positions');
        currentSemSpan = document.getElementById('current-sem');
        copyBtn = document.getElementById('copy-btn');
        resetBtn = document.getElementById('reset-btn');

        if (!container || !img || !marker || !positionsDiv || !currentSemSpan) {
            console.error('Fehlende DOM-Elemente');
            return;
        }

        // Event Listeners
        img.addEventListener('click', handleImageClick);
        copyBtn.addEventListener('click', copyToClipboard);
        resetBtn.addEventListener('click', reset);

        console.log('Position Picker initialisiert');
    } catch (err) {
        console.error('Fehler bei Initialisierung:', err);
    }
});

// Handlers
function handleImageClick(e) {
    try {
        const rect = img.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const x_percent = (x / rect.width).toFixed(3);
        const y_percent = (y / rect.height).toFixed(3);

        // Marker anzeigen
        marker.style.left = (e.clientX - container.getBoundingClientRect().left) + 'px';
        marker.style.top = (e.clientY - container.getBoundingClientRect().top) + 'px';
        marker.style.display = 'block';

        // Position speichern
        positions[currentSemester] = { x_percent, y_percent };

        updateDisplay();

        // Nächstes Semester
        if (currentSemester < MAX_SEMESTER) {
            currentSemester++;
            currentSemSpan.textContent = currentSemester === 7 ? 'Bachelor' : `Semester ${currentSemester}`;
        } else {
            currentSemSpan.textContent = '✅ Fertig!';
        }
    } catch (err) {
        console.error('Fehler bei Klick:', err);
    }
}

function updateDisplay() {
    positionsDiv.innerHTML = '';

    for (let sem = 1; sem <= MAX_SEMESTER; sem++) {
        if (positions[sem]) {
            const semName = sem === 7 ? 'Bachelor' : `Sem ${sem}`;
            const div = document.createElement('div');
            div.className = 'position-entry';
            div.textContent = `${semName}: x=${positions[sem].x_percent}, y=${positions[sem].y_percent}`;
            positionsDiv.appendChild(div);
        }
    }
}

function copyToClipboard() {
    try {
        let code = 'SEMESTER_POSITIONS = {\n';

        for (let sem = 1; sem <= MAX_SEMESTER; sem++) {
            if (positions[sem]) {
                const pos = positions[sem];
                code += `    ${sem}: {"x_percent": ${pos.x_percent}, "y_percent": ${pos.y_percent}, "angle": 0, "flip": False},\n`;
            }
        }

        code += '}';

        navigator.clipboard.writeText(code).then(() => {
            alert('✅ Python-Code in Zwischenablage kopiert!');
        }).catch(err => {
            console.error('Clipboard-Fehler:', err);
            // Fallback: Textfeld anzeigen
            const textarea = document.createElement('textarea');
            textarea.value = code;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            alert('✅ Code kopiert (Fallback-Methode)');
        });
    } catch (err) {
        console.error('Fehler beim Kopieren:', err);
        alert('❌ Fehler beim Kopieren');
    }
}

function reset() {
    Object.keys(positions).forEach(key => delete positions[key]);
    currentSemester = 1;
    currentSemSpan.textContent = 'Semester 1';
    marker.style.display = 'none';
    updateDisplay();
}