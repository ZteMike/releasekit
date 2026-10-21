
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
