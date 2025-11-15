# tests/unit/test_semester_controller.py
"""
Unit Tests fÃƒÂ¼r SemesterController

Testet die Semester-/Modulbuchungs-Logik mit gemockten Repositories.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
from controllers.semester_controller import SemesterController
from models.student import Student
from models.einschreibung import Einschreibung


@pytest.fixture
def mock_db_path(tmp_path):
    """TemporÃƒÂ¤rer DB-Pfad"""
    return str(tmp_path / "test.db")


@pytest.fixture
def controller(mock_db_path):
    """SemesterController Instanz mit gemockten Dependencies"""
    with patch('controllers.semester_controller.StudentRepository'), \
            patch('controllers.semester_controller.EinschreibungRepository'), \
            patch('controllers.semester_controller.ModulRepository'), \
            patch('controllers.semester_controller.ModulbuchungRepository'):
        return SemesterController(mock_db_path)


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


# ========== Initialization Tests ==========

def test_controller_initialization(mock_db_path):
    """Test: Controller wird korrekt initialisiert"""
    with patch('controllers.semester_controller.StudentRepository'), \
            patch('controllers.semester_controller.EinschreibungRepository'), \
            patch('controllers.semester_controller.ModulRepository'), \
            patch('controllers.semester_controller.ModulbuchungRepository'):
        controller = SemesterController(mock_db_path)

        assert controller.db_path == mock_db_path


# ========== get_modules_for_semester Tests ==========

def test_get_modules_for_semester_no_student(controller):
    """Test: Module laden wenn Student nicht existiert"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=None)

    result = controller.get_modules_for_semester(999, 1)

    assert result['success'] is False
    assert 'error' in result
    assert 'Kein Student' in result['error']


def test_get_modules_for_semester_success(controller, sample_student, sample_einschreibung):
    """Test: Module werden erfolgreich geladen"""
    # Mock Student & Einschreibung
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    # Mock Module
    mock_module = MagicMock()
    mock_module.modul_id = 1
    mock_module.name = "Mathematik I"
    mock_module.status = 'verfÃƒÂ¼gbar'
    mock_module.to_dict.return_value = {
        'modul_id': 1,
        'name': 'Mathematik I',
        'status': 'verfÃƒÂ¼gbar',
        'ects': 5
    }

    controller._SemesterController__modul_repo.get_modules_for_semester = Mock(return_value=[mock_module])

    result = controller.get_modules_for_semester(1, 1)

    assert result['success'] is True
    assert result['semester'] == 1
    assert 'modules' in result
    assert len(result['modules']) > 0


def test_get_modules_for_semester_with_booked_module(controller, sample_student, sample_einschreibung):
    """Test: Gebuchte Module haben modulbuchung_id"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    # Mock gebuchtes Modul
    mock_module = MagicMock()
    mock_module.modul_id = 1
    mock_module.name = "Mathematik I"
    mock_module.status = 'gebucht'
    mock_module.to_dict.return_value = {
        'modul_id': 1,
        'name': 'Mathematik I',
        'status': 'gebucht',
        'ects': 5
    }

    controller._SemesterController__modul_repo.get_modules_for_semester = Mock(return_value=[mock_module])

    # Mock SQLite fÃƒÂ¼r modulbuchung_id
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = {
            'modulbuchung_id': 10,
            'pruefungsdatum': None,
            'anmeldemodus': None
        }
        mock_connect.return_value = mock_conn

        result = controller.get_modules_for_semester(1, 1)

    assert result['success'] is True
    assert result['modules'][0]['modulbuchung_id'] == 10


def test_get_modules_for_semester_with_exam_date(controller, sample_student, sample_einschreibung):
    """Test: Module mit PrÃƒÂ¼fungsdatum haben Status 'angemeldet'"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    mock_module = MagicMock()
    mock_module.modul_id = 1
    mock_module.name = "Mathematik I"
    mock_module.status = 'gebucht'
    mock_module.to_dict.return_value = {
        'modul_id': 1,
        'name': 'Mathematik I',
        'status': 'gebucht',
        'ects': 5
    }

    controller._SemesterController__modul_repo.get_modules_for_semester = Mock(return_value=[mock_module])

    # Mock mit PrÃƒÂ¼fungsdatum
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = {
            'modulbuchung_id': 10,
            'pruefungsdatum': '2024-06-15',
            'anmeldemodus': 'Automatisch'
        }
        mock_connect.return_value = mock_conn

        result = controller.get_modules_for_semester(1, 1)

    assert result['success'] is True
    assert result['modules'][0]['status'] == 'angemeldet'
    assert result['modules'][0]['pruefungsdatum'] == '2024-06-15'


def test_get_modules_for_semester_no_einschreibung_fallback(controller, sample_student):
    """Test: Fallback auf Studiengang 1 wenn keine Einschreibung"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(
        side_effect=Exception("Keine Einschreibung")
    )

    controller._SemesterController__modul_repo.get_modules_for_semester = Mock(return_value=[])

    result = controller.get_modules_for_semester(1, 1)

    # Sollte trotzdem erfolgreich sein (mit Fallback)
    assert result['success'] is True


def test_get_modules_for_semester_various_semesters(controller, sample_student, sample_einschreibung):
    """Test: Module kÃƒÂ¶nnen fÃƒÂ¼r verschiedene Semester geladen werden"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)
    controller._SemesterController__modul_repo.get_modules_for_semester = Mock(return_value=[])

    for semester in range(1, 8):
        result = controller.get_modules_for_semester(1, semester)

        assert result['success'] is True
        assert result['semester'] == semester


def test_get_modules_for_semester_exception_handling(controller):
    """Test: Exception wird abgefangen"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(
        side_effect=Exception("DB Error")
    )

    result = controller.get_modules_for_semester(1, 1)

    assert result['success'] is False
    assert 'error' in result


# ========== book_module Tests ==========

def test_book_module_no_student(controller):
    """Test: Modul buchen wenn Student nicht existiert"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=None)

    result = controller.book_module(999, 1)

    assert result['success'] is False
    assert 'error' in result
    assert 'Kein Student' in result['error']


def test_book_module_success(controller, sample_student, sample_einschreibung):
    """Test: Modul wird erfolgreich gebucht"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    # Mock SQLite
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn

        # Modul ist noch nicht gebucht
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_connect.return_value = mock_conn

        result = controller.book_module(1, 1)

    assert result['success'] is True
    assert 'message' in result
    assert 'erfolgreich gebucht' in result['message']


def test_book_module_already_booked(controller, sample_student, sample_einschreibung):
    """Test: Bereits gebuchtes Modul gibt Fehler"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    # Mock SQLite - Modul bereits gebucht
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn

        # Modul ist bereits gebucht (gibt ID zurÃƒÂ¼ck)
        mock_conn.execute.return_value.fetchone.return_value = (10,)
        mock_connect.return_value = mock_conn

        result = controller.book_module(1, 1)

    assert result['success'] is False
    assert 'error' in result
    assert 'bereits gebucht' in result['error']


def test_book_module_no_einschreibung(controller, sample_student):
    """Test: Modul buchen ohne aktive Einschreibung schlÃƒÂ¤gt fehl"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(
        side_effect=Exception("Keine Einschreibung")
    )

    result = controller.book_module(1, 1)

    assert result['success'] is False
    assert 'error' in result


def test_book_module_exception_handling(controller):
    """Test: Exception beim Buchen wird abgefangen"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(
        side_effect=Exception("Critical DB Error")
    )

    result = controller.book_module(1, 1)

    assert result['success'] is False
    assert 'error' in result


def test_book_module_foreign_key_constraint(controller, sample_student, sample_einschreibung):
    """Test: Foreign Key Constraint wird aktiviert"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_connect.return_value = mock_conn

        controller.book_module(1, 1)

        # PrÃƒÂ¼fe ob PRAGMA foreign_keys aufgerufen wurde
        calls = [str(call) for call in mock_conn.execute.call_args_list]
        assert any('PRAGMA foreign_keys' in str(call) for call in calls)


# ========== Integration Tests ==========

def test_book_and_get_modules_workflow(controller, sample_student, sample_einschreibung):
    """Test: Workflow - Modul buchen und dann Module laden"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    # 1. Modul buchen
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_connect.return_value = mock_conn

        book_result = controller.book_module(1, 1)

    assert book_result['success'] is True

    # 2. Module laden
    mock_module = MagicMock()
    mock_module.modul_id = 1
    mock_module.status = 'gebucht'
    mock_module.to_dict.return_value = {'modul_id': 1, 'status': 'gebucht'}

    controller._SemesterController__modul_repo.get_modules_for_semester = Mock(return_value=[mock_module])

    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = {
            'modulbuchung_id': 10,
            'pruefungsdatum': None,
            'anmeldemodus': None
        }
        mock_connect.return_value = mock_conn

        modules_result = controller.get_modules_for_semester(1, 1)

    assert modules_result['success'] is True
    assert modules_result['modules'][0]['status'] == 'gebucht'


def test_response_structure_completeness(controller, sample_student, sample_einschreibung):
    """Test: Response enthÃƒÂ¤lt alle erforderlichen Felder"""
    controller._SemesterController__student_repo.get_by_login_id = Mock(return_value=sample_student)
    controller._SemesterController__einschreibung_repo.get_aktive_by_student = Mock(return_value=sample_einschreibung)

    mock_module = MagicMock()
    mock_module.modul_id = 1
    mock_module.status = 'verfÃƒÂ¼gbar'
    mock_module.to_dict.return_value = {
        'modul_id': 1,
        'name': 'Test Modul',
        'status': 'verfÃƒÂ¼gbar',
        'ects': 5
    }

    controller._SemesterController__modul_repo.get_modules_for_semester = Mock(return_value=[mock_module])

    result = controller.get_modules_for_semester(1, 1)

    # PrÃƒÂ¼fe Response-Struktur
    assert 'success' in result
    assert 'semester' in result
    assert 'modules' in result
    assert isinstance(result['modules'], list)

    # PrÃƒÂ¼fe Modul-Struktur
    module = result['modules'][0]
    assert 'modulbuchung_id' in module
    assert 'pruefungsdatum' in module
    assert 'anmeldemodus' in module