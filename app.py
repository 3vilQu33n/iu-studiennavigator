# app.py
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
import logging
import sqlite3
from pathlib import Path

# Controllers
from controllers import AuthController
from controllers import DashboardController
from controllers import SemesterController

# Repositories
from repositories import PruefungsterminRepository
from repositories import PruefungsanmeldungRepository
from repositories import ModulbuchungRepository

# Models
from utils.login import User
from models import Pruefungsanmeldung

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Flask App Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Datenbank-Pfad
DB_PATH = Path(__file__).parent / 'dashboard.db'

# Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None

# Controller initialisieren
auth_ctrl = AuthController(str(DB_PATH))
dashboard_ctrl = DashboardController(str(DB_PATH))
semester_ctrl = SemesterController(str(DB_PATH))

# Repositories initialisieren
pruefungstermin_repo = PruefungsterminRepository(str(DB_PATH))
pruefungsanmeldung_repo = PruefungsanmeldungRepository(str(DB_PATH))
modulbuchung_repo = ModulbuchungRepository(str(DB_PATH))


# ============================================================================
# LOGIN MANAGER USER LOADER
# ============================================================================

@login_manager.user_loader
def load_user(user_id):
    """Laedt User fuer Flask-Login"""
    return User.get(int(user_id), str(DB_PATH))


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
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
            if result.get('must_change_password'):
                user = User.get(result['user_id'], str(DB_PATH))
                if user:
                    login_user(user, remember=False)
                    flash('Bitte aendere dein Passwort', 'warning')
                    return redirect(url_for('change_password'))
                else:
                    flash('Fehler beim Laden der User-Daten', 'error')
            else:
                user = User.get(result['user_id'], str(DB_PATH))
                if user:
                    login_user(user, remember=True)
                    flash('Login erfolgreich!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Fehler beim Laden der User-Daten', 'error')
        else:
            flash(result.get('error', 'Login fehlgeschlagen'), 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('Erfolgreich abgemeldet', 'success')
    return redirect(url_for('login'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Passwort aendern (fuer eingeloggte User)"""
    if request.method == 'GET':
        return render_template('change_password.html')

    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not old_password or not new_password or not confirm_password:
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
    else:
        flash(result.get('error', 'Fehler beim Aendern des Passworts'), 'error')
        return render_template('change_password.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Passwort vergessen - Code anfordern"""
    if request.method == 'GET':
        return render_template('forgot_password.html')

    email = request.form.get('email', '').strip().lower()

    if not email:
        flash('Bitte E-Mail-Adresse eingeben', 'error')
        return render_template('forgot_password.html')

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            user = conn.execute(
                'SELECT id FROM login WHERE LOWER(email) = ?',
                (email,)
            ).fetchone()

        if user:
            import secrets
            from datetime import datetime, timedelta

            reset_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

            session['reset_email'] = email
            session['reset_code'] = reset_code
            session['reset_expires'] = (datetime.now() + timedelta(minutes=15)).isoformat()

            logger.info(f"\n{'=' * 60}")
            logger.info(f"RESET-CODE fuer {email}: {reset_code}")
            logger.info(f"Gueltig bis: {session['reset_expires']}")
            logger.info(f"{'=' * 60}\n")

            flash('Ein Reset-Code wurde generiert. Pruefe das Terminal fuer den Code!', 'success')
        else:
            logger.warning(f"Reset-Versuch fuer nicht existierende E-Mail: {email}")
            flash('Falls die E-Mail registriert ist, wurde ein Reset-Code generiert.', 'info')

        return redirect(url_for('reset_password'))

    except Exception as e:
        logger.error(f"Fehler bei forgot_password: {e}")
        flash('Ein Fehler ist aufgetreten', 'error')
        return render_template('forgot_password.html')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """Passwort zuruecksetzen mit Code"""
    if 'reset_email' not in session:
        flash('Keine aktive Reset-Anfrage. Bitte starte den Prozess erneut.', 'error')
        return redirect(url_for('forgot_password'))

    try:
        from datetime import datetime
        expires = datetime.fromisoformat(session['reset_expires'])
        if datetime.now() > expires:
            session.pop('reset_email', None)
            session.pop('reset_code', None)
            session.pop('reset_expires', None)
            flash('Reset-Code abgelaufen. Bitte fordere einen neuen Code an.', 'error')
            return redirect(url_for('forgot_password'))
    except (KeyError, ValueError) as e:
        logger.warning(f"Session-Fehler: {e}")
        flash('Unguelt ige Session. Bitte starte den Prozess erneut.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'GET':
        return render_template('reset_password.html', email=session.get('reset_email'))

    code = request.form.get('code', '').strip()
    new_password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if code != session.get('reset_code'):
        flash('Ungueltiger Code. Bitte pruefe deine Eingabe.', 'error')
        return render_template('reset_password.html', email=session.get('reset_email'))

    if not new_password or not confirm_password:
        flash('Bitte beide Passwort-Felder ausfuellen', 'error')
        return render_template('reset_password.html', email=session.get('reset_email'))

    if new_password != confirm_password:
        flash('Passwoerter stimmen nicht ueberein', 'error')
        return render_template('reset_password.html', email=session.get('reset_email'))

    if len(new_password) < 8:
        flash('Passwort muss mindestens 8 Zeichen haben', 'error')
        return render_template('reset_password.html', email=session.get('reset_email'))

    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        new_hash = ph.hash(new_password)

        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                """UPDATE login
                   SET password_hash        = ?,
                       must_change_password = 0
                   WHERE LOWER(email) = LOWER(?)""",
                (new_hash, session.get('reset_email'))
            )
            conn.commit()

        email = session.pop('reset_email', None)
        session.pop('reset_code', None)
        session.pop('reset_expires', None)

        logger.info(f"Passwort erfolgreich zurueckgesetzt fuer: {email}")
        flash('Passwort erfolgreich zurueckgesetzt! Du kannst dich jetzt einloggen.', 'success')
        return redirect(url_for('login'))

    except Exception as e:
        logger.exception(f"Fehler beim Zuruecksetzen des Passworts: {e}")
        flash('Fehler beim Zuruecksetzen des Passworts', 'error')
        return render_template('reset_password.html', email=session.get('reset_email'))


# ============================================================================
# DASHBOARD ROUTE
# ============================================================================

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    """Hauptseite - Dashboard"""
    try:
        logger.info(f"Dashboard aufgerufen von: current_user.id={current_user.id}")

        data = dashboard_ctrl.get_dashboard_data(current_user.id)

        if 'error' in data:
            flash(f"Fehler beim Laden: {data['error']}", 'error')

        return render_template('index.html', **data)

    except Exception as e:
        logger.exception(f"Fehler im Dashboard: {e}")
        flash('Fehler beim Laden des Dashboards', 'error')
        return redirect(url_for('login'))


# ============================================================================
# SEMESTER ROUTES
# ============================================================================

@app.route('/semester/<int:semester_nr>', methods=['GET'])
@login_required
def get_semester_modules(semester_nr):
    """API-Endpoint: Holt alle Module fuer ein Semester"""
    try:
        logger.info(f"Lade Module fuer Semester {semester_nr}, User: {current_user.id}")

        result = semester_ctrl.get_modules_for_semester(
            login_id=current_user.id,
            semester_nr=semester_nr
        )

        logger.info(f"Gefundene Module: {len(result.get('modules', []))}")
        return jsonify(result)

    except Exception as e:
        logger.exception(f"Fehler beim Laden von Semester {semester_nr}")
        return jsonify({
            'success': False,
            'error': 'Serverfehler beim Laden der Module'
        }), 500


@app.route('/semester/<int:semester_nr>/book/<int:modul_id>', methods=['POST'])
@login_required
def book_module(semester_nr, modul_id):
    """API-Endpoint: Bucht ein Modul"""
    try:
        logger.info(f"Buche Modul {modul_id} fuer Semester {semester_nr}")

        result = semester_ctrl.book_module(
            login_id=current_user.id,
            modul_id=modul_id
        )

        if result['success']:
            logger.info(f"Modul {modul_id} erfolgreich gebucht")
        else:
            logger.warning(f"Buchung fehlgeschlagen: {result.get('error')}")

        return jsonify(result)

    except Exception as e:
        logger.exception(f"Fehler beim Buchen von Modul {modul_id}")
        return jsonify({
            'success': False,
            'error': 'Serverfehler beim Buchen des Moduls'
        }), 500


@app.route('/api/book-module', methods=['POST'])
@login_required
def api_book_module():
    """API-Endpoint: Bucht ein Modul (JSON-basiert)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Keine Daten empfangen'
            }), 400

        modul_id = data.get('modul_id')
        semester = data.get('semester')

        if not modul_id:
            return jsonify({
                'success': False,
                'error': 'Modul-ID fehlt'
            }), 400

        logger.info(f"API: Buche Modul {modul_id} (Semester {semester}) fuer User {current_user.id}")

        result = semester_ctrl.book_module(
            login_id=current_user.id,
            modul_id=modul_id
        )

        if result['success']:
            logger.info(f"Modul {modul_id} erfolgreich gebucht")
        else:
            logger.warning(f"Buchung fehlgeschlagen: {result.get('error')}")

        return jsonify(result)

    except Exception as e:
        logger.exception(f"Fehler beim Buchen von Modul {modul_id}")
        return jsonify({
            'success': False,
            'error': 'Serverfehler beim Buchen des Moduls'
        }), 500


# ============================================================================
# PRUEFUNGSTERMINE & MODERNE ANMELDUNG
# ============================================================================

@app.route('/api/pruefungstermine/<int:modul_id>', methods=['GET'])
@login_required
def get_pruefungstermine(modul_id: int):
    """API-Endpoint: Liefert verfuegbare Pruefungstermine fuer ein Modul"""
    try:
        logger.info(f"Lade verfuegbare Pruefungstermine fuer Modul {modul_id}")

        termine = pruefungstermin_repo.find_verfuegbare_termine(modul_id)
        termine_dict = [t.to_dict() for t in termine]

        logger.info(f"{len(termine_dict)} verfuegbare Termine gefunden")

        return jsonify({
            'success': True,
            'termine': termine_dict
        })

    except Exception as e:
        logger.exception("Fehler beim Laden der Pruefungstermine")
        return jsonify({
            'success': False,
            'error': f'Fehler beim Laden der Pruefungstermine: {str(e)}'
        }), 500


@app.route('/api/pruefung-anmelden', methods=['POST'])
@login_required
def pruefung_anmelden():
    """API-Endpoint: Meldet Student zu einem Pruefungstermin an"""
    try:
        logger.info("=" * 60)
        logger.info("PRUEFUNGSANMELDUNG - REQUEST EMPFANGEN")

        data = request.get_json()
        logger.info(f"Parsed JSON: {data}")

        if not data:
            logger.error("Keine Daten empfangen")
            return jsonify({
                'success': False,
                'error': 'Keine Daten empfangen'
            }), 400

        modulbuchung_id = data.get('modulbuchung_id')
        pruefungstermin_id = data.get('pruefungstermin_id')

        if not all([modulbuchung_id, pruefungstermin_id]):
            logger.error("Pflichtfelder fehlen!")
            return jsonify({
                'success': False,
                'error': 'Modulbuchung-ID und Pruefungstermin-ID sind erforderlich'
            }), 400

        if pruefungsanmeldung_repo.hat_aktive_anmeldung(modulbuchung_id):
            logger.warning(f"Bereits angemeldet fuer Modulbuchung {modulbuchung_id}")
            return jsonify({
                'success': False,
                'error': 'Fuer diese Modulbuchung existiert bereits eine aktive Pruefungsanmeldung'
            })

        termin = pruefungstermin_repo.find_by_id(pruefungstermin_id)
        if not termin:
            logger.error(f"Pruefungstermin {pruefungstermin_id} nicht gefunden")
            return jsonify({
                'success': False,
                'error': 'Pruefungstermin nicht gefunden'
            }), 404

        if termin.ist_anmeldeschluss_vorbei():
            logger.warning(f"Anmeldeschluss vorbei fuer Termin {pruefungstermin_id}")
            return jsonify({
                'success': False,
                'error': 'Anmeldeschluss fuer diesen Termin ist bereits vorbei'
            })

        if termin.hat_kapazitaet():
            anzahl_anmeldungen = pruefungsanmeldung_repo.anzahl_anmeldungen_fuer_termin(pruefungstermin_id)
            if anzahl_anmeldungen >= termin.kapazitaet:
                logger.warning(f"Kapazitaet erschoepft fuer Termin {pruefungstermin_id}")
                return jsonify({
                    'success': False,
                    'error': 'Dieser Pruefungstermin ist bereits ausgebucht'
                })

        anmeldung = Pruefungsanmeldung(
            id=0,
            modulbuchung_id=modulbuchung_id,
            pruefungstermin_id=pruefungstermin_id,
            status='angemeldet'
        )

        anmeldung_id = pruefungsanmeldung_repo.create(anmeldung)
        logger.info(f"Pruefungsanmeldung erfolgreich erstellt (ID: {anmeldung_id})")
        logger.info("=" * 60)

        return jsonify({
            'success': True,
            'message': 'Pruefung erfolgreich angemeldet',
            'anmeldung_id': anmeldung_id
        })

    except Exception as e:
        logger.exception("Fehler bei Pruefungsanmeldung")
        logger.info("=" * 60)
        return jsonify({
            'success': False,
            'error': f'Serverfehler bei der Pruefungsanmeldung: {str(e)}'
        }), 500


@app.route('/api/pruefung-stornieren/<int:anmeldung_id>', methods=['POST'])
@login_required
def pruefung_stornieren(anmeldung_id: int):
    """API-Endpoint: Storniert eine Pruefungsanmeldung"""
    try:
        logger.info(f"Storniere Pruefungsanmeldung {anmeldung_id}")

        anmeldung = pruefungsanmeldung_repo.find_by_id(anmeldung_id)

        if not anmeldung:
            return jsonify({
                'success': False,
                'error': 'Pruefungsanmeldung nicht gefunden'
            }), 404

        if not anmeldung.kann_storniert_werden():
            return jsonify({
                'success': False,
                'error': 'Diese Anmeldung kann nicht mehr storniert werden'
            })

        pruefungsanmeldung_repo.stornieren(anmeldung_id)

        logger.info(f"Pruefungsanmeldung {anmeldung_id} erfolgreich storniert")

        return jsonify({
            'success': True,
            'message': 'Pruefungsanmeldung erfolgreich storniert'
        })

    except Exception as e:
        logger.exception("Fehler beim Stornieren der Pruefungsanmeldung")
        return jsonify({
            'success': False,
            'error': f'Serverfehler beim Stornieren: {str(e)}'
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """404 - Seite nicht gefunden"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """500 - Interner Serverfehler"""
    logger.exception("Interner Serverfehler")
    return render_template('500.html'), 500


# ============================================================================
# DEVELOPMENT SERVER
# ============================================================================

if __name__ == '__main__':
    if not DB_PATH.exists():
        logger.error(f"Datenbank nicht gefunden: {DB_PATH}")
        logger.info("Bitte fuehre zuerst db_migration.py aus!")
    else:
        logger.info(f"Starte Flask-App mit Datenbank: {DB_PATH}")
        logger.info("Dashboard verfuegbar unter: http://localhost:5000")

        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000
        )