from pathlib import Path

import parsers


def test_every_parser_package_is_registered():
    pkg_dir = Path(parsers.__file__).parent
    package_dirs = {p.name for p in pkg_dir.iterdir() if p.is_dir() and (p / "parser.py").exists()}
    registered = set(parsers.registry.get_factories())
    assert package_dirs == registered, (
        "parsers/__init__.py is out of sync with the parser packages on disk. "
        f"On disk but not imported/registered: {package_dirs - registered}; "
        f"registered but no package dir: {registered - package_dirs}"
    )
