"""Every Python block in the docs has to parse.

Five ``async.md`` snippets shipped as ``SyntaxError`` (bare ``async for``,
``async with`` and ``await`` at module scope) while their sync twins in
``paging.md`` were copy-pasteable. Nothing caught it, because docs are only ever
read by people.

Syntax only. Names are deliberately not resolved: a snippet may reference a
``store()`` or ``handle()`` the reader supplies, and demanding otherwise would
push the docs toward complete programs rather than illustrations.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_FENCE = re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)


def _blocks() -> list[tuple[str, int, str]]:
    """Every ```python fence in the docs, as (path, line number, source)."""
    found: list[tuple[str, int, str]] = []
    sources = [_ROOT / "README.md", *sorted((_ROOT / "docs").rglob("*.md"))]
    for path in sources:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for match in _FENCE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            found.append((str(path.relative_to(_ROOT)), line, match.group(1)))
    return found


_BLOCKS = _blocks()


def test_the_docs_actually_contain_examples():
    """A regex that silently matches nothing would make every test below pass."""
    assert len(_BLOCKS) > 30


@pytest.mark.parametrize(
    ("path", "line", "source"),
    _BLOCKS,
    ids=[f"{path}:{line}" for path, line, _ in _BLOCKS],
)
def test_example_parses(path: str, line: int, source: str):
    try:
        compile(source, f"{path}:{line}", "exec")
    except SyntaxError as exc:
        pytest.fail(f"{path}:{line} does not parse: {exc.msg} (line {exc.lineno})")
