# Contributing to Goldleaves

Thank you for your interest in contributing to Goldleaves! This document provides guidelines and information for contributors.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Git
- PostgreSQL (for production testing)

### Local Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Goldleaves.git
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
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Verify setup by running tests:**
   ```bash
   python -m pytest
   ```

## 🔄 Development Workflow

### Branch Naming Convention

- `feature/` - New features (`feature/user-roles`)
- `fix/` - Bug fixes (`fix/auth-token-expiry`)
- `docs/` - Documentation updates (`docs/api-examples`)
- `test/` - Test improvements (`test/email-verification`)
- `refactor/` - Code refactoring (`refactor/service-layer`)

### Commit Message Style

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `test` - Adding or updating tests
- `refactor` - Code refactoring
- `style` - Code style changes (formatting, etc.)
- `chore` - Maintenance tasks

**Examples:**
```bash
feat(auth): add two-factor authentication
fix(email): resolve verification token expiry issue
docs(api): update authentication endpoint examples
test(auth): add comprehensive token refresh tests
```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run with coverage
python -m pytest --cov=apps --cov-report=html
```

### Writing Tests

1. **Test Structure:** Follow the existing pattern in `tests/`
2. **Fixtures:** Use the provided `client` and `db_session` fixtures
3. **Naming:** Test methods should start with `test_` and be descriptive
4. **Documentation:** Include docstrings explaining what each test validates

**Example:**
```python
def test_user_registration_success(self, client: TestClient, db_session: Session):
    """✅ Test successful user registration with valid data."""
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
```

### Test Categories

- **Unit Tests:** Test individual functions and methods
- **Integration Tests:** Test API endpoints and database interactions
- **Security Tests:** Test authentication, authorization, and input validation
- **Schema Tests:** Test request/response validation

## 📝 Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) conventions
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Import Organization

```python
# Standard library imports
import os
from datetime import datetime, timedelta

# Third-party imports
import jwt
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

# Local application imports
from apps.backend.models import User
from core.config import settings
```

### Error Handling

- Use appropriate HTTP status codes
- Provide clear error messages
- Log errors for debugging
- Handle edge cases gracefully

```python
@router.post("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## 🔍 Pull Request Process

### Before Submitting

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

3. **Run tests locally:**
   ```bash
   python -m pytest
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Pull Request Guidelines

1. **Title:** Use a clear, descriptive title
2. **Description:** Explain what the PR does and why
3. **Testing:** Describe how you tested your changes
4. **Documentation:** Update relevant documentation
5. **Breaking Changes:** Clearly mark any breaking changes

### PR Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🛡️ Security Guidelines

- Never commit sensitive information (passwords, API keys, etc.)
- Use environment variables for configuration
- Validate all user inputs
- Follow secure coding practices
- Report security vulnerabilities privately

## 📋 Issue Reporting

### Bug Reports

Please include:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Error messages or logs

### Feature Requests

Please include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Potential alternatives considered

## 🤝 Code Review

### As a Reviewer

- Be constructive and respectful
- Focus on code quality, not personal preferences
- Explain the reasoning behind suggestions
- Approve when ready, request changes when needed

### As an Author

- Be open to feedback
- Respond to comments promptly
- Make requested changes or explain why not
- Keep PRs focused and reasonably sized

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

## 🆘 Getting Help

- **GitHub Issues:** For bug reports and feature requests
- **GitHub Discussions:** For questions and general discussion
- **Documentation:** Check the docs folder for detailed guides

---

Thank you for contributing to Goldleaves! 🌿
