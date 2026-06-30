from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    parser = _TinyYamlParser(lines)
    data = parser.parse_block(0)
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return data


class _TinyYamlParser:
    def __init__(self, lines: list[str]) -> None:
        self.lines = [_strip_comment(line.rstrip()) for line in lines]

    def parse_block(self, start_index: int) -> dict[str, Any]:
        result: dict[str, Any] = {}
        index = start_index

        while index < len(self.lines):
            raw = self.lines[index]
            if not raw.strip():
                index += 1
                continue

            indent = _indent(raw)
            if indent != 0:
                break

            key, value = _split_key_value(raw.strip())
            if value:
                result[key] = _parse_scalar(value)
                index += 1
                continue

            child_lines, index = self._collect_child(index + 1, indent)
            result[key] = _parse_child(child_lines)

        return result

    def _collect_child(self, start_index: int, parent_indent: int) -> tuple[list[str], int]:
        child: list[str] = []
        index = start_index
        while index < len(self.lines):
            raw = self.lines[index]
            if not raw.strip():
                index += 1
                continue
            if _indent(raw) <= parent_indent:
                break
            child.append(raw[parent_indent + 2 :])
            index += 1
        return child, index


def _parse_child(lines: list[str]) -> Any:
    meaningful = [line for line in lines if line.strip()]
    if not meaningful:
        return {}

    if meaningful[0].lstrip().startswith("- "):
        return _parse_list(meaningful)
    return _parse_mapping(meaningful)


def _parse_list(lines: list[str]) -> list[Any]:
    values: list[Any] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.lstrip().startswith("- "):
            index += 1
            continue

        prefix_indent = _indent(line)
        content = line.strip()[2:].strip()
        if not content:
            nested, index = _collect_nested(lines, index + 1, prefix_indent)
            values.append(_parse_child(nested))
            continue

        if ":" in content:
            key, value = _split_key_value(content)
            item: dict[str, Any] = {key: _parse_scalar(value)} if value else {key: {}}
            nested, index = _collect_nested(lines, index + 1, prefix_indent)
            if nested:
                item.update(_parse_mapping([line[2:] if line.startswith("  ") else line for line in nested]))
            values.append(item)
            continue

        values.append(_parse_scalar(content))
        index += 1
    return values


def _parse_mapping(lines: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        raw = lines[index]
        if not raw.strip():
            index += 1
            continue
        key, value = _split_key_value(raw.strip())
        if value:
            result[key] = _parse_scalar(value)
            index += 1
            continue
        nested, index = _collect_nested(lines, index + 1, _indent(raw))
        result[key] = _parse_child(nested)
    return result


def _collect_nested(lines: list[str], start_index: int, parent_indent: int) -> tuple[list[str], int]:
    nested: list[str] = []
    index = start_index
    while index < len(lines):
        raw = lines[index]
        if not raw.strip():
            index += 1
            continue
        if _indent(raw) <= parent_indent:
            break
        nested.append(raw[parent_indent + 2 :])
        index += 1
    return nested, index


def _parse_scalar(value: str) -> Any:
    cleaned = value.strip()
    if cleaned.startswith('"') and cleaned.endswith('"'):
        return cleaned[1:-1]
    if cleaned.startswith("'") and cleaned.endswith("'"):
        return cleaned[1:-1]
    if cleaned.casefold() == "true":
        return True
    if cleaned.casefold() == "false":
        return False
    try:
        return int(cleaned)
    except ValueError:
        return cleaned


def _split_key_value(line: str) -> tuple[str, str]:
    key, _, value = line.partition(":")
    return key.strip(), value.strip()


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index].rstrip()
    return line
