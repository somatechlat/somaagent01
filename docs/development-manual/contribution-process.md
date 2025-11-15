# Contribution Process

## Overview
This document outlines the complete contribution process for SomaAgent01, from idea to merged code.

## Contribution Workflow

```
Idea → Discussion → Issue → Branch → Code → Tests → PR → Review → Merge
```

## 1. Idea Phase

### Before You Start
- Check if a similar feature/fix already exists
- Search existing issues and PRs
- Review the roadmap to see if it's planned

### Discuss Your Idea
- Open a discussion on GitHub
- Explain the problem and proposed solution
- Get feedback from maintainers

## 2. Issue Creation

### Create an Issue
```markdown
**Title**: Clear, concise description

**Description**:
- What problem does this solve?
- What is the proposed solution?
- Any alternatives considered?

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2

**Additional Context**:
- Screenshots, logs, or examples
```

### Issue Labels
- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed

## 3. Development Phase

### Claim the Issue
Comment on the issue: "I'd like to work on this"

### Create a Branch
```bash
git checkout -b type/issue-number-description

# Examples:
git checkout -b feat/123-add-memory-export
git checkout -b fix/456-sse-reconnect
git checkout -b docs/789-api-reference
```

### Development Guidelines
1. **Write tests first** (TDD approach)
2. **Keep changes focused** (one issue per PR)
3. **Follow coding standards**
4. **Update documentation**
5. **Add changelog entry**

## 4. Testing Phase

### Test Requirements
```bash
# Unit tests (required)
pytest tests/unit/ -v

# Integration tests (required for features)
pytest tests/integration/ -v

# E2E tests (required for UI changes)
pytest tests/e2e/ -v

# Coverage check (aim for >80%)
pytest --cov=services --cov-report=html
```

### Manual Testing
1. Start the dev stack: `make dev-up`
2. Test your changes manually
3. Verify no regressions
4. Test edge cases

## 5. Pull Request Phase

### Before Creating PR
```bash
# Update your branch
git fetch origin
git rebase origin/main

# Run all checks
make lint
make test
make type-check

# Ensure clean commit history
git log --oneline
```

### PR Template
```markdown
## Description
Brief description of changes

## Related Issue
Closes #123

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
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests pass locally
```

### PR Best Practices
- Keep PRs small and focused
- Write clear commit messages
- Include screenshots for UI changes
- Link related issues
- Respond to feedback promptly

## 6. Review Phase

### What Reviewers Look For
- Code quality and style
- Test coverage
- Documentation completeness
- Performance implications
- Security considerations
- Breaking changes

### Addressing Feedback
```bash
# Make requested changes
git add .
git commit -m "address review feedback"

# Push updates
git push origin your-branch

# If requested, squash commits
git rebase -i HEAD~3
git push --force-with-lease
```

### Review Etiquette
- Be respectful and professional
- Ask questions if feedback is unclear
- Explain your reasoning
- Be open to suggestions

## 7. Merge Phase

### Merge Requirements
- ✅ All CI checks passing
- ✅ At least one approval
- ✅ No merge conflicts
- ✅ Documentation updated
- ✅ Changelog entry added

### After Merge
1. Delete your branch
2. Close related issues
3. Update any dependent PRs
4. Celebrate! 🎉

## Special Cases

### Breaking Changes
1. Discuss with maintainers first
2. Document migration path
3. Update major version
4. Add deprecation warnings

### Security Fixes
1. Report privately to security@example.com
2. Do not create public issue
3. Wait for coordinated disclosure
4. Follow security policy

### Documentation Only
1. Can be merged faster
2. Still needs review
3. Check for accuracy
4. Verify links work

## Contribution Types

### Code Contributions
- New features
- Bug fixes
- Performance improvements
- Refactoring

### Documentation Contributions
- API documentation
- Tutorials and guides
- README improvements
- Code comments

### Testing Contributions
- New test cases
- Test coverage improvements
- E2E test scenarios
- Performance benchmarks

### Design Contributions
- UI/UX improvements
- Wireframes and mockups
- User research
- Accessibility enhancements

## Quality Standards

### Code Quality
- Passes all linters
- Type hints included
- Docstrings present
- No code smells

### Test Quality
- Tests are deterministic
- Good coverage (>80%)
- Tests are maintainable
- Edge cases covered

### Documentation Quality
- Clear and concise
- Examples included
- Up to date
- Properly formatted

## Getting Help

### Stuck on Something?
1. Check existing documentation
2. Search closed issues/PRs
3. Ask in discussions
4. Tag maintainers (sparingly)

### Need Clarification?
- Comment on the issue
- Ask in PR review
- Join community chat

## Recognition

### Contributors
All contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

### Significant Contributions
- Featured in blog posts
- Mentioned in announcements
- Invited to maintainer team

## References
- [Coding Standards](./coding-standards.md)
- [Testing Guidelines](./testing-guidelines.md)
- [First Contribution Guide](./first-contribution.md)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
