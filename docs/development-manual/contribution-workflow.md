# Contribution Workflow

**Standards**: ISO/IEC 12207§6.6

## Getting Started

### 1. Fork Repository

```bash
# Fork on GitHub, then clone
git clone https://github.com/YOUR_USERNAME/somaagent01.git
cd somaagent01

# Add upstream remote
git remote add upstream https://github.com/somatechlat/somaagent01.git
```

### 2. Create Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or bugfix branch
git checkout -b fix/issue-123-description
```

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<description>` | `feature/add-jwt-auth` |
| Bugfix | `fix/<issue>-<description>` | `fix/123-memory-leak` |
| Hotfix | `hotfix/<description>` | `hotfix/security-patch` |
| Docs | `docs/<description>` | `docs/update-api-reference` |
| Refactor | `refactor/<description>` | `refactor/simplify-event-bus` |

## Development Workflow

### 1. Make Changes

```bash
# Edit files
nano services/gateway/main.py

# Run locally
make stack-up

# Test changes
pytest tests/unit/test_gateway.py
```

### 2. Write Tests

```python
# tests/unit/test_your_feature.py
import pytest

def test_your_feature():
    """Test your new feature."""
    result = your_function()
    assert result == expected
```

### 3. Run Quality Checks

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy services/

# Run tests
pytest tests/unit/ --cov=services

# Check coverage
pytest --cov=services --cov-fail-under=80
```

### 4. Commit Changes

```bash
# Stage changes
git add services/gateway/main.py tests/unit/test_gateway.py

# Commit with conventional message
git commit -m "feat(gateway): add JWT authentication

- Implement JWT token validation
- Add /v1/auth/login endpoint
- Update dependencies with PyJWT

Closes #123"
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example**:
```
fix(worker): handle LLM timeout gracefully

- Add timeout handling in call_llm()
- Retry with exponential backoff
- Log timeout events for monitoring

Fixes #456
```

### 5. Push Branch

```bash
# Push to your fork
git push origin feature/your-feature-name
```

## Pull Request Process

### 1. Create PR

1. Go to GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill out PR template

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Commit messages follow convention

## Related Issues
Closes #123
```

### 2. Code Review

**Reviewers check**:
- Code quality and style
- Test coverage (≥80%)
- Documentation updates
- Breaking changes
- Security implications

**Review process**:
1. Automated checks (CI)
2. Peer review (2 approvals required)
3. Maintainer review
4. Approval and merge

### 3. Address Feedback

```bash
# Make requested changes
nano services/gateway/main.py

# Commit changes
git add .
git commit -m "refactor: address review feedback"

# Push updates
git push origin feature/your-feature-name
```

### 4. Merge

**Merge strategies**:
- **Squash and merge**: Default for features
- **Rebase and merge**: For clean history
- **Merge commit**: For large features

**After merge**:
```bash
# Update local main
git checkout main
git pull upstream main

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

## CI/CD Pipeline

### Automated Checks

**On PR**:
1. Linting (black, ruff)
2. Type checking (mypy)
3. Unit tests
4. Integration tests
5. Coverage check (≥80%)
6. Security scan (trivy)

**On merge to main**:
1. All PR checks
2. E2E tests
3. Build Docker images
4. Push to registry
5. Deploy to staging

### Status Checks

| Check | Required | Blocks Merge |
|-------|----------|--------------|
| Lint | ✅ | Yes |
| Type Check | ✅ | Yes |
| Unit Tests | ✅ | Yes |
| Coverage ≥80% | ✅ | Yes |
| Integration Tests | ✅ | Yes |
| Security Scan | ✅ | Yes |
| E2E Tests | ⚠️ | No (warning only) |

## Release Process

### Version Numbering

**Semantic Versioning**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Creating a Release

```bash
# 1. Update version
echo "1.2.0" > VERSION

# 2. Update changelog
nano docs/changelog.md

# 3. Commit
git add VERSION docs/changelog.md
git commit -m "chore: bump version to 1.2.0"

# 4. Tag
git tag -a v1.2.0 -m "Release v1.2.0"

# 5. Push
git push upstream main --tags
```

### Release Notes

```markdown
## [1.2.0] - 2025-01-24

### Added
- JWT authentication support
- Memory search API endpoint
- Prometheus metrics for circuit breaker

### Changed
- Improved error handling in conversation worker
- Updated dependencies (LiteLLM 1.50.0)

### Fixed
- Memory replication lag issue (#456)
- Streaming connection timeout (#478)

### Security
- Patched SQL injection vulnerability (CVE-2025-1234)
```

## Best Practices

### DO

- ✅ Write tests for all new code
- ✅ Update documentation
- ✅ Follow coding standards
- ✅ Keep PRs small and focused
- ✅ Respond to review feedback promptly
- ✅ Rebase on main before merging
- ✅ Write descriptive commit messages
- ✅ Add type hints

### DON'T

- ❌ Commit directly to main
- ❌ Push without running tests
- ❌ Include unrelated changes
- ❌ Ignore linter warnings
- ❌ Skip documentation updates
- ❌ Merge without approval
- ❌ Leave commented-out code
- ❌ Hardcode secrets

## Getting Help

### Resources

- **Documentation**: `/docs`
- **GitHub Issues**: https://github.com/somatechlat/somaagent01/issues
- **Discord**: https://discord.gg/B8KZKNsPpj
- **Email**: dev@somaagent01.ai

### Issue Templates

**Bug Report**:
```markdown
**Describe the bug**
Clear description of the issue.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What should happen.

**Actual behavior**
What actually happens.

**Environment**
- OS: macOS 14.0
- Python: 3.11.5
- Docker: 24.0.6

**Logs**
```
Paste relevant logs here
```
```

**Feature Request**:
```markdown
**Is your feature request related to a problem?**
Description of the problem.

**Describe the solution you'd like**
Clear description of desired functionality.

**Describe alternatives you've considered**
Other approaches you've thought about.

**Additional context**
Any other relevant information.
```

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

**Positive behavior**:
- Using welcoming language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**Unacceptable behavior**:
- Trolling, insulting comments, personal attacks
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Violations may result in:
1. Warning
2. Temporary ban
3. Permanent ban

Report violations to: conduct@somaagent01.ai

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
