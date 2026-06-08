# Contributing to Travel Agency Enhanced

Thank you for your interest in contributing to the Travel Agency application! We welcome contributions from everyone. This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Welcome diverse perspectives
- Focus on what is best for the community
- Show empathy towards other community members
- Report unacceptable behavior

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Git
- GitHub account

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/travel_agency_enhanced.git
cd travel_agency_enhanced

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Initialize database
flask db upgrade

# Run tests
pytest tests/ -v

# Start development server
python run.py
```

---

## Development Workflow

### 1. Create an Issue

Before starting work, please:

1. **Search existing issues** to avoid duplicates
2. **Create a new issue** describing the problem or feature
3. **Get feedback** from maintainers before major changes

### 2. Fork and Branch

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/travel_agency_enhanced.git
cd travel_agency_enhanced

# Add upstream remote
git remote add upstream https://github.com/your-org/travel_agency_enhanced.git

# Create a feature branch
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/bug-description
# or for documentation:
git checkout -b docs/description
```

### 3. Make Changes

Follow the coding standards (see below) and write tests for your changes.

```bash
# Make your changes
# Write or update tests
# Test locally
pytest tests/ -v

# Check code quality
flake8 .
black .
isort .
mypy app.py routes/ models/
```

### 4. Commit Changes

```bash
# Stage your changes
git add .

# Commit with a clear message
git commit -m "feat: add tour package filtering

- Implement database query optimization
- Add filter UI components
- Write comprehensive tests
- Update documentation

Closes #123"
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Fill out the PR template completely
# Link to related issues
# Add screenshots if applicable
```

---

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some customizations:

```python
# Good
def book_tour_package(package_id: int, user_id: int) -> Booking:
    """Book a tour package for a user.
    
    Args:
        package_id: ID of the tour package
        user_id: ID of the user
        
    Returns:
        The created Booking object
        
    Raises:
        ValueError: If package or user not found
    """
    package = TourPackage.query.get(package_id)
    if not package:
        raise ValueError(f"Package {package_id} not found")
    
    booking = Booking(package_id=package_id, user_id=user_id)
    db.session.add(booking)
    db.session.commit()
    return booking


# Bad
def bookPackage(pid, uid):  # Incorrect naming
    p = TourPackage.query.get(pid)  # Unclear variable names
    if not p:  # Missing error handling
        return None
    b = Booking(package_id=pid, user_id=uid)
    db.session.add(b)
    db.session.commit()
    return b
```

### Code Organization

**File Structure:**
```
models/          - Database models
routes/          - API endpoints and routes
templates/       - HTML templates
static/          - CSS, JS, images
tests/           - Test files
services/        - Business logic services
utils/           - Utility functions
```

**Function Organization:**
```python
# 1. Imports
from flask import Blueprint, render_template, request
from models import db, User

# 2. Module constants
DEFAULT_PAGE_SIZE = 20
UPLOAD_FOLDER = './uploads'

# 3. Helper functions
def validate_email(email: str) -> bool:
    """Validate email format."""
    pass

# 4. Main functions
def create_user(email: str, password: str) -> User:
    """Create a new user."""
    pass

# 5. Error handlers
def handle_not_found(e):
    """Handle 404 errors."""
    pass
```

### Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Variables | snake_case | `user_email`, `page_number` |
| Functions | snake_case | `get_user_by_id()` |
| Classes | PascalCase | `UserModel`, `BookingService` |
| Constants | UPPER_SNAKE_CASE | `MAX_UPLOAD_SIZE`, `TIMEOUT_SECONDS` |
| Private methods | _prefix | `_validate_data()` |
| Protected methods | __prefix | `__init_database()` |

### Code Comments

```python
# Good - explains WHY
if user.role != 'admin':
    # Only admins can access this endpoint
    # Regular users get a 403 Forbidden response
    abort(403)

# Bad - explains WHAT (code already shows this)
user_role = user.role  # Get the user's role
if user_role != 'admin':  # Check if user is admin
    abort(403)  # Return 403 error
```

### Type Hints

Always use type hints for functions:

```python
from typing import Optional, List, Dict
from models import User, Booking

def get_user_bookings(
    user_id: int,
    status: Optional[str] = None,
    limit: int = 10
) -> List[Booking]:
    """Retrieve bookings for a user."""
    pass

def parse_booking_data(data: Dict[str, any]) -> Dict[str, str]:
    """Parse and validate booking data."""
    pass
```

---

## Testing Requirements

### Test Coverage

- Minimum **70% code coverage** required
- All new features must have tests
- All bug fixes must include regression tests

### Test Structure

```python
import pytest
from models import db, User, Booking

class TestBookingSystem:
    """Tests for the booking system."""
    
    def test_book_tour_package_success(self, test_user, test_package):
        """Test successful booking."""
        booking = Booking(user_id=test_user.id, package_id=test_package.id)
        db.session.add(booking)
        db.session.commit()
        
        assert booking.id is not None
        assert booking.user_id == test_user.id
    
    def test_book_tour_package_invalid_package(self, test_user):
        """Test booking with invalid package."""
        with pytest.raises(ValueError):
            Booking(user_id=test_user.id, package_id=99999)
    
    @pytest.mark.parametrize("price", [0, -100, None])
    def test_invalid_booking_price(self, price):
        """Test booking with invalid prices."""
        assert not validate_price(price)
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_bookings.py -v

# Run specific test
pytest tests/test_bookings.py::TestBookingSystem::test_book_tour_package_success

# Run with coverage
pytest tests/ --cov --cov-report=html

# Run marked tests only
pytest tests/ -m "not slow"
```

---

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def book_package(package_id: int, user_id: int) -> Booking:
    """Book a tour package for a user.
    
    This function creates a booking record linking a user to a tour
    package. It handles payment processing and sends confirmation emails.
    
    Args:
        package_id: The ID of the tour package to book.
        user_id: The ID of the user making the booking.
        
    Returns:
        The newly created Booking object with all fields populated.
        
    Raises:
        ValueError: If the package_id or user_id doesn't exist.
        PaymentError: If payment processing fails.
        EmailError: If confirmation email cannot be sent.
        
    Example:
        >>> booking = book_package(package_id=1, user_id=42)
        >>> print(booking.confirmation_number)
        'BOOK-2024-001'
    """
    pass
```

### README Updates

If your changes affect how to use the application:

1. Update the main [README.md](README.md)
2. Add examples if introducing new features
3. Update any affected documentation

### Commit Message Guidelines

```
<type>: <subject>

<body>

<footer>
```

**Type:** feat, fix, docs, style, refactor, perf, test, chore
**Subject:** Imperative, present tense, no period
**Body:** Explain what and why, not how
**Footer:** Reference issues (Closes #123)

**Example:**
```
feat: add tour package search functionality

Implement advanced search with filters for:
- Date range
- Price range
- Destination
- Tour duration

Add database indexes for search optimization.
Write comprehensive tests for all filter combinations.
Update user documentation with search guide.

Closes #456
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guide (run `black`, `flake8`, `isort`)
- [ ] All tests pass locally (`pytest`)
- [ ] Coverage remains above 70%
- [ ] Type checking passes (`mypy`)
- [ ] Security checks pass (`bandit`)
- [ ] Docstrings are complete
- [ ] Tests are written
- [ ] No debug code or print statements
- [ ] No secrets in code
- [ ] Branch is up to date with main

### PR Description

Fill out the PR template completely:

- Describe changes clearly
- Link related issues
- Explain testing
- Note breaking changes
- Add screenshots if applicable

### Code Review

Expect feedback from maintainers:

- Address all comments
- Request re-review after changes
- Be respectful and open to feedback
- Ask questions if unclear

### Merge

A maintainer will merge once:
- ✅ All checks pass
- ✅ Code review approved
- ✅ No conflicts with main
- ✅ All tests passing

---

## Issue Guidelines

### When Creating an Issue

1. **Search first** - Check if issue already exists
2. **Use templates** - Use the provided issue templates
3. **Be specific** - Include clear details and examples
4. **Include environment** - Browser, OS, Python version, etc.
5. **Provide logs** - Include error messages and stack traces

### Issue Labels

| Label | Meaning |
|-------|---------|
| `bug` | Something isn't working |
| `enhancement` | New feature request |
| `documentation` | Improvements to documentation |
| `good-first-issue` | Good for new contributors |
| `help-wanted` | Need community assistance |
| `performance` | Performance improvements |
| `security` | Security issue |
| `urgent` | Needs immediate attention |

---

## Release Process

Releases follow [Semantic Versioning](https://semver.org/):

- **MAJOR** - Incompatible API changes
- **MINOR** - New features (backwards compatible)
- **PATCH** - Bug fixes (backwards compatible)

Format: `v1.2.3`

---

## Community Standards

### Be Respectful
- Welcome diverse perspectives
- Disagree professionally
- No harassment or discrimination

### Be Collaborative
- Help other contributors
- Share knowledge
- Give constructive feedback

### Be Transparent
- Explain decisions
- Document assumptions
- Share context

---

## Getting Help

- **Documentation:** Check [README.md](README.md) and [docs/](docs/) folder
- **Issues:** Search [GitHub Issues](https://github.com/your-org/travel_agency_enhanced/issues)
- **Discussions:** Join [GitHub Discussions](https://github.com/your-org/travel_agency_enhanced/discussions)
- **Email:** contact@travel-agency.com

---

## Advanced Topics

### Setting Up Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml (see example below)

# Install the hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "description of changes"

# Review the migration file in migrations/versions/

# Apply migration
flask db upgrade

# Rollback if needed
flask db downgrade
```

### Performance Profiling

```bash
# Profile with cProfile
python -m cProfile -s cumulative run.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler app.py
```

---

## Troubleshooting

### Issue: Import errors when running tests

**Solution:**
```bash
pip install -e .
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

### Issue: Database locked error

**Solution:**
```bash
# Close any other connections
# Or use different test database
export DATABASE_URL=sqlite:///test2.db
pytest tests/
```

### Issue: Tests pass locally but fail in CI

**Solution:**
- Check Python version matches
- Check dependencies versions match
- Check environment variables are set
- Try running in isolated environment

---

## Thank You!

We appreciate your contributions to making Travel Agency Enhanced better for everyone. Your effort and dedication help make this project successful!

---

**Questions?** Don't hesitate to ask in GitHub Discussions or open an issue.

**Happy coding! 🚀**

---

*Last Updated: January 2024*
