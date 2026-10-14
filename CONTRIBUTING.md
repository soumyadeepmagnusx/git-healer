# Contributing to GitHealer

We love contributions! Follow these steps to set up GitHealer locally and submit a pull request.

## Local Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/git-healer.git
   cd git-healer
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   ```

3. **Install dependencies in editable mode:**
   ```bash
   pip install -e .[test]
   ```

4. **Run the test suite:**
   ```bash
   pytest tests/
   ```

5. **Test the interactive demo:**
   ```bash
   git-healer demo
   ```

## Pull Request Guidelines

- Ensure all existing and new unit tests pass (`pytest tests/`).
- Add tests for any new parser or agent functionality.
- Keep commits descriptive (`feat: ...`, `fix: ...`).
