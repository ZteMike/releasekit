import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiscoveredFile:
    relative_path: Path
    size: int


def discover_files(
    directory: Path, excluded_directories: set[str] | None = None
) -> list[DiscoveredFile]:
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    files = []
    excluded_directories = excluded_directories or set()

    for root, directories, filenames in os.walk(directory):
        directories[:] = [name for name in directories if name not in excluded_directories]
        for filename in filenames:
            path = Path(root) / filename
            if not path.is_symlink() and path.is_file():
                files.append(
                    DiscoveredFile(
                        relative_path=path.relative_to(directory),
                        size=path.stat().st_size,
                    )
                )

    return files
