from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup


def _read_requirements(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


setup(
    name="langgraph_demo",
    version="0.1.0",
    packages=find_packages(),
    install_requires=_read_requirements(Path(__file__).parent / "requirements.txt"),
)
