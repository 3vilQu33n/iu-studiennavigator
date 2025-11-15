# tests/unit/test_dashboard_controller.py
"""
Unit Tests fÃ¼r DashboardController

Testet die Dashboard-Logik mit gemockten Repositories.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime
from decimal import Decimal
from controllers.dashboard_controller import DashboardController
from models.student import Student
from models.einschreibung import Einschreibung
from models.progress import Progress


@pytest.fixture
def mock_db_path(tmp_path):
    """TemporÃ¤rer DB-Pfad"""
    return str(tmp_path / "test.db")


@pytest.fixture
def controller(mock_db_path):
    """DashboardController Instanz mit gemockten Dependencies"""
    with patch('controllers.dashboard_controller.StudentRepository'), \
            patch('controllers.dashboard_controller.EinschreibungRepository'), \
            patch('controllers.dashboard_controller.ProgressRepository'), \
            patch('controllers.dashboard_controller.ProgressTextService'):
        return DashboardController(mock_db_path)


@pytest.fixture
def sample_student():
    """Test-Student"""
    return Student(
        id=1,
        matrikel_nr="IU12345678",
        vorname="Max",
        nachname="Mustermann",
        login_id=1
    )


@pytest.fixture
def sample_einschreibung():
    """Test-Einschreibung"""
    return Einschreibung(
        id=1,
        student_id=1,
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date(2024, 3, 1),
        status='aktiv'
    )


@pytest.fixture
def sample_progress():
    """Test-Progress"""
    return Progress(
        student_id=1,
        durchschnittsnote=Decimal('2.0'),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal('199.00'),
        aktuelles_semester=2.5,
        erwartetes_semester=2.3
    )


# ========== Initialization Tests ==========

def test_controller_initialization(mock_db_path):
    """Test: Controller wird korrekt initialisiert"""
    with patch('controllers.dashboard_controller.StudentRepository'), \
            patch('controllers.dashboard_controller.EinschreibungRepository'), \
            patch('controllers.dashboard_controller.ProgressRepository'), \
            patch('controllers.dashboard_controller.ProgressTextService'):
        controller = DashboardController(mock_db_path)

        assert controller.db_path == mock_db_path
        assert hasattr(controller, 'SEMESTER_POSITIONS')
        assert len(controller.SEMESTER_POSITIONS) == 7


def test_semester_positions_defined(controller):
    """Test: Semester-Positionen sind definiert"""
    assert 1 in controller.SEMESTER_POSITIONS
    assert 7 in controller.SEMESTER_POSITIONS

    for pos in controller.SEMESTER_POSITIONS.values():
        assert 'x_percent' in pos
        assert 'y_percent' in pos
        assert 'angle' in pos
        assert 'flip' in pos


# ========== get_student_by_auth_user Tests ==========

def test_get_student_by_auth_user_success(controller, sample_student):
    """Test: Student wird korrekt geladen"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)

    result = controller.get_student_by_auth_user(1)

    assert result is not None
    assert result['id'] == 1
    assert result['vorname'] == 'Max'
    assert result['nachname'] == 'Mustermann'


def test_get_student_by_auth_user_not_found(controller):
    """Test: Nicht existierender Student gibt None zurÃ¼ck"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=None)

    result = controller.get_student_by_auth_user(999)

    assert result is None


def test_get_student_by_auth_user_exception_handling(controller):
    """Test: Exception wird abgefangen und None zurÃ¼ckgegeben"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(
        side_effect=Exception("DB Error")
    )

    result = controller.get_student_by_auth_user(1)

    assert result is None


# ========== get_car_position_for_semester Tests ==========

def test_get_car_position_semester_1(controller):
    """Test: Auto-Position fÃ¼r Semester 1"""
    pos = controller.get_car_position_for_semester(1.0)

    assert 'x_percent' in pos
    assert 'y_percent' in pos
    assert 'rotation' in pos
    assert 'flip' in pos
    assert pos['x_percent'] == controller.SEMESTER_POSITIONS[1]['x_percent']


def test_get_car_position_semester_7(controller):
    """Test: Auto-Position fÃ¼r Semester 7"""
    pos = controller.get_car_position_for_semester(7.0)

    assert pos['x_percent'] == controller.SEMESTER_POSITIONS[7]['x_percent']
    assert pos['y_percent'] == controller.SEMESTER_POSITIONS[7]['y_percent']


def test_get_car_position_intermediate(controller):
    """Test: Auto-Position zwischen zwei Semestern wird interpoliert"""
    pos = controller.get_car_position_for_semester(2.5)

    # Position sollte zwischen Semester 2 und 3 liegen
    pos2 = controller.SEMESTER_POSITIONS[2]
    pos3 = controller.SEMESTER_POSITIONS[3]

    # X sollte zwischen den beiden Werten liegen
    assert min(pos2['x_percent'], pos3['x_percent']) <= pos['x_percent'] <= max(pos2['x_percent'], pos3['x_percent'])


def test_get_car_position_boundaries(controller):
    """Test: Position bleibt in gÃ¼ltigen Grenzen"""
    for semester in [0.5, 1.0, 3.5, 7.0, 7.5]:
        pos = controller.get_car_position_for_semester(semester)

        assert 0 <= pos['x_percent'] <= 1
        assert 0 <= pos['y_percent'] <= 1
        assert isinstance(pos['flip'], bool)


# ========== get_dashboard_data Tests ==========

def test_get_dashboard_data_complete(controller, sample_student, sample_einschreibung, sample_progress):
    """Test: VollstÃ¤ndige Dashboard-Daten"""
    # Mock Repositories
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)
    controller._DashboardController__progress_repo.get_progress_for_student = Mock(return_value=sample_progress)

    # Mock ProgressTextService
    mock_texts = {
        'grade': 'Note: 2.0',
        'time': 'Im Zeitplan',
        'fee': '199.00 â‚¬ offen',
        'category': 'fast'
    }
    controller._DashboardController__progress_text_service.get_all_texts = Mock(return_value=mock_texts)

    # Mock SQLite fÃ¼r zeitmodell
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (36,)  # 36 Monate = 6 Semester
        mock_connect.return_value = mock_conn

        result = controller.get_dashboard_data(1)

    # Assertions
    assert result['student_name'] == 'Max Mustermann'
    assert result['student_id'] == 1
    assert result['current_semester'] > 0
    assert 'car_x_percent' in result
    assert 'car_y_percent' in result
    assert 'progress_grade' in result
    assert 'progress_time' in result
    assert 'progress_fee' in result


def test_get_dashboard_data_no_student(controller):
    """Test: Dashboard-Daten wenn Student nicht gefunden"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=None)

    result = controller.get_dashboard_data(999)

    # Sollte Fallback-Daten enthalten
    assert result['student_name'] == 'Unbekannt'
    assert result['student_id'] is None
    assert 'error' in result


def test_get_dashboard_data_no_einschreibung(controller, sample_student):
    """Test: Dashboard-Daten ohne aktive Einschreibung"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(
        side_effect=ValueError("Keine aktive Einschreibung")
    )

    # Mock SQLite
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_connect.return_value = mock_conn

        result = controller.get_dashboard_data(1)

    # Sollte Fallback-Progress-Texte haben
    assert result['progress_grade'] == 'Noch keine Noten'
    assert result['progress_time'] == 'Gerade gestartet'
    assert result['progress_fee'] == 'Keine Gebühren'


def test_get_dashboard_data_time_status_ahead(controller, sample_student, sample_einschreibung):
    """Test: time_status ist 'ahead' wenn weit voraus"""
    progress_ahead = Progress(
        student_id=1,
        durchschnittsnote=Decimal('2.0'),
        anzahl_bestandene_module=20,
        anzahl_gebuchte_module=22,
        offene_gebuehren=Decimal('0'),
        aktuelles_semester=2.0,  # ✅ Korrigiert: Student ist in Sem 2
        erwartetes_semester=3.0  # ✅ Sollte in Sem 3 sein → 1 Sem voraus = +180 Tage
    )

    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)
    controller._DashboardController__progress_repo.get_progress_for_student = Mock(return_value=progress_ahead)

    mock_texts = {'grade': 'Test', 'time': 'Test', 'fee': 'Test', 'category': 'fast'}
    controller._DashboardController__progress_text_service.get_all_texts = Mock(return_value=mock_texts)

    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (36,)
        mock_connect.return_value = mock_conn

        result = controller.get_dashboard_data(1)

    # Bei 180 Tagen voraus sollte time_status 'ahead' sein
    assert result['time_status'] == 'ahead'


def test_get_dashboard_data_time_status_minus(controller, sample_student, sample_einschreibung):
    """Test: time_status ist 'minus' wenn im Verzug"""
    progress_behind = Progress(
        student_id=1,
        durchschnittsnote=Decimal('2.0'),
        anzahl_bestandene_module=5,
        anzahl_gebuchte_module=7,
        offene_gebuehren=Decimal('0'),
        aktuelles_semester=4.0,  # ✅ Korrigiert: Student ist in Sem 4
        erwartetes_semester=3.0  # ✅ Sollte in Sem 3 sein → 1 Sem Verzug = -180 Tage
    )

    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)
    controller._DashboardController__progress_repo.get_progress_for_student = Mock(return_value=progress_behind)

    mock_texts = {'grade': 'Test', 'time': 'Test', 'fee': 'Test', 'category': 'slow'}
    controller._DashboardController__progress_text_service.get_all_texts = Mock(return_value=mock_texts)

    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (36,)
        mock_connect.return_value = mock_conn

        result = controller.get_dashboard_data(1)

    assert result['time_status'] == 'minus'


def test_get_dashboard_data_includes_next_exam(controller, sample_student, sample_einschreibung, sample_progress):
    """Test: Dashboard-Daten enthalten nÃ¤chste PrÃ¼fung"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)
    controller._DashboardController__progress_repo.get_progress_for_student = Mock(return_value=sample_progress)

    mock_texts = {'grade': 'Test', 'time': 'Test', 'fee': 'Test', 'category': 'medium'}
    controller._DashboardController__progress_text_service.get_all_texts = Mock(return_value=mock_texts)

    mock_exam = {
        'modul_name': 'Mathematik I',
        'datum': '2024-06-15',
        'tage_bis_pruefung': 30,
        'anmeldemodus': 'Automatisch'
    }

    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (36,)
        mock_connect.return_value = mock_conn

        with patch.object(controller, 'get_next_exam', return_value=mock_exam):
            result = controller.get_dashboard_data(1)

    assert 'next_exam' in result
    assert result['next_exam'] == mock_exam


# ========== get_next_exam Tests ==========

def test_get_next_exam_found(controller, sample_student, sample_einschreibung):
    """Test: NÃ¤chste PrÃ¼fung wird gefunden"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    # Mock DB result
    mock_row = {
        'modul_name': 'Mathematik I',
        'pruefungsdatum': '2024-06-15',
        'anmeldemodus': 'Automatisch'
    }

    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = mock_row
        mock_connect.return_value = mock_conn

        result = controller.get_next_exam(1)

    assert result is not None
    assert result['modul_name'] == 'Mathematik I'
    assert result['datum'] == '2024-06-15'
    assert 'tage_bis_pruefung' in result


def test_get_next_exam_not_found(controller, sample_student, sample_einschreibung):
    """Test: Keine PrÃ¼fung gefunden gibt None zurÃ¼ck"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_connect.return_value = mock_conn

        result = controller.get_next_exam(1)

    assert result is None


def test_get_next_exam_no_student(controller):
    """Test: Keine PrÃ¼fung wenn Student nicht existiert"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=None)

    result = controller.get_next_exam(999)

    assert result is None


def test_get_next_exam_no_einschreibung(controller, sample_student):
    """Test: Keine PrÃ¼fung wenn keine aktive Einschreibung"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(
        side_effect=ValueError("Keine Einschreibung")
    )

    result = controller.get_next_exam(1)

    assert result is None


def test_get_next_exam_exception_handling(controller):
    """Test: Exception beim Laden der PrÃ¼fung wird abgefangen"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(
        side_effect=Exception("DB Error")
    )

    result = controller.get_next_exam(1)

    assert result is None


# ========== Integration/Edge Case Tests ==========

def test_dashboard_data_structure_complete(controller, sample_student, sample_einschreibung, sample_progress):
    """Test: Dashboard-Daten enthalten alle erforderlichen Felder"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)
    controller._DashboardController__progress_repo.get_progress_for_student = Mock(return_value=sample_progress)

    mock_texts = {'grade': 'Test', 'time': 'Test', 'fee': 'Test', 'category': 'medium'}
    controller._DashboardController__progress_text_service.get_all_texts = Mock(return_value=mock_texts)

    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (36,)
        mock_connect.return_value = mock_conn

        result = controller.get_dashboard_data(1)

    # PrÃ¼fe alle erforderlichen Felder
    required_fields = [
        'student_name', 'student_id', 'current_semester', 'max_semester',
        'car_x_percent', 'car_y_percent', 'car_rotation', 'car_flip',
        'progress_grade', 'progress_time', 'progress_fee', 'grade_category',
        'time_status', 'next_exam', 'image_svg', 'original_image'
    ]

    for field in required_fields:
        assert field in result, f"Feld '{field}' fehlt in Dashboard-Daten"


def test_car_position_interpolation_accuracy(controller):
    """Test: Auto-Position wird korrekt interpoliert"""
    # Test Semester 1.5 (Mitte zwischen 1 und 2)
    pos = controller.get_car_position_for_semester(1.5)
    pos1 = controller.SEMESTER_POSITIONS[1]
    pos2 = controller.SEMESTER_POSITIONS[2]

    # Sollte exakt in der Mitte sein
    expected_x = (pos1['x_percent'] + pos2['x_percent']) / 2
    expected_y = (pos1['y_percent'] + pos2['y_percent']) / 2

    assert abs(pos['x_percent'] - expected_x) < 0.001
    assert abs(pos['y_percent'] - expected_y) < 0.001


def test_max_semester_calculation(controller, sample_student, sample_einschreibung, sample_progress):
    """Test: max_semester wird korrekt aus Zeitmodell berechnet"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._DashboardController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)
    controller._DashboardController__progress_repo.get_progress_for_student = Mock(return_value=sample_progress)

    mock_texts = {'grade': 'Test', 'time': 'Test', 'fee': 'Test', 'category': 'medium'}
    controller._DashboardController__progress_text_service.get_all_texts = Mock(return_value=mock_texts)

    # Test mit 48 Monaten = 8 Semester
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (48,)
        mock_connect.return_value = mock_conn

        result = controller.get_dashboard_data(1)

    # 48 Monate / 6 Monate pro Semester + 1 = 9
    assert result['max_semester'] == 9


def test_fallback_data_on_exception(controller):
    """Test: Fallback-Daten bei Exception"""
    controller._DashboardController__student_repo.get_by_login_id = Mock(
        side_effect=Exception("Critical Error")
    )

    result = controller.get_dashboard_data(1)

    # Sollte Fallback-Daten zurÃ¼ckgeben
    assert result['student_name'] == 'Unbekannt'
    assert result['progress_grade'] == 'Keine Daten'
    assert 'error' in result