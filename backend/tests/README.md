# Backend Tests

This directory contains unit tests for the backend components of the application.

## Test Structure

- `test_auth_system.py`: Tests for JWT-based authentication, token generation, and validation
- `test_password_utils.py`: Tests for password hashing and verification utilities
- `test_models.py`: Tests for SQLAlchemy database models and their relationships
- `conftest.py`: Shared pytest fixtures and test configuration

## Running Tests

To run the tests, make sure you have pytest installed and execute:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=backend

# Run specific test file
pytest test_auth_system.py

# Run tests with verbose output
pytest -v
```

## Test Coverage

The tests cover:

### Authentication System
- Token generation and validation
- User authentication
- Role-based access control
- Protected route handlers

### Password Utilities
- Password hashing
- Hash verification
- Hash uniqueness
- Special character handling
- Unicode support

### Database Models
- User model and relationships
- LLM configurations
- Document handling settings
- SQL server connections
- Document records and logs
- Field constraints and validations
- Default values

## Adding New Tests

When adding new tests:

1. Use the appropriate test file based on functionality
2. Create new fixtures in conftest.py if needed
3. Follow the existing naming conventions
4. Include docstrings explaining test purpose
5. Use meaningful assertions
6. Consider edge cases and error conditions