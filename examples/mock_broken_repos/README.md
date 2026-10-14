# Mock Broken Repositories

This folder contains sample micro-repositories with simulated bugs for testing **GitHealer**:

1. `python_calculator/`:
   - Contains `calculator.py` with an unhandled zero division.
   - Run GitHealer on it:
     ```bash
     git-healer run --repo ./examples/mock_broken_repos/python_calculator --cmd "pytest"
     ```
   - Watch GitHealer analyze the failure, apply the patch, and verify the fix!
