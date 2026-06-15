# Contributing

Thanks for taking the time to contribute! This is a small project, so the process is light.

## Getting started
Requires Python 3.13.

```shell
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Before opening a pull request, make sure these pass:
```shell
pytest
ruff check .
ruff format --check .
```

## Adding a new parser
Parsers are self-contained packages in [`parsers/`](../parsers/) and are discovered
automatically — no edits to `core/` or `bootstrap/` are needed.

1. Create `parsers/<platform>/` with a `parser.py` implementing the `Parser` contract
   (`supports()` + `parse()`).
2. Register a factory in `parsers/<platform>/__init__.py`:
   ```python
   from parsers.registry import register

   @register("<platform>")
   def create_parser(container):
       return Parser(...)
   ```
3. Add a test (a routing case + a `parse()` test on a saved fixture, HTTP mocked).
4. Add a `README.md` to the package following the format below.

A parser is considered done when it has all of: `@register`, a test, and a `README.md`.

### Parser README format
Each parser package must ship a `README.md` with the same sections, filled in from the code
(not from memory). Use this template:

```markdown
# <Platform> Parser

One–two lines: what it expands and what content it extracts (media / metrics / author / time).

## Supported links
- example URLs and/or a short description of the `URL_REGEX` pattern

## Data source
External service / API endpoint and how it is accessed (public / key / proxy).

## Configuration
| Env | Purpose | Required |
|-----|---------|----------|
| `FOO_API_KEY` | … | yes |

(or state explicitly: "Not required.")

## Registration
Name in the auto-registry: `@register("<name>")` → service key `parser_<name>`.

## Notes & limitations
- quirks: special User-Agent, URL encryption, time/timezone, limits, etc.
```

Fill each section from the source of truth:
- `URL_REGEX` in `parser.py` → **Supported links**;
- the `@register(...)` factory and `bootstrap/container.py` → **Configuration** (env vars) and the registry name;
- the parser constructor / `parse()` → **Data source** and **Notes & limitations**.

Don't leave sections empty — either fill them in or write "Not required." / "None."

## Pull requests
- Branch off `master` and keep changes focused.
- Make sure tests, `ruff check` and `ruff format --check` are green.
- Fill in the pull request template.
- Use clear commit messages describing the change.

## Reporting bugs and requesting features
Open an issue using one of the [issue templates](ISSUE_TEMPLATE). For security issues,
see [SECURITY.md](SECURITY.md) instead of opening a public issue.
