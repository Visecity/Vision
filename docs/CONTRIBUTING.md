# Contributing to Vision

Thank you for your interest in contributing to Vision! This document provides guidelines and instructions for contributing.

## 🌟 Ways to Contribute

- 🐛 Report bugs and issues
- 💡 Suggest new features or improvements
- 📝 Improve documentation
- 🔧 Submit bug fixes
- ✨ Implement new features
- 🎨 Create example pixel art assets
- 🧪 Write tests

## 🚀 Getting Started

### Development Setup

1. Fork and clone the repository
2. Set up your development environment:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies with dev tools
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Start Redis
docker-compose up -d
```

3. Create a branch for your changes:
```bash
git checkout -b feature/your-feature-name
```

### Development Workflow

1. Make your changes
2. Run tests: `pytest`
3. Format code: `black src tests`
4. Lint code: `ruff src tests`
5. Type check: `mypy src`
6. Commit changes with clear messages
7. Push to your fork
8. Create a Pull Request

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code is formatted with Black
- [ ] No linting errors from Ruff
- [ ] Type hints are added/updated
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)

### PR Description Should Include

1. **What** - Description of changes
2. **Why** - Motivation for changes
3. **How** - Implementation approach
4. **Testing** - How changes were tested
5. **Screenshots** - For visual changes

### Example PR Title Format

```
[Type] Brief description

Types: Feature, Fix, Docs, Refactor, Test, Chore
```

## 🎨 Code Style Guidelines

### Python Code

- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 100 characters
- Use docstrings for all public functions/classes

```python
def generate_sprite(
    description: str,
    style: str = "stardew",
    size: tuple[int, int] = (16, 16),
) -> SpriteResult:
    """Generate a pixel art sprite from description.
    
    Args:
        description: Natural language description of the sprite
        style: Art style to use (default: "stardew")
        size: Sprite dimensions in pixels (default: (16, 16))
        
    Returns:
        SpriteResult containing the generated sprite and metadata
        
    Raises:
        GenerationError: If sprite generation fails
    """
    pass
```

### Naming Conventions

- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

### Import Organization

```python
# Standard library
import os
from typing import Any

# Third-party
import anthropic
from langgraph import Graph

# Local
from vision.agents import BaseAgent
from vision.core import Config
```

## 🧪 Testing Guidelines

### Test Structure

```python
def test_feature_description():
    """Test description following AAA pattern."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result.is_valid()
    assert result.value == expected_value
```

### Test Coverage

- Aim for >80% code coverage
- Test edge cases and error conditions
- Use fixtures for complex test data
- Mock external API calls

## 📝 Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

### Examples

```
feat(agents): add palette caching for improved performance

- Implement Redis-based palette cache
- Add cache invalidation strategy
- Reduces API calls by 30%

Closes #123
```

## 🐛 Reporting Bugs

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Step 1
2. Step 2
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., macOS 14.0]
- Python version: [e.g., 3.11.5]
- Vision version: [e.g., 0.1.0]

**Logs/Screenshots**
Error messages or screenshots
```

## 💡 Requesting Features

### Feature Request Template

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Any other relevant information
```

## 📚 Documentation

### Documentation Guidelines

- Use clear, concise language
- Include code examples
- Add type hints and docstrings
- Link to related documentation
- Update docs with code changes

### Building Documentation

```bash
cd docs
mkdocs serve
# View at http://localhost:8000
```

## 🏗️ Architecture Guidelines

### Adding New Agents

1. Inherit from `BaseAgent`
2. Implement required methods
3. Add comprehensive type hints
4. Include detailed docstrings
5. Add unit tests
6. Update documentation

### Code Organization

- Keep modules focused and small
- Use dependency injection
- Follow SOLID principles
- Minimize coupling between agents

## 🎯 Priority Areas

Current focus areas for contributions:

1. **Agent Development** - Implementing specialized agents
2. **Testing** - Expanding test coverage
3. **Documentation** - Improving guides and examples
4. **Performance** - Optimization and caching
5. **Examples** - Creating sample pixel art assets

## 📞 Getting Help

- 💬 Discord: [Join our community](https://discord.gg/vision)
- 📧 Email: dev@vision-project.dev
- 📖 Docs: [Documentation](https://vision-docs.dev)

## 📜 Code of Conduct

Be respectful and inclusive. We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/).

---

Thank you for contributing to Vision! 🎨