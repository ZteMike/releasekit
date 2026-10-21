# ReleaseKit

ReleaseKit is an open-source Python project for validating, organizing, and safely packaging project deliverables.

## Engineering guidelines

- Prefer simple, readable, and maintainable Python.
- Use type hints and clear, descriptive function names.
- Add automated tests for every new behavior or functionality.
- Never delete or overwrite user files without explicit permission.
- Never commit secrets or private client information.
- Explain important technical decisions in Spanish.
- Treat the project owner as a Software Engineering student: explain reasoning clearly and encourage them to understand and implement parts of the code themselves.
- Before implementing a feature, propose a short plan.
- Keep changes small, focused, and easy to review.

## Change workflow

1. Inspect the relevant code and existing tests before making changes.
2. For feature work, propose a brief implementation plan before editing application code.
3. Implement the smallest coherent change that satisfies the requirement.
4. Add or update automated tests for changed behavior.
5. Run the relevant tests and report the results.
6. Summarize important technical decisions in Spanish.

## Safety

Protect user data throughout validation, organization, and packaging workflows. Any operation that could remove or overwrite a user file requires explicit permission first. Keep credentials, secrets, and private client information out of source code, tests, logs, fixtures, and commits.
