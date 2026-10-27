
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
