import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from releasekit.discovery import discover_files


def test_discovers_file_in_directory(tmp_path: Path):
    # Arrange: preparar un archivo temporal
    file = tmp_path / "document.txt"
    file.write_text("Hello ReleaseKit", encoding="utf-8")

    # Act: ejecutar la función que queremos probar
    result = discover_files(tmp_path)

    # Assert: comprobar el resultado
    assert len(result) == 1
    assert result[0].relative_path == Path("document.txt")
    assert result[0].size == len(b"Hello ReleaseKit")


def test_discovers_files_in_nested_directories(tmp_path: Path):
    nested_directory = tmp_path / "documents" / "drafts"
    nested_directory.mkdir(parents=True)

    (tmp_path / "root.txt").write_bytes(b"root")
    (tmp_path / "documents" / "notes.txt").write_bytes(b"notes")
    (nested_directory / "draft.txt").write_bytes(b"draft content")

    result = discover_files(tmp_path)

    assert len(result) == 3
    assert {file.relative_path: file.size for file in result} == {
        Path("root.txt"): len(b"root"),
        Path("documents/notes.txt"): len(b"notes"),
        Path("documents/drafts/draft.txt"): len(b"draft content"),
    }


def test_ignores_symbolic_links(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()

    regular_file = project / "normal.txt"
    regular_file.write_text("normal", encoding="utf-8")

    external_file = tmp_path / "outside.txt"
    external_file.write_text("outside", encoding="utf-8")

    symlink = project / "external-link.txt"

    try:
        symlink.symlink_to(external_file)
    except (OSError, NotImplementedError):
        pytest.skip("Symbolic links are not available in this environment")

    result = discover_files(project)

    assert [file.relative_path for file in result] == [Path("normal.txt")]


def test_ignores_path_reported_as_symbolic_link(
    tmp_path: Path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    normal_file = project / "normal.txt"
    normal_file.write_text("normal", encoding="utf-8")

    symlink_candidate = project / "link.txt"
    symlink_candidate.write_text("linked", encoding="utf-8")

    original_lstat = os.lstat

    def fake_lstat(path, *args, **kwargs):
        if Path(path) == symlink_candidate:
            return SimpleNamespace(st_mode=stat.S_IFLNK, st_reparse_tag=0)
        return original_lstat(path, *args, **kwargs)

    monkeypatch.setattr("releasekit.discovery.os.lstat", fake_lstat)

    result = discover_files(project)

    assert [file.relative_path for file in result] == [Path("normal.txt")]


def test_uses_file_lstat_metadata_for_size(tmp_path: Path, monkeypatch):
    file = tmp_path / "document.txt"
    file.write_text("content", encoding="utf-8")
    original_lstat = os.lstat

    def fake_lstat(path, *args, **kwargs):
        if Path(path) == file:
            return SimpleNamespace(st_mode=stat.S_IFREG, st_reparse_tag=0, st_size=123)
        return original_lstat(path, *args, **kwargs)

    monkeypatch.setattr("releasekit.discovery.os.lstat", fake_lstat)

    result = discover_files(tmp_path)

    assert [(item.relative_path, item.size) for item in result] == [(Path("document.txt"), 123)]


def test_excludes_directories_by_name(tmp_path: Path):
    source_directory = tmp_path / "src"
    source_directory.mkdir()

    git_directory = tmp_path / ".git"
    git_directory.mkdir()

    nested_venv = tmp_path / "docs" / ".venv"
    nested_venv.mkdir(parents=True)

    (tmp_path / "root.txt").write_text("root", encoding="utf-8")
    (source_directory / "app.py").write_text("app", encoding="utf-8")
    (git_directory / "config").write_text("git config", encoding="utf-8")
    (nested_venv / "package.py").write_text("venv", encoding="utf-8")

    result = discover_files(
        tmp_path,
        excluded_directories={".git", ".venv"},
    )

    assert {file.relative_path for file in result} == {
        Path("root.txt"),
        Path("src/app.py"),
    }


def test_raises_error_when_directory_does_not_exist(tmp_path: Path):
    missing_directory = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        discover_files(missing_directory)


def test_raises_error_when_path_is_not_a_directory(tmp_path: Path):
    file = tmp_path / "document.txt"
    file.write_text("content", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        discover_files(file)


def test_raises_permission_error_during_directory_walk(
    tmp_path: Path,
    monkeypatch,
):
    restricted_directory = tmp_path / "restricted"

    def fake_walk(directory: Path, *, onerror=None):
        error = PermissionError(
            13,
            "Permission denied",
            str(restricted_directory),
        )

        if onerror is not None:
            onerror(error)

        return []

    monkeypatch.setattr("releasekit.discovery.os.walk", fake_walk)

    with pytest.raises(PermissionError, match="Permission denied"):
        discover_files(tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="Windows junctions only")
def test_does_not_traverse_windows_junctions(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()

    normal_file = project / "normal.txt"
    normal_file.write_text("normal", encoding="utf-8")

    external_directory = tmp_path / "external"
    external_directory.mkdir()

    secret_file = external_directory / "secret.txt"
    secret_file.write_text("secret", encoding="utf-8")

    junction = project / "external-link"

    completed = subprocess.run(
        [
            "cmd",
            "/c",
            "mklink",
            "/J",
            str(junction),
            str(external_directory),
        ],
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        pytest.skip("Unable to create a Windows junction")

    result = discover_files(project)

    assert {file.relative_path for file in result} == {
        Path("normal.txt"),
    }


def test_does_not_traverse_symbolic_link_directory(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "normal.txt").write_text("normal", encoding="utf-8")
    external = tmp_path / "external"
    external.mkdir()
    (external / "secret.txt").write_text("secret", encoding="utf-8")

    try:
        (project / "link").symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symbolic links are not available in this environment")

    assert {file.relative_path for file in discover_files(project)} == {
        Path("normal.txt")
    }


def test_rejects_symbolic_link_as_root(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symbolic links are not available in this environment")

    with pytest.raises(ValueError, match="symbolic link"):
        discover_files(link)


def test_prunes_directory_reported_as_symbolic_link(tmp_path: Path, monkeypatch):
    link = tmp_path / "link"
    link.mkdir()
    (link / "secret.txt").write_text("secret", encoding="utf-8")
    original_lstat = os.lstat

    def fake_lstat(path, *args, **kwargs):
        if Path(path) == link:
            return SimpleNamespace(st_mode=stat.S_IFLNK, st_reparse_tag=0)
        return original_lstat(path, *args, **kwargs)

    def fake_walk(directory, *, onerror=None):
        directories = ["link"]
        yield str(directory), directories, []
        if "link" in directories:
            yield str(link), [], ["secret.txt"]

    monkeypatch.setattr("releasekit.discovery.os.lstat", fake_lstat)
    monkeypatch.setattr("releasekit.discovery.os.walk", fake_walk)

    assert discover_files(tmp_path) == []


def test_rejects_root_reported_as_symbolic_link(tmp_path: Path, monkeypatch):
    original_lstat = os.lstat

    def fake_lstat(path, *args, **kwargs):
        if Path(path) == tmp_path:
            return SimpleNamespace(st_mode=stat.S_IFLNK, st_reparse_tag=0)
        return original_lstat(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr("releasekit.discovery.os.lstat", fake_lstat)
        with pytest.raises(ValueError, match="symbolic link"):
            discover_files(tmp_path)


def test_propagates_permission_error_inspecting_root(tmp_path: Path, monkeypatch):
    error = PermissionError(13, "Permission denied", str(tmp_path))
    original_lstat = os.lstat

    def fake_lstat(path, *args, **kwargs):
        if Path(path) == tmp_path:
            raise error
        return original_lstat(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr("releasekit.discovery.os.lstat", fake_lstat)
        with pytest.raises(PermissionError) as raised:
            discover_files(tmp_path)

    assert raised.value is error
    assert raised.value.filename == str(tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="Windows junctions only")
def test_rejects_root_reported_as_windows_junction(tmp_path: Path, monkeypatch):
    original_lstat = os.lstat

    def fake_lstat(path, *args, **kwargs):
        if Path(path) == tmp_path:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR,
                st_reparse_tag=stat.IO_REPARSE_TAG_MOUNT_POINT,
            )
        return original_lstat(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr("releasekit.discovery.os.lstat", fake_lstat)
        with pytest.raises(ValueError, match="junction"):
            discover_files(tmp_path)
