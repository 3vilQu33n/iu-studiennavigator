# 🚗 IU Studiennavigator

**Student Progress Management System with Automotive Infotainment Metaphor**

A comprehensive web application for managing and visualizing academic progress at IU Internationale Hochschule. The system uses an innovative automotive infotainment design where students' progress is represented by a car moving along an interactive SVG roadmap between semester milestones.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.3-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Architecture](#-architecture)
- [Testing](#-testing)
- [License](#-license)
- [Contact](#-contact)

---

## ✨ Features

### Core Functionality
- 🎓 **Student Management** - Complete student data administration
- 📚 **Module Booking** - Semester-based module selection and booking
- 📝 **Exam Registration** - Two-stage dropdown system for different exam types
- 💰 **Fee Management** - Automated semester fee calculation and tracking
- 📊 **Progress Tracking** - Real-time visualization of academic progress
- 🔐 **Authentication** - Secure login with Argon2 password hashing
- 🔄 **Password Reset** - Email-based password recovery system

### Innovative UI
- 🚗 **Automotive Metaphor** - Progress visualized as a car journey
- 🗺️ **SVG Roadmap** - Dynamic, responsive roadmap with milestone markers
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🎨 **Infotainment Style** - Modern automotive dashboard aesthetics
- 🌐 **Bilingual Support** - German and English interface elements

### Technical Excellence
- 🏗️ **MVC Architecture** - Clean separation of concerns
- 📦 **Repository Pattern** - Abstract data access layer
- 🧪 **1000+ Tests** - Comprehensive unit and integration test coverage
- 🐳 **Docker Support** - Containerized deployment ready
- 🔒 **Security Best Practices** - Input validation, CSRF protection, secure sessions

---

## 🛠️ Tech Stack

### Backend
- **Python 3.12+** - Core programming language
- **Flask 3.0.3** - Web framework
- **SQLite3** - Database
- **Argon2** - Password hashing
- **Flask-Mail** - Email functionality

### Frontend
- **HTML5 / CSS3** - Structure and styling
- **Vanilla JavaScript** - Client-side interactions
- **SVG** - Vector graphics for roadmap visualization
- **Jinja2** - Server-side templating

### Testing & DevOps
- **pytest** - Testing framework
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

### Architecture Patterns
- **MVC (Model-View-Controller)** - Application structure
- **Repository Pattern** - Data access abstraction
- **Gateway Pattern** - Database connection management
- **DTO (Data Transfer Object)** - Data encapsulation
- **Service Layer** - Business logic separation

---

## 🚀 Installation

### Prerequisites
- Python 3.12 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Option 1: Standard Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/3vilQu33n/iu-studiennavigator
   cd iu-studiennavigator
   ```

2. **Create virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # OR
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (optional for demo)
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   ```
   http://localhost:5000
   ```

### Option 2: Docker Installation 🐳

1. **Clone the repository**
   ```bash
    git clone https://github.com/3vilQu33n/iu-studiennavigator
    cd iu-studiennavigator  
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d --build
   ```

4. **Access the application**
   ```
   http://localhost:5050
   ```

### Docker Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Remove everything including data
docker-compose down -v
```

---

## 📖 Usage

### Demo Account

For testing purposes, use the demo account:

- **Email:** `demo.student@study.ignatzek.org`
- **Password:** `DemoStudent#2024`

### Main Features

1. **Dashboard** - View your academic progress with the interactive roadmap
2. **Semester View** - Browse and book modules for upcoming semesters
3. **Exam Registration** - Register for exams using the two-stage dropdown
4. **Profile** - Manage your student information
5. **Fees** - View and track semester fees

---

## 📁 Project Structure

```
IU-Studiennavigator/
├── app.py                      # Flask application entry point
├── config.py                   # Application configuration
├── requirements.txt            # Python dependencies
├── schema.txt                  # Database schema documentation
│
├── controllers/                # MVC Controllers
│   ├── auth_controller.py     # Authentication logic
│   ├── dashboard_controller.py # Dashboard views
│   └── semester_controller.py  # Semester management
│
├── models/                     # Domain Models (Entities)
│   ├── student.py             # Student entity with composition
│   ├── login.py               # Login credentials
│   ├── einschreibung.py       # Enrollment with module bookings
│   ├── modulbuchung.py        # Module booking base class
│   ├── pruefungsleistung.py   # Exam performance (inheritance)
│   ├── modul.py               # Module entity
│   ├── studiengang.py         # Study program
│   ├── pruefungstermin.py     # Exam schedule
│   └── gebuehr.py             # Fee management
│
├── repositories/               # Data Access Layer
│   ├── db_gateway.py          # Database connection gateway
│   ├── student_repository.py  # Student data access
│   ├── modul_repository.py    # Module data access
│   ├── einschreibung_repository.py
│   ├── modulbuchung_repository.py
│   ├── pruefungstermin_repository.py
│   └── gebuehr_repository.py
│
├── services/                   # Business Logic Services
│   └── progress_text_service.py # Multilingual progress texts
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html              # Base template
│   ├── login.html             # Login page
│   └── index.html             # Dashboard
│
├── static/                     # Static Assets
│   ├── css/                   # Stylesheets
│   │   ├── base.css
│   │   ├── auth.css
│   │   ├── infotainment.css
│   │   └── modals.css
│   ├── js/
│   │   └── dashboard.js       # Client-side logic
│   └── uploads/               # SVG graphics
│       ├── Pfad.svg           # Main roadmap
│       ├── Pfad_Popup.svg     # Popup miniature
│       └── Car.svg            # Vehicle icon
│
├── tests/                      # Test Suite (1000+ tests)
│   ├── conftest.py            # Pytest configuration
│   ├── integration/           # Integration tests
│   └── unit/                  # Unit tests
│
├── Dockerfile                  # Docker container definition
├── docker-compose.yaml         # Docker Compose configuration
└── .dockerignore              # Docker build exclusions
```

---

## 🏗️ Architecture

### Design Principles

The application follows **SOLID principles** and implements several design patterns:

#### 1. **Composition over Inheritance**
- `Student` composes `Login` (dies with student)
- `Einschreibung` composes `Modulbuchung` collection

#### 2. **Aggregation for Independent Lifecycles**
- `Student` aggregates `Einschreibung` (can exist independently)
- `Einschreibung` aggregates `Gebuehr` (for accounting purposes)

#### 3. **Inheritance with Polymorphism**
- `Pruefungsleistung` extends `Modulbuchung`
- Different exam types handled polymorphically

#### 4. **Encapsulation**
- Private methods with double underscore (`__method_name`)
- Minimal public interfaces
- Data hiding enforced

### Layer Architecture

```
┌─────────────────────────────────────┐
│      Presentation Layer             │
│   (Templates + Static Assets)       │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      Controller Layer               │
│   (Request Handling & Routing)      │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      Service Layer                  │
│   (Business Logic)                  │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      Repository Layer               │
│   (Data Access Abstraction)         │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      Data Layer                     │
│   (SQLite Database)                 │
└─────────────────────────────────────┘
```

### Key OOP Relationships

- **Composition (◆)**: `Student ◆→ Login`, `Einschreibung ◆→ Modulbuchung`
- **Aggregation (◇)**: `Student ◇→ Einschreibung`, `Einschreibung ◇→ Gebuehr`
- **Inheritance (|>)**: `Pruefungsleistung |> Modulbuchung`
- **Association (→)**: `Modul → Pruefungstermin`

---

## 🧪 Testing

The project includes comprehensive test coverage with over **1000 unit and integration tests**.

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_student.py

# Run with verbose output
pytest -v
```

### Test Structure

- **Unit Tests**: Test individual classes and methods in isolation
- **Integration Tests**: Test database interactions and Flask routes
- **Fixtures**: Provide consistent test data and mock objects
- **Coverage**: High coverage ensures code quality and reliability

---

## 📄 Documentation

### Additional Documentation

- **Installation Guide (PDF)**: Detailed step-by-step installation instructions
- **Project Abstract (PDF)**: Technical overview and reflection
- **Schema Documentation**: `schema.txt` contains complete database structure
- **UML Diagrams**: Class diagrams available in project documentation

---

## 🎓 Academic Context

This project was developed as a portfolio project for the course:
**Object-Oriented and Functional Programming with Python (DLBDSOOFPP01_D)**
at **IU Internationale Hochschule**.

### Learning Objectives Demonstrated

- ✅ Object-oriented design principles (SOLID)
- ✅ UML modeling and implementation
- ✅ Design patterns (Repository, Gateway, DTO, Service Layer)
- ✅ Test-driven development
- ✅ MVC architecture
- ✅ Clean code practices
- ✅ Modern web development (Flask)
- ✅ DevOps basics (Docker)

---

## 🚀 Future Enhancements

Potential features for future development:

- [ ] Grade calculation and GPA tracking
- [ ] Module recommendations based on progress
- [ ] Study plan generator
- [ ] PDF transcript export
- [ ] Mobile app (React Native)
- [ ] REST API for third-party integrations
- [ ] Multi-university support
- [ ] Real-time notifications
- [ ] Analytics dashboard for administrators

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Contact

**Teresa Ignatzek**

- 📧 Email: teresa.ignatzek@iu-study.org
- 🎓 IU Internationale Hochschule
- 📚 Student ID: IU14098383

---

## 🙏 Acknowledgments

- IU Internationale Hochschule for the educational framework
- Flask and Python communities for excellent documentation
- Open source contributors for the libraries used in this project

---

<div align="center">

**Made with ❤️ and Python**

*This project demonstrates professional software development practices<br>
combining academic rigor with practical, production-ready implementation.*

</div>