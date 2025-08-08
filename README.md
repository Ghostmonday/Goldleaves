# 🌿 Goldleaves

[![Status](https://img.shields.io/badge/Status-Under%20Development-yellow.svg)](https://github.com/Ghostmonday/Goldleaves)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/Tests-52%2F52%20Passing-brightgreen.svg)](https://github.com/Ghostmonday/Goldleaves)

**Goldleaves** is a robust backend foundation for an AI-augmented legal document platform. Built with modern Python technologies, it provides secure authentication, email verification, and a scalable architecture ready for AI integration and multi-tenant deployments.

## ✨ Features

### ✅ Completed Modules
- **🔐 Authentication System** - JWT-based auth with secure password hashing
- **📧 Email Verification** - Complete send/confirm/resend workflow
- **🔄 Token Refresh** - Automatic token renewal system
- **🧪 Comprehensive Testing** - 100% test coverage (52/52 tests passing)
- **🛡️ Security** - Password hashing, JWT tokens, input validation
- **📊 Database Integration** - SQLAlchemy 2.0 with Alembic migrations

### 🚧 Planned Features
- **🎯 Admin Dashboard** - User management and system monitoring
- **🤖 AI Integration** - Document analysis and legal insights
- **🏢 Multi-tenant Support** - Organization-based data isolation
- **📈 Analytics** - Usage tracking and performance metrics
- **🔍 Document Processing** - PDF parsing and text extraction
- **⚡ Real-time Features** - WebSocket support for live updates

## 🛠️ Tech Stack

- **Framework:** FastAPI (async Python web framework)
- **Database:** PostgreSQL with SQLAlchemy 2.0 ORM
- **Authentication:** JWT tokens with bcrypt password hashing
- **Validation:** Pydantic models for request/response validation
- **Testing:** Pytest with fixtures and comprehensive coverage
- **Migrations:** Alembic for database schema management
- **Configuration:** Environment-based settings with Pydantic

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL (for production) or SQLite (for development)
- Git

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ghostmonday/Goldleaves.git
   cd Goldleaves
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy example environment file
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server:**
   ```bash
   uvicorn apps.backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Redoc: http://localhost:8000/redoc

## 🧪 Testing

The project maintains 100% test coverage across all implemented modules.

### Run All Tests
```bash
python -m pytest
```

### Run Specific Test Modules
```bash
# Authentication tests
python -m pytest tests/test_auth.py -v

# Email verification tests
python -m pytest tests/test_email_verification.py -v

# Token refresh tests
python -m pytest tests/test_token_refresh.py -v
```

### Test Coverage Report
```bash
python -m pytest --cov=apps --cov-report=html
```

## 📁 Project Structure

```
gold-leaves/
├── apps/
│   └── backend/
│       ├── api/
│       │   └── routers/          # API endpoint definitions
│       ├── models/               # SQLAlchemy database models
│       ├── services/             # Business logic layer
│       └── main.py              # FastAPI application entry point
├── core/
│   ├── config.py                # Application configuration
│   └── database.py              # Database connection setup
├── tests/                       # Comprehensive test suite
├── alembic/                     # Database migration files
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project configuration
└── alembic.ini                 # Alembic configuration
```

## 📊 Test Suite Overview

| Module | Tests | Status |
|--------|-------|--------|
| Authentication | 24 | ✅ Passing |
| Email Verification | 24 | ✅ Passing |
| Token Refresh | 4 | ✅ Passing |
| **Total** | **52** | **✅ 100% Passing** |

### Test Categories
- **Unit Tests:** Individual service and utility functions
- **Integration Tests:** API endpoint behavior and database interactions
- **Security Tests:** Authentication, authorization, and input validation
- **Schema Validation:** Request/response structure verification

## 🔧 Configuration

The application uses environment-based configuration. Key settings include:

- `DATABASE_URL` - Database connection string
- `JWT_SECRET` - Secret key for JWT token signing
- `JWT_ALGORITHM` - Algorithm for JWT encoding (default: HS256)
- `EMAIL_*` - Email service configuration (for production)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Commit your changes (`git commit -m 'feat: add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

### Phase 1: Foundation (✅ Complete)
- Core authentication system
- Email verification workflow
- Comprehensive test coverage
- API documentation

### Phase 2: Administration (🚧 In Progress)
- Admin dashboard
- User management
- System monitoring
- Role-based permissions

### Phase 3: AI Integration (📋 Planned)
- Document analysis engine
- Legal insight generation
- AI-powered search
- Natural language processing

### Phase 4: Scale & Deploy (📋 Planned)
- Multi-tenant architecture
- Performance optimization
- Production deployment
- Monitoring and logging

---

**Built with ❤️ for the legal technology community**

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/Ghostmonday/Goldleaves).