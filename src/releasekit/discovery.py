import os
import stat
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiscoveredFile:
    relative_path: Path
    size: int


def _is_windows_junction(path: Path) -> bool:
    return (
        os.name == "nt"
        and os.lstat(path).st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT
    )


def discover_files(
    directory: Path, excluded_directories: set[str] | None = None
) -> list[DiscoveredFile]:
    """Discover files safely inside a directory tree.

    Symbolic links and Windows junctions are not traversed.
    Directory exclusions are matched by directory name at any nesting level.
    Traversal errors are propagated instead of being silently ignored.

    The function only reads filesystem metadata and does not modify source files.

    Args:
        directory: Root directory to scan.
        excluded_directories: Optional directory names to exclude from traversal.

    Returns:
        Discovered files with paths relative to the root directory and file sizes.

    Raises:
        FileNotFoundError: If the root directory does not exist.
        NotADirectoryError: If the root path is not a directory.
        PermissionError: If a directory cannot be read during traversal.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    files = []
    excluded_directories = excluded_directories or set()

    def raise_walk_error(error: OSError) -> None:
        raise error

    for root, directories, filenames in os.walk(directory, onerror=raise_walk_error):
        directories[:] = [
            name
            for name in directories
            if name not in excluded_directories
            and not _is_windows_junction(Path(root) / name)
        ]
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
