"""Test that word exporter correctly handles different backend ports."""

import os
import tempfile
from unittest.mock import patch, MagicMock


def test_word_export_converts_relative_image_urls_with_port_5000():
    """Verify /api/image URLs are converted to absolute with port 5000."""
    from markdown_viewer.exporters.word_exporter import WordExporter

    html_input = '<img src="/api/image?path=%2Ftest%2Fimage.png">'
    expected_output = 'src="http://localhost:5000/api/image'

    exporter = WordExporter()

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        output_path = tmp.name

    try:
        with patch.object(exporter, "_load_html") as mock_load:
            with patch.object(exporter, "_cleanup"):
                # Mock page.content() to return the same HTML
                mock_page = MagicMock()
                mock_page.content.return_value = html_input
                exporter.page = mock_page

                # Mock Document
                with patch("markdown_viewer.exporters.word_exporter.Document"):
                    exporter.export(html_input, "# Test", output_path, backend_port=5000)

                # Check that _load_html was called with converted URL
                loaded_html = mock_load.call_args[0][0]
                assert expected_output in loaded_html
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_word_export_converts_relative_image_urls_with_port_5050():
    """Verify /api/image URLs are converted to absolute with port 5050."""
    from markdown_viewer.exporters.word_exporter import WordExporter

    html_input = '<img src="/api/image?path=%2Ftest%2Fimage.png">'
    expected_output = 'src="http://localhost:5050/api/image'

    exporter = WordExporter()

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        output_path = tmp.name

    try:
        with patch.object(exporter, "_load_html") as mock_load:
            with patch.object(exporter, "_cleanup"):
                mock_page = MagicMock()
                mock_page.content.return_value = html_input
                exporter.page = mock_page

                with patch("markdown_viewer.exporters.word_exporter.Document"):
                    exporter.export(html_input, "# Test", output_path, backend_port=5050)

                loaded_html = mock_load.call_args[0][0]
                assert expected_output in loaded_html
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_word_export_converts_relative_image_urls_with_port_8080():
    """Verify /api/image URLs are converted to absolute with port 8080."""
    from markdown_viewer.exporters.word_exporter import WordExporter

    html_input = """
    <img src="/api/image?path=%2Ftest%2Fimage1.png">
    <img src="/api/image?path=%2Ftest%2Fimage2.jpg">
    """
    expected_output = 'src="http://localhost:8080/api/image'

    exporter = WordExporter()

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        output_path = tmp.name

    try:
        with patch.object(exporter, "_load_html") as mock_load:
            with patch.object(exporter, "_cleanup"):
                mock_page = MagicMock()
                mock_page.content.return_value = html_input
                exporter.page = mock_page

                with patch("markdown_viewer.exporters.word_exporter.Document"):
                    exporter.export(html_input, "# Test", output_path, backend_port=8080)

                loaded_html = mock_load.call_args[0][0]
                # Should have 2 converted URLs
                assert loaded_html.count(expected_output) == 2
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_word_export_defaults_to_port_5000_when_not_provided():
    """Verify default port 5000 is used when backend_port not specified."""
    from markdown_viewer.exporters.word_exporter import WordExporter

    html_input = '<img src="/api/image?path=%2Ftest%2Fimage.png">'
    expected_output = 'src="http://localhost:5000/api/image'

    exporter = WordExporter()

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        output_path = tmp.name

    try:
        with patch.object(exporter, "_load_html") as mock_load:
            with patch.object(exporter, "_cleanup"):
                mock_page = MagicMock()
                mock_page.content.return_value = html_input
                exporter.page = mock_page

                with patch("markdown_viewer.exporters.word_exporter.Document"):
                    # Call without backend_port parameter
                    exporter.export(html_input, "# Test", output_path)

                loaded_html = mock_load.call_args[0][0]
                assert expected_output in loaded_html
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_export_word_route_passes_backend_port_from_environment(app_client):
    """Verify /api/export/word route passes BACKEND_PORT to exporter."""
    from unittest.mock import patch

    # Set custom port in environment
    with patch.dict(os.environ, {"BACKEND_PORT": "5050"}):
        from pathlib import Path as _Path

        captured_port = None

        def fake_export(_html, _markdown, path, backend_port=None):
            nonlocal captured_port
            captured_port = backend_port
            _Path(path).write_bytes(b"PK dummy docx")

        with patch("markdown_viewer.routes.WordExporter") as mock_cls:
            mock_cls.return_value.export.side_effect = fake_export

            response = app_client.post(
                "/api/export/word",
                json={"html": "<p>Hello</p>", "filename": "test.docx"},
            )

        assert response.status_code == 200
        assert captured_port == 5050
