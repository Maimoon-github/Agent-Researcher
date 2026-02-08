# Contributing to Source Discovery Agent

Thank you for your interest in contributing to the Source Discovery Agent! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

- **Title**: Clear, descriptive title
- **Description**: Detailed description of the bug
- **Steps to Reproduce**: Step-by-step instructions to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: Python version, OS, relevant dependencies
- **Code Sample**: Minimal code example that demonstrates the issue

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:

- **Title**: Clear description of the enhancement
- **Motivation**: Why this enhancement would be useful
- **Proposed Solution**: How you envision the enhancement working
- **Alternatives**: Any alternative solutions you've considered

### Pull Requests

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/source-discovery-agent.git
   cd source-discovery-agent
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Write clean, readable code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   # Run tests
   pytest tests/
   
   # Run with coverage
   pytest --cov=source_discovery_agent tests/
   
   # Check code style
   flake8 source_discovery_agent/
   black source_discovery_agent/
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- git

### Installation

```bash
# Clone your fork
git clone https://github.com/yourusername/source-discovery-agent.git
cd source-discovery-agent

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Coding Standards

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Keep functions focused and single-purpose
- Maximum line length: 100 characters
- Use type hints where appropriate

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Update README.md if adding new features
- Add inline comments for complex logic

Example docstring:
```python
def calculate_score(url: str, metadata: Optional[Dict] = None) -> float:
    """
    Calculate comprehensive credibility score for a source.
    
    Args:
        url: The URL to score
        metadata: Optional metadata about the source
        
    Returns:
        Credibility score between 0.0 and 1.0
        
    Raises:
        ValueError: If URL is invalid
    """
```

### Testing

- Write tests for all new functionality
- Aim for >80% code coverage
- Use pytest for testing
- Mock external dependencies (network calls, file I/O)

Example test:
```python
def test_calculate_score():
    """Test credibility score calculation"""
    scorer = CredibilityScorer()
    score = scorer.calculate_score("https://example.edu")
    
    assert 0.0 <= score <= 1.0
    assert score > 0.7  # Academic domains should score high
```

## Project Structure

```
source-discovery-agent/
├── source_discovery_agent/   # Main package
│   ├── __init__.py
│   ├── agent.py              # Main orchestration
│   ├── query_analyzer.py
│   ├── source_generator.py
│   ├── validator.py
│   ├── credibility_scorer.py
│   ├── robots_parser.py
│   ├── local_discoverer.py
│   ├── curator.py
│   ├── config.py
│   ├── metrics.py
│   └── exceptions.py
├── tests/                     # Test suite
├── docs/                      # Documentation
├── examples/                  # Example scripts
├── README.md
├── setup.py
├── requirements.txt
└── LICENSE
```

## Commit Message Guidelines

Use clear, descriptive commit messages:

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

Examples:
```
feat: Add support for PDF content extraction
fix: Handle timeout errors in URL validation
docs: Update README with configuration examples
test: Add tests for credibility scorer
```

## Review Process

1. All pull requests require review before merging
2. Address review comments promptly
3. Keep pull requests focused and reasonably sized
4. Ensure all tests pass before requesting review
5. Update the CHANGELOG.md with your changes

## Questions?

If you have questions about contributing, please:

- Check existing issues and pull requests
- Create a new issue with the "question" label
- Reach out to the maintainers

Thank you for contributing to Source Discovery Agent!
