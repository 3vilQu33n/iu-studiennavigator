# app.py
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_mailman import Mail, EmailMessage
from dotenv import load_dotenv
import logging
import sqlite3
from pathlib import Path
import os

# .env Datei laden (vor os.getenv Aufrufen)
load_dotenv()

from controllers import AuthController, DashboardController, SemesterController
from repositories import PruefungsterminRepository, PruefungsanmeldungRepository, ModulbuchungRepository
from utils.login import User
from models import Pruefungsanmeldung

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Flask-Mail Konfiguration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))

mail = Mail(app)

# Datenbank-Pfad (unterstuetzt Docker-Volume)
DB_PATH = Path(os.getenv('DATABASE_PATH', Path(__file__).parent / 'dashboard.db'))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None

auth_ctrl = AuthController(str(DB_PATH))
dashboard_ctrl = DashboardController(str(DB_PATH))
semester_ctrl = SemesterController(str(DB_PATH))

pruefungstermin_repo = PruefungsterminRepository(str(DB_PATH))
pruefungsanmeldung_repo = PruefungsanmeldungRepository(str(DB_PATH))
modulbuchung_repo = ModulbuchungRepository(str(DB_PATH))


@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id), str(DB_PATH))


# ============================================================================
# HEALTH CHECK ENDPOINT (fuer Docker/Monitoring)
# ============================================================================

@app.route('/health')
def health():
    """
    Health-Check Endpoint fuer Docker/Kubernetes/Monitoring

    Prueft:
    - App laeuft
    - Datenbank erreichbar

    Returns:
        JSON mit Status und HTTP 200 (gesund) oder 503 (Problem)
    """
    try:
        # Pruefe Datenbankverbindung
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("SELECT 1")

        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email') or request.form.get('username')
        password = request.form.get('password')

        if not email or not password:
            flash('Bitte E-Mail und Passwort eingeben', 'error')
            return render_template('login.html')

        result = auth_ctrl.login(email, password)

        if result['success']:
            user = User.get(result['user_id'], str(DB_PATH))
            if not user:
                flash('Fehler beim Laden der User-Daten', 'error')
                return render_template('login.html')

            if result.get('must_change_password'):
                login_user(user, remember=False)
                flash('Bitte aendere dein Passwort', 'warning')
                return redirect(url_for('change_password'))

            login_user(user, remember=True)
            flash('Login erfolgreich!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result.get('error', 'Login fehlgeschlagen'), 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Erfolgreich abgemeldet', 'success')
    return redirect(url_for('login'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'GET':
        return render_template('change_password.html')

    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not all([old_password, new_password, confirm_password]):
        flash('Bitte alle Felder ausfuellen', 'error')
        return render_template('change_password.html')

    if new_password != confirm_password:
        flash('Neue Passwoerter stimmen nicht ueberein', 'error')
        return render_template('change_password.html')

    result = auth_ctrl.change_password(
        user_id=current_user.id,
        old_password=old_password,
        new_password=new_password
    )

    if result['success']:
        flash('Passwort erfolgreich geaendert!', 'success')
        return redirect(url_for('dashboard'))

    flash(result.get('error', 'Fehler beim Aendern des Passworts'), 'error')
    return render_template('change_password.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')

    email = request.form.get('email', '').strip().lower()

    if not email:
        flash('Bitte E-Mail-Adresse eingeben', 'error')
        return render_template('forgot_password.html')

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            user = conn.execute(
                'SELECT id FROM login WHERE LOWER(email) = ?', (email,)
            ).fetchone()

        if user:
            import secrets
            from datetime import datetime, timedelta

            reset_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            session['reset_email'] = email
            session['reset_code'] = reset_code
            session['reset_expires'] = (datetime.now() + timedelta(minutes=15)).isoformat()

            logger.info(f"Reset-Code fuer {email}: {reset_code}")

            try:
                msg = EmailMessage(
                    subject='Dein Passwort-Reset-Code',
                    body=f'''Hallo,

            du hast einen Passwort-Reset angefordert.

            Dein Reset-Code: {reset_code}

            Dieser Code ist 15 Minuten gueltig.

            Falls du diese Anfrage nicht gestellt hast, ignoriere diese E-Mail.

            Viele Gruesse
            Dein Studiennavigator-Team''',
                    to=[email]
                )
                msg.send()
                flash('Ein Reset-Code wurde an deine E-Mail-Adresse gesendet.', 'success')
            except Exception as e:
                logger.warning(f"E-Mail konnte nicht versendet werden: {e}")
                flash('Reset-Code generiert. Pruefe das Terminal!', 'success')
        else:
            flash('Falls die E-Mail registriert ist, wurde ein Reset-Code generiert.', 'info')

        return redirect(url_for('reset_password'))

    except Exception as e:
        logger.error(f"Fehler bei forgot_password: {e}")
        flash('Ein Fehler ist aufgetreten', 'error')
        return render_template('forgot_password.html')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        flash('Keine aktive Reset-Anfrage.', 'error')
        return redirect(url_for('forgot_password'))

    try:
        from datetime import datetime
        expires = datetime.fromisoformat(session['reset_expires'])
        if datetime.now() > expires:
            session.pop('reset_email', None)
            session.pop('reset_code', None)
            session.pop('reset_expires', None)
            flash('Reset-Code abgelaufen.', 'error')
            return redirect(url_for('forgot_password'))
    except (KeyError, ValueError):
        flash('Ungueltige Session.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'GET':
        return render_template('reset_password.html', email=session.get('reset_email'))

    code = request.form.get('code', '').strip()
    new_password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if code != session.get('reset_code'):
        flash('Ungueltiger Code.', 'error')
        return render_template('reset_password.html', email=session.get('reset_email'))

    if not new_password or new_password != confirm_password:
        flash('Passwoerter stimmen nicht ueberein.', 'error')
        return render_template('reset_password.html', email=session.get('reset_email'))

    from utils.login import password_meets_policy
    valid, msg = password_meets_policy(new_password)
    if not valid:
        flash(msg, 'error')
        return render_template('reset_password.html', email=session.get('reset_email'))

    try:
        result = auth_ctrl.reset_password(
            email=session['reset_email'],
            new_password=new_password
        )

        session.pop('reset_email', None)
        session.pop('reset_code', None)
        session.pop('reset_expires', None)

        if result['success']:
            flash('Passwort erfolgreich zurueckgesetzt!', 'success')
            return redirect(url_for('login'))
        else:
            flash(result.get('error', 'Fehler beim Zuruecksetzen'), 'error')
            return redirect(url_for('forgot_password'))

    except Exception as e:
        logger.error(f"Fehler bei reset_password: {e}")
        flash('Ein Fehler ist aufgetreten', 'error')
        return redirect(url_for('forgot_password'))


# --- Dashboard Routes ---

@app.route('/')
@login_required
def dashboard():
    try:
        data = dashboard_ctrl.get_dashboard_data(current_user.id)
        if 'error' in data:
            flash(f"Fehler beim Laden: {data['error']}", 'error')
        return render_template('index.html', **data)
    except Exception as e:
        logger.exception(f"Fehler im Dashboard: {e}")
        flash('Fehler beim Laden des Dashboards', 'error')
        return redirect(url_for('login'))


# --- Semester API Routes ---

@app.route('/api/semester/<int:semester>/modules', methods=['GET'])
@login_required
def api_get_semester_modules(semester):
    """Liefert alle Module eines Semesters mit Buchungsstatus"""
    try:
        result = semester_ctrl.get_modules_for_semester(
            login_id=current_user.id,
            semester_nr=semester
        )

        if result['success']:
            for modul in result['modules']:
                modul['kann_pruefung_anmelden'] = (
                        modul.get('status') == 'gebucht' and
                        modul.get('modulbuchung_id') is not None and
                        not modul.get('pruefungsdatum')
                )
                modul['pruefung_angemeldet'] = modul.get('pruefungsdatum') is not None

                if modul['pruefung_angemeldet']:
                    modul['pruefung_info'] = {
                        'datum': modul.get('pruefungsdatum'),
                        'art': modul.get('anmeldemodus', 'unbekannt')
                    }

                if modul['kann_pruefung_anmelden']:
                    modul['erlaubte_pruefungsarten'] = _get_erlaubte_pruefungsarten(modul['modul_id'])

        return jsonify(result)

    except Exception as e:
        logger.exception(f"Fehler beim Laden der Module fuer Semester {semester}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _get_erlaubte_pruefungsarten(modul_id):
    """Laedt erlaubte Pruefungsarten fuer ein Modul"""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            result = conn.execute("""
                                  SELECT pa.kuerzel as wert, pa.anzeigename, pa.hat_unterteilung
                                  FROM modul_pruefungsart mp
                                           JOIN pruefungsart pa ON pa.id = mp.pruefungsart_id
                                  WHERE mp.modul_id = ?
                                  ORDER BY mp.reihenfolge, pa.name
                                  """, (modul_id,)).fetchall()

            if result:
                return [dict(row) for row in result]

            return [
                {'wert': 'K', 'anzeigename': 'Klausur', 'hat_unterteilung': True},
                {'wert': 'PO', 'anzeigename': 'Portfolio', 'hat_unterteilung': False}
            ]
    except Exception:
        return [{'wert': 'K', 'anzeigename': 'Klausur', 'hat_unterteilung': True}]


@app.route('/semester/<int:semester_nr>', methods=['GET'])
@login_required
def get_semester_modules_legacy(semester_nr):
    """Legacy-Route fuer Semester-Module"""
    try:
        result = semester_ctrl.get_modules_for_semester(
            login_id=current_user.id,
            semester_nr=semester_nr
        )
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Fehler beim Laden von Semester {semester_nr}")
        return jsonify({'success': False, 'error': 'Serverfehler'}), 500


@app.route('/semester/<int:semester_nr>/book/<int:modul_id>', methods=['POST'])
@login_required
def book_module(semester_nr, modul_id):
    """Bucht ein Modul"""
    try:
        result = semester_ctrl.book_module(login_id=current_user.id, modul_id=modul_id)
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Fehler beim Buchen von Modul {modul_id}")
        return jsonify({'success': False, 'error': 'Serverfehler'}), 500


@app.route('/api/book-module', methods=['POST'])
@login_required
def api_book_module():
    """Bucht ein Modul (JSON-basiert)"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Keine Daten empfangen'}), 400

        modul_id = data.get('modul_id')
        if not modul_id:
            return jsonify({'success': False, 'error': 'Modul-ID fehlt'}), 400

        result = semester_ctrl.book_module(login_id=current_user.id, modul_id=modul_id)
        return jsonify(result)

    except Exception as e:
        logger.exception("Fehler beim Buchen")
        return jsonify({'success': False, 'error': 'Serverfehler'}), 500


# --- Pruefungstermine API Routes ---

@app.route('/api/pruefungstermine/<int:modul_id>', methods=['GET'])
@login_required
def get_pruefungstermine(modul_id):
    """Liefert verfuegbare Pruefungstermine fuer ein Modul"""
    try:
        termine = pruefungstermin_repo.find_verfuegbare_termine(modul_id)
        return jsonify({'success': True, 'termine': [t.to_dict() for t in termine]})
    except Exception as e:
        logger.exception("Fehler beim Laden der Pruefungstermine")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pruefung-anmelden', methods=['POST'])
@login_required
def pruefung_anmelden():
    """Meldet Student zu einem Pruefungstermin an"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Keine Daten empfangen'}), 400

        modulbuchung_id = data.get('modulbuchung_id')
        pruefungstermin_id = data.get('pruefungstermin_id')

        if not all([modulbuchung_id, pruefungstermin_id]):
            return jsonify({'success': False, 'error': 'Modulbuchung-ID und Pruefungstermin-ID erforderlich'}), 400

        if pruefungsanmeldung_repo.hat_aktive_anmeldung(modulbuchung_id):
            return jsonify({'success': False, 'error': 'Bereits angemeldet'})

        termin = pruefungstermin_repo.find_by_id(pruefungstermin_id)
        if not termin:
            return jsonify({'success': False, 'error': 'Pruefungstermin nicht gefunden'}), 404

        if termin.ist_anmeldeschluss_vorbei():
            return jsonify({'success': False, 'error': 'Anmeldeschluss vorbei'})

        if termin.hat_kapazitaet():
            anzahl = pruefungsanmeldung_repo.anzahl_anmeldungen_fuer_termin(pruefungstermin_id)
            if anzahl >= termin.kapazitaet:
                return jsonify({'success': False, 'error': 'Termin ausgebucht'})

        anmeldung = Pruefungsanmeldung(
            id=0,
            modulbuchung_id=modulbuchung_id,
            pruefungstermin_id=pruefungstermin_id,
            status='angemeldet'
        )
        anmeldung_id = pruefungsanmeldung_repo.create(anmeldung)

        return jsonify({'success': True, 'message': 'Pruefung angemeldet', 'anmeldung_id': anmeldung_id})

    except Exception as e:
        logger.exception("Fehler bei Pruefungsanmeldung")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pruefung-stornieren/<int:anmeldung_id>', methods=['POST'])
@login_required
def pruefung_stornieren(anmeldung_id):
    """Storniert eine Pruefungsanmeldung"""
    try:
        anmeldung = pruefungsanmeldung_repo.find_by_id(anmeldung_id)
        if not anmeldung:
            return jsonify({'success': False, 'error': 'Nicht gefunden'}), 404

        if not anmeldung.kann_storniert_werden():
            return jsonify({'success': False, 'error': 'Kann nicht storniert werden'})

        pruefungsanmeldung_repo.stornieren(anmeldung_id)
        return jsonify({'success': True, 'message': 'Storniert'})

    except Exception as e:
        logger.exception("Fehler beim Stornieren")
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Error Handlers ---

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    logger.exception("Interner Serverfehler")
    return render_template('500.html'), 500


if __name__ == '__main__':
    if not DB_PATH.exists():
        logger.error(f"Datenbank nicht gefunden: {DB_PATH}")
    else:
        logger.info("Dashboard: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)