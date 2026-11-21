"""
Package ULTEAMMATE Builder as a legacy Blender add-on zip (Install from disk).

Usage (from this directory):
    python build_release.py

Output:
    <ULTEAMMATE-Builder>/Version/ulteamate-builder-0.8.5.zip
    (version from bl_info in __init__.py; repo layout: ULTEAMMATE-Builder/Plugin/ulteamate-builder/)
"""

from __future__ import annotations

import ast
import fnmatch
import shutil
import sys
import zipfile
from pathlib import Path

ADDON_DIR = Path(__file__).resolve().parent
ADDON_MODULE_NAME = ADDON_DIR.name
INIT_PY = ADDON_DIR / "__init__.py"
ULTEAMMATE_BUILDER_ROOT = ADDON_DIR.parent.parent
OUT_DIR = ULTEAMMATE_BUILDER_ROOT / "Version"

# Dev / junk — never ship these
IGNORE_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".cursor",
    ".venv",
    "dist",
}
IGNORE_FILE_PATTERNS = (
    "*.pyc",
    "*.pyo",
    "*~",
    ".DS_Store",
    "Thumbs.db",
    "build_release.py",
)


def _read_bl_info_version(init_path: Path) -> tuple[int, ...]:
    source = init_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(init_path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "bl_info":
                bl_info = ast.literal_eval(node.value)
                version = bl_info.get("version", (0, 0, 0))
                if not isinstance(version, (tuple, list)):
                    raise ValueError("bl_info['version'] must be a tuple")
                return tuple(int(x) for x in version)
    raise ValueError("bl_info not found in %s" % init_path)


def _version_string(version: tuple[int, ...]) -> str:
    return ".".join(str(x) for x in version)


def _should_ignore_dir(name: str) -> bool:
    return name in IGNORE_DIR_NAMES or name.startswith(".")


def _should_ignore_file(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in IGNORE_FILE_PATTERNS)


def _iter_files_to_package(root: Path):
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(_should_ignore_dir(part) for part in rel.parts[:-1]):
            continue
        if path.is_dir():
            if _should_ignore_dir(path.name):
                continue
            continue
        if _should_ignore_file(path.name):
            continue
        yield path, rel


def build(zip_path: Path | None = None) -> Path:
    if not INIT_PY.is_file():
        raise FileNotFoundError("Missing %s" % INIT_PY)

    version = _read_bl_info_version(INIT_PY)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if zip_path is None:
        zip_path = OUT_DIR / ("%s-%s.zip" % (ADDON_MODULE_NAME, _version_string(version)))

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, rel in _iter_files_to_package(ADDON_DIR):
            arcname = Path(ADDON_MODULE_NAME) / rel
            zf.write(src, arcname.as_posix())
            file_count += 1

    return zip_path, file_count


def main() -> int:
    try:
        zip_path, file_count = build()
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print("Build failed:", exc, file=sys.stderr)
        return 1

    print("Built %s" % zip_path)
    print("  %d files" % file_count)
    print("Install: Blender → Edit → Preferences → Add-ons → Install…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())