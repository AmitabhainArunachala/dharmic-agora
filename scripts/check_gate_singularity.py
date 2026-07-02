#!/usr/bin/env python3
"""Fail if publication surfaces bypass the canonical SAB gate evaluator."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
AGORA_ROOT = REPO_ROOT / "agora"
CANONICAL_EVALUATOR = "evaluate_submission_gates"
PROHIBITED_GATE_SYMBOLS = {
    "GateProtocol",
    "GATE_PROTOCOL",
    "OrthogonalGates",
    "evaluate_content",
    "verify_content",
}
PUBLICATION_ROUTE_FRAGMENTS = (
    "/posts",
    "/api/spark/submit",
    "/submit",
    "/sublate",
    "/admin/approve",
)
PUBLICATION_SQL_MARKERS = (
    "INSERT INTO posts",
    "INSERT INTO comments",
    "INSERT INTO sparks",
)


def _iter_python_files() -> Iterable[Path]:
    for path in AGORA_ROOT.rglob("*.py"):
        rel = path.relative_to(REPO_ROOT)
        if "tests" in rel.parts or path.name.endswith(".backup.py"):
            continue
        if ".backup" in path.name:
            continue
        yield path


def _decorator_path(decorator: ast.AST) -> str:
    call = decorator if isinstance(decorator, ast.Call) else None
    if call is None or not call.args:
        return ""
    first = call.args[0]
    return first.value if isinstance(first, ast.Constant) and isinstance(first.value, str) else ""


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    return ""


def _string_constants(node: ast.AST) -> Iterable[str]:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            yield child.value


def _is_publication_route(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in fn.decorator_list:
        path = _decorator_path(decorator)
        if path and any(fragment in path for fragment in PUBLICATION_ROUTE_FRAGMENTS):
            return True
    strings = tuple(_string_constants(fn))
    if any(marker in value for marker in PUBLICATION_SQL_MARKERS for value in strings):
        return True
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "approve"
        for node in ast.walk(fn)
    )


def _called_local_functions(fn: ast.FunctionDef | ast.AsyncFunctionDef, local_names: set[str]) -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name in local_names:
                calls.add(name)
    return calls


def _reachable_publication_functions(
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> set[str]:
    local_names = set(functions)
    graph = {name: _called_local_functions(fn, local_names) for name, fn in functions.items()}
    frontier = {name for name, fn in functions.items() if _is_publication_route(fn)}
    seen: set[str] = set()
    while frontier:
        name = frontier.pop()
        if name in seen:
            continue
        seen.add(name)
        frontier.update(graph.get(name, set()) - seen)
    return seen


def _check_file(path: Path) -> list[str]:
    rel = path.relative_to(REPO_ROOT)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    failures: list[str] = []
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    publication_functions = _reachable_publication_functions(functions)

    if publication_functions:
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("gates"):
                for alias in node.names:
                    if alias.name in PROHIBITED_GATE_SYMBOLS:
                        failures.append(
                            f"{rel}:{node.lineno}: publication module imports noncanonical gate symbol {alias.name}"
                        )

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "GateKeeper":
            failures.append(f"{rel}:{node.lineno}: local GateKeeper evaluator is forbidden")

    for name in publication_functions:
        fn = functions[name]
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                call_name = _call_name(node.func)
                if call_name in PROHIBITED_GATE_SYMBOLS:
                    failures.append(
                        f"{rel}:{node.lineno}: publication route {name} calls {call_name}; use {CANONICAL_EVALUATOR}"
                    )

    return failures


def main() -> int:
    failures: list[str] = []
    for path in _iter_python_files():
        failures.extend(_check_file(path))

    if failures:
        print("Gate singularity check failed:")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(f"Gate singularity check passed: publication routes use {CANONICAL_EVALUATOR}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
