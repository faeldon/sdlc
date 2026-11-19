# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""This repo's comment health for `/sdlc:retro`'s Quality pillar, with Cost as its guardrail.

Named in `.sdlc/config.toml` under `retro.indicators`, so only `sdlc.py retro` in this repo runs
it, as `function-heat.py` is. It reads every `*.py` file under `scripts/` and
`plugins/factory/scripts/` on the base branch and prints indicator rows, JSON Lines, which the
report sets against the last retrospective's, so each row's trend is the report's own `Change`:

- per file, `comment density`: comment and docstring lines over non-blank lines, a line that is
  both counted once; and `narration share`, for a file with comments;
- for `all scripts`, the density across every file, the files outside `BAND`, the narration
  share, the `comment token share` (comment and docstring bytes over all bytes) and `comment est.
  tokens` (those bytes / 4, the retrospective's own estimate);
- `long functions (30+ lines)` and `hot functions`, each a count and, when there are any, the
  `share with a docstring`. Long is a top-level function or a top-level class's method spanning
  `LONG` lines or more; hot is one function heat's `rank()` keeps with a commit since the last
  retrospective.

Comments are read with `tokenize`, never by text, so a `#` in a string is none. Tool directives
(`# noqa`, `# fmt:`, `# type:`, `# pragma`), a line-1 shebang and the PEP 723 block are not
comments. A comment block (consecutive full-line comments, or one trailing comment) of at most
`NARRATION_MOST_LINES` lines narrates when `NARRATION_OVERLAP` of its words are in the code line it
describes: the next code line for a block, its own line for a trailing one. The rule is narrow and
fixed on purpose: the signal is a trend, so a rule that never moves matters more than one that
catches everything.

Function heat (`function-heat.py`, beside this) is loaded by path for the base branch, the
last-retrospective boundary and the hot ranking, so the two indicators can't disagree on them.
Nothing is written, a file that doesn't parse gives no rows, and rows carry names and numbers only.
"""

from __future__ import annotations

import ast
import importlib.util
import io
import json
import re
import sys
import tokenize
from pathlib import Path

DIRS = ("scripts", "plugins/factory/scripts")
BAND = (0.10, 0.40)
LONG = 30
NARRATION_MOST_LINES = 2
NARRATION_OVERLAP = 0.5
DIRECTIVES = ("noqa", "fmt:", "type:", "pragma")
STOPWORDS = frozenset({
    "the", "and", "for", "are", "but", "not", "all", "any", "can", "was", "one", "has", "have",
    "had", "from", "this", "that", "with", "into", "its", "when", "then", "than", "else", "here",
    "there", "what", "which", "while", "been", "were", "they", "them", "their", "will", "would",
    "should", "could", "does", "each", "also", "only", "just", "over", "such", "some",
})  # fmt: skip
# The PEP 723 block's opening and closing lines.
BLOCK_OPEN = re.compile(r"^# /// [a-zA-Z0-9-]+$")
BLOCK_CLOSE = "# ///"
LONG_NAME = "long functions (30+ lines)"
HOT_NAME = "hot functions"
ALL = "all scripts"
NOT_CODE = frozenset({
    tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
    tokenize.ENDMARKER, tokenize.ENCODING,
})  # fmt: skip


def _load_heat():
    """`function-heat.py`, beside this script, loaded by path: its name holds a hyphen."""
    path = Path(__file__).with_name("function-heat.py")
    spec = importlib.util.spec_from_file_location("sdlc_function_heat", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HEAT = _load_heat()


def _metadata_lines(lines: list[str]) -> set[int]:
    """The 1-based lines of each PEP 723 block, its opening and closing lines included."""
    out: set[int] = set()
    start = None
    for n, line in enumerate(lines, 1):
        if start is None and BLOCK_OPEN.match(line):
            start = n
        elif start is not None and line == BLOCK_CLOSE:
            out.update(range(start, n + 1))
            start = None
        elif start is not None and not (line == "#" or line.startswith("# ")):
            start = None
    return out


def _is_directive(text: str, line: int) -> bool:
    body = text[1:].strip()
    return body.startswith(DIRECTIVES) or (line == 1 and text.startswith("#!"))


def scan(source: str) -> tuple[list[tuple[int, str, bool]], dict[int, str]]:
    """One `tokenize` pass: each comment as (line, text, full-line), leaving out directives and the
    PEP 723 block, and each line's code tokens joined, by the line they start on."""
    skip = _metadata_lines(source.splitlines())
    comments: list[tuple[int, str, bool]] = []
    code: dict[int, list[str]] = {}
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        line = tok.start[0]
        if tok.type == tokenize.COMMENT:
            if line not in skip and not _is_directive(tok.string, line):
                comments.append((line, tok.string, not tok.line[: tok.start[1]].strip()))
        elif tok.type not in NOT_CODE:
            code.setdefault(line, []).append(tok.string)
    return comments, {n: " ".join(parts) for n, parts in code.items()}


def docstrings(source: str, tree: ast.AST) -> list[tuple[int, int, int]]:
    """Each module, class and function docstring as (first line, last line, literal bytes)."""
    out = []
    for node in ast.walk(tree):
        kinds = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        if not isinstance(node, kinds) or not node.body:
            continue
        first = node.body[0]
        value = first.value if isinstance(first, ast.Expr) else None
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            literal = ast.get_source_segment(source, first) or ""
            end = first.end_lineno or first.lineno
            out.append((first.lineno, end, len(literal.encode("utf-8"))))
    return out


def words(text: str) -> set[str]:
    """Lowercase alphabetic runs of `3+` letters, identifiers split on `_` and camelCase, without
    `STOPWORDS`."""
    split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text).lower()
    return set(re.findall(r"[a-z]{3,}", split)) - STOPWORDS


def is_narration(block_words: set[str], code_words: set[str]) -> bool:
    """A block narrates when `NARRATION_OVERLAP` of its words are its line's; with none, never."""
    if not block_words:
        return False
    return len(block_words & code_words) / len(block_words) >= NARRATION_OVERLAP


def _blocks(comments: list[tuple[int, str, bool]]) -> list[tuple[list[tuple[int, str]], bool]]:
    """Comments grouped as blocks: consecutive full-line ones together, each trailing one alone,
    each with whether it is full-line."""
    out: list[tuple[list[tuple[int, str]], bool]] = []
    for line, text, full in sorted(comments):
        if full and out and out[-1][1] and out[-1][0][-1][0] == line - 1:
            out[-1][0].append((line, text))
        else:
            out.append(([(line, text)], full))
    return out


def _narration_lines(comments: list[tuple[int, str, bool]], code: dict[int, str]) -> int:
    code_lines = sorted(code)
    total = 0
    for block, full in _blocks(comments):
        if len(block) > NARRATION_MOST_LINES:
            continue
        last = block[-1][0]
        target = next((n for n in code_lines if n > last), None) if full else last
        code_words = words(code.get(target, "")) if target is not None else set()
        if is_narration(words(" ".join(text[1:] for _, text in block)), code_words):
            total += len(block)
    return total


def long_functions(tree: ast.Module) -> list[tuple[str, bool]]:
    """Each top-level function, and each method of a top-level class (`Class.method`), spanning
    `LONG` lines or more, with whether it has a docstring. A nested function is its holder's."""
    kinds = ast.FunctionDef | ast.AsyncFunctionDef
    found: list[tuple[str, ast.AST]] = []
    for node in tree.body:
        if isinstance(node, kinds):
            found.append((node.name, node))
        elif isinstance(node, ast.ClassDef):
            found += [(f"{node.name}.{n.name}", n) for n in node.body if isinstance(n, kinds)]
    return [
        (name, bool(ast.get_docstring(n)))
        for name, n in found
        if (n.end_lineno or n.lineno) - n.lineno + 1 >= LONG
    ]


def measure(source: str) -> dict | None:
    """One file's counts, or None when it doesn't parse or tokenize."""
    try:
        tree = ast.parse(source)
        comments, code = scan(source)
    except (SyntaxError, tokenize.TokenError, ValueError):
        return None
    docs = docstrings(source, tree)
    doc_lines = {n for first, last, _ in docs for n in range(first, last + 1)}
    comment_lines = {line for line, _, _ in comments}
    return {
        "nonblank": sum(1 for line in source.splitlines() if line.strip()),
        "marked": len(doc_lines | comment_lines),
        "comment_lines": len(comment_lines),
        "narration_lines": _narration_lines(comments, code),
        "comment_bytes": sum(len(t.encode("utf-8")) for _, t, _ in comments)
        + sum(n for _, _, n in docs),
        "bytes": len(source.encode("utf-8")),
        "long": long_functions(tree),
    }


def _share(part: int, whole: int) -> float:
    return round(part / whole, 3)


def _coverage(name: str, has_doc: list[bool]) -> list[dict]:
    """A count, and the share with a docstring when there is any to share."""
    out = [{"name": name, "value": len(has_doc), "unit": "functions"}]
    if has_doc:
        out.append({"name": name, "value": _share(sum(has_doc), len(has_doc)),
                    "unit": "share with a docstring"})  # fmt: skip
    return out


def rows(measured: dict[str, dict], hot: list[bool]) -> str:
    """The rows, JSON Lines, in a fixed order: each file's in path order, then `all scripts`,
    long functions and hot functions. `hot` is each hot function's having a docstring."""
    out: list[dict] = []
    outside = 0
    for path in sorted(measured):
        m = measured[path]
        if m["nonblank"]:
            density = _share(m["marked"], m["nonblank"])
            outside += not BAND[0] <= density <= BAND[1]
            out.append({"name": path, "value": density, "unit": "comment density"})
        if m["comment_lines"]:
            share = _share(m["narration_lines"], m["comment_lines"])
            out.append({"name": path, "value": share, "unit": "narration share"})
    keys = ("nonblank", "marked", "comment_lines", "narration_lines", "comment_bytes", "bytes")
    total = {k: sum(m[k] for m in measured.values()) for k in keys}
    if total["nonblank"]:
        density = _share(total["marked"], total["nonblank"])
        out.append({"name": ALL, "value": density, "unit": "comment density"})
    band = f"files outside {BAND[0]:.2f}-{BAND[1]:.2f}"
    out.append({"name": ALL, "value": outside, "unit": band})
    if total["comment_lines"]:
        share = _share(total["narration_lines"], total["comment_lines"])
        out.append({"name": ALL, "value": share, "unit": "narration share"})
    if total["bytes"]:
        share = _share(total["comment_bytes"], total["bytes"])
        out.append({"name": ALL, "value": share, "unit": "comment token share"})
        tokens = total["comment_bytes"] // 4
        out.append({"name": ALL, "value": tokens, "unit": "comment est. tokens"})
    out += _coverage(LONG_NAME, [doc for m in measured.values() for _, doc in m["long"]])
    out += _coverage(HOT_NAME, hot)
    return "\n".join(json.dumps(row, ensure_ascii=False) for row in out)


def hot(root: Path, base: str, files: list[str]) -> list[bool]:
    """Whether each hot function has a docstring: those function heat's `rank()` keeps for its
    file with a commit since the last retrospective, in its order."""
    out: list[bool] = []
    for path, found in HEAT.heat(root, base, files).items():
        kept = [r["name"] for r in HEAT.rank(found) if r["commits"] >= 1]
        source = HEAT._git(root, "show", f"{base}:{path}") if kept else None
        if source is None:
            continue
        tops = {
            n.name: n
            for n in ast.parse(source).body
            if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
        }
        out += [bool(ast.get_docstring(tops[name])) for name in kept if name in tops]
    return out


def main() -> int:
    root = Path.cwd()
    base = HEAT.base_branch(root)
    if base is None:
        print("comment-health: no base branch found", file=sys.stderr)
        return 1
    listing = HEAT._git(root, "ls-tree", "-r", "-z", "--name-only", base, "--", *DIRS) or ""
    measured = {}
    for path in sorted(p for p in listing.split("\0") if p.endswith(".py")):
        source = HEAT._git(root, "show", f"{base}:{path}")
        found = measure(source) if source is not None else None
        if found is not None:
            measured[path] = found
    print(rows(measured, hot(root, base, HEAT.FILES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
