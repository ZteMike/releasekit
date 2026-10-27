from pathlib import Path

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
        import pytest

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

    original_is_symlink = Path.is_symlink

    def fake_is_symlink(path: Path) -> bool:
        if path == symlink_candidate:
            return True

        return original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)

    result = discover_files(project)

    assert [file.relative_path for file in result] == [Path("normal.txt")]