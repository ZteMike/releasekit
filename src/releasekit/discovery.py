
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiscoveredFile:
    relative_path: Path
    size: int


def discover_files(directory: Path) -> list[DiscoveredFile]:
    files = []

    for path in directory.rglob("*"):
        if path.is_file():
            files.append(
                DiscoveredFile(
                    relative_path=path.relative_to(directory),
                    size=path.stat().st_size,
                )
            )

    return files
