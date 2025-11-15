# First Contribution Guide

## Welcome!
Thank you for your interest in contributing to SomaAgent01. This guide will help you make your first contribution.

## Prerequisites
- Git installed and configured
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for UI development)

## Getting Started

### 1. Fork and Clone
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/somaAgent01.git
cd somaAgent01
```

### 2. Set Up Development Environment
```bash
# Start the development stack
make dev-up

# Verify everything is running
curl http://localhost:21016/v1/health
```

### 3. Create a Branch
```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/issue-number-description
```

## Making Changes

### Code Style
- Follow PEP 8 for Python code
- Use type hints
- Write docstrings for functions and classes
- Keep functions small and focused

### Testing
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run specific test
pytest tests/unit/test_your_feature.py -v
```

### Linting
```bash
# Run linters
ruff check .
mypy .

# Auto-fix issues
ruff check --fix .
```

## Submitting Your Contribution

### 1. Commit Your Changes
```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add new feature description"

# Or for bug fixes
git commit -m "fix: resolve issue #123"
```

### Commit Message Format
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

### 2. Push to Your Fork
```bash
git push origin feature/your-feature-name
```

### 3. Create a Pull Request
1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in the PR template
5. Submit the PR

## PR Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] PR description explains the changes
- [ ] No merge conflicts

## Code Review Process
1. Automated checks run (CI/CD)
2. Maintainers review your code
3. Address feedback if requested
4. Once approved, your PR will be merged

## Common Issues

### Tests Failing
```bash
# Check test output
pytest -v

# Run with more detail
pytest -vv --tb=long
```

### Docker Issues
```bash
# Clean restart
make dev-down-hard
make dev-up

# Check logs
docker logs gateway
docker logs conversation-worker
```

### Import Errors
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Getting Help
- Check existing issues on GitHub
- Ask in discussions
- Join our Discord server
- Read the [Development Manual](./index.md)

## What to Contribute

### Good First Issues
Look for issues labeled:
- `good first issue`
- `help wanted`
- `documentation`

### Areas Needing Help
- Documentation improvements
- Test coverage
- Bug fixes
- Performance optimizations
- UI/UX enhancements

## Resources
- [Coding Standards](./coding-standards.md)
- [Testing Guidelines](./testing-guidelines.md)
- [API Reference](./api-reference.md)
- [Architecture Documentation](../technical-manual/architecture.md)

## Thank You!
Every contribution, no matter how small, helps make SomaAgent01 better. We appreciate your time and effort!
