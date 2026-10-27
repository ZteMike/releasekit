import os
import stat
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiscoveredFile:
    relative_path: Path
    size: int


def _is_link_or_junction(file_stat: os.stat_result) -> bool:
    return (
        stat.S_ISLNK(file_stat.st_mode)
        or (os.name == "nt" and file_stat.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT)
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
        ValueError: If the root path is a symbolic link or junction.
        PermissionError: If the root or a directory cannot be accessed.
    """
    root_stat = os.lstat(directory)
    if _is_link_or_junction(root_stat):
        raise ValueError(f"Root directory cannot be a symbolic link or junction: {directory}")
    if not stat.S_ISDIR(root_stat.st_mode):
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    files: list[DiscoveredFile] = []
    excluded_directories = excluded_directories or set()

    def raise_walk_error(error: OSError) -> None:
        raise error

    for root, directories, filenames in os.walk(directory, onerror=raise_walk_error):
        directories[:] = [
            name
            for name in directories
            if name not in excluded_directories
            and not _is_link_or_junction(os.lstat(Path(root) / name))
        ]
        for filename in filenames:
            path = Path(root) / filename
            file_stat = os.lstat(path)
            if not _is_link_or_junction(file_stat) and stat.S_ISREG(file_stat.st_mode):
                files.append(
                    DiscoveredFile(
                        relative_path=path.relative_to(directory),
                        size=file_stat.st_size,
                    )
                )

    return files
