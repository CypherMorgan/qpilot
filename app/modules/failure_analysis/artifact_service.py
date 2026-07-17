"""Artifact service — file upload, storage, and content extraction.

Handles saving uploaded files to disk, reading their contents
for AI prompt context, and cleaning up when sessions are deleted.

Supported artifact types:
- **Text files**: JSON, plain text, Markdown, HTML, YAML, CSV, log files
- **Images**: PNG, JPG, GIF, WebP (stored for reference; passed as base64 to vision-capable providers)
"""

from __future__ import annotations

import base64
import contextlib
import mimetypes
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel, Field
from structlog import get_logger

# ── Constants ──────────────────────────────────────────────────

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB default (overridden by config)

TEXT_EXTENSIONS: set[str] = {
    ".json", ".txt", ".md", ".html", ".htm", ".xml", ".yaml", ".yml",
    ".csv", ".log", ".env", ".cfg", ".ini", ".conf", ".toml",
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".sh", ".bash", ".ps1", ".bat", ".sql",
}

IMAGE_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg",
}

_logger = get_logger(__name__)


# ── Data models ────────────────────────────────────────────────


class ArtifactMeta(BaseModel):
    """Metadata for a single uploaded artifact file."""

    filename: str = Field(description="Original filename.")
    file_type: str = Field(
        description="Artifact type: 'text', 'image', or 'other'.",
    )
    mime_type: str = Field(default="", description="Detected MIME type.")
    file_size: int = Field(default=0, description="File size in bytes.")
    storage_path: str = Field(description="Relative path under artifacts directory.")
    content_preview: str = Field(
        default="",
        description="First 500 characters for text files, empty for images.",
    )


# ── Helpers ────────────────────────────────────────────────────


def _detect_file_type(filename: str) -> str:
    """Detect whether a file is text, image, or other based on extension."""
    ext = Path(filename).suffix.lower()
    if ext in TEXT_EXTENSIONS:
        return "text"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    return "other"


def _get_mime_type(filename: str) -> str:
    """Guess MIME type from filename."""
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def _safe_filename(filename: str) -> str:
    """Sanitize a filename to prevent directory traversal."""
    # Keep only the basename, strip any path components
    safe = Path(filename).name
    # Replace potentially problematic characters
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in safe)
    return safe or "untitled"


def _truncate_text(content: str, max_chars: int = 500) -> str:
    """Truncate text to a preview length."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "..."


# ── Public API ─────────────────────────────────────────────────


async def save_artifact(
    upload: UploadFile,
    artifacts_dir: str,
    session_id: UUID,
    max_size: int = MAX_UPLOAD_BYTES,
) -> ArtifactMeta:
    """Save an uploaded file to disk and return its metadata.

    Args:
        upload: The uploaded file from FastAPI.
        artifacts_dir: Root directory for artifact storage.
        session_id: Session UUID (used as subdirectory).
        max_size: Maximum allowed file size in bytes.

    Returns:
        ``ArtifactMeta`` with file metadata.

    Raises:
        ValueError: If the file exceeds the size limit.
    """
    filename = _safe_filename(upload.filename or "untitled")
    file_type = _detect_file_type(filename)
    mime_type = _get_mime_type(filename)

    # Session subdirectory
    session_dir = Path(artifacts_dir) / str(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    # Avoid name collisions (very simple: append a counter)
    dest = session_dir / filename
    counter = 1
    while dest.exists():
        stem = dest.stem
        suffix = dest.suffix
        dest = session_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    content = await upload.read()

    if len(content) > max_size:
        raise ValueError(
            f"File '{filename}' exceeds maximum upload size of "
            f"{max_size // (1024 * 1024)} MB"
            f" ({len(content)} bytes > {max_size} bytes)",
        )

    dest.write_bytes(content)
    storage_path = str(dest.relative_to(artifacts_dir))

    content_preview = ""
    if file_type == "text":
        try:
            text = content.decode("utf-8")
            content_preview = _truncate_text(text)
        except UnicodeDecodeError:
            # Binary-ish text file — store empty preview
            pass

    _logger.info(
        "Artifact saved",
        filename=filename,
        session_id=str(session_id),
        file_type=file_type,
        size=len(content),
        path=storage_path,
    )

    return ArtifactMeta(
        filename=filename,
        file_type=file_type,
        mime_type=mime_type,
        file_size=len(content),
        storage_path=storage_path,
        content_preview=content_preview,
    )


def read_artifact_content(
    artifacts_dir: str,
    storage_path: str,
) -> str:
    """Read the full text content of an artifact file.

    Args:
        artifacts_dir: Root directory for artifact storage.
        storage_path: Relative path (as stored in ``ArtifactMeta.storage_path``).

    Returns:
        The full file contents as a string, or an empty string if not found.
    """
    full_path = Path(artifacts_dir) / storage_path
    if not full_path.is_file():
        _logger.warning("Artifact file not found", path=str(full_path))
        return ""

    try:
        return full_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"[Binary file: {full_path.name}]"


def read_artifact_as_base64(
    artifacts_dir: str,
    storage_path: str,
) -> str | None:
    """Read an image artifact and return as a base64 data URI.

    Args:
        artifacts_dir: Root directory for artifact storage.
        storage_path: Relative path to the artifact file.

    Returns:
        A base64-encoded data URI string for images, or ``None`` for
        non-image files.
    """
    full_path = Path(artifacts_dir) / storage_path
    if not full_path.is_file():
        return None

    ext = full_path.suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        return None

    mime_type = _get_mime_type(full_path.name)
    data = full_path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_artifact_context(
    artifacts_dir: str,
    artifacts: list[ArtifactMeta],
) -> str:
    """Build a text block describing all artifacts for inclusion in the AI prompt.

    For text artifacts, includes the full file content.
    For image artifacts, includes a note that an image is available.
    For other artifacts, lists filename and size only.

    Args:
        artifacts_dir: Root directory for artifact storage.
        artifacts: List of artifact metadata to process.

    Returns:
        A formatted string ready to append to the prompt user message.
    """
    if not artifacts:
        return ""

    sections: list[str] = [
        "\n\n## Uploaded Artifacts\n"
        "The following files were attached to this analysis:\n"
    ]

    for artifact in artifacts:
        header = f"\n### File: `{artifact.filename}`\n"
        header += f"- Type: {artifact.file_type}\n"
        header += f"- Size: {_format_size(artifact.file_size)}\n"

        if artifact.file_type == "text":
            content = read_artifact_content(artifacts_dir, artifact.storage_path)
            if content:
                header += f"\n```\n{content}\n```\n"
        elif artifact.file_type == "image":
            header += "- This is a screenshot/image file that may provide visual context.\n"
            header += "- The filename and metadata are provided above.\n"
        else:
            header += "- Binary file (content not readable as text).\n"

        sections.append(header)

    return "".join(sections)


def delete_artifact_files(artifacts_dir: str, session_id: UUID) -> int:
    """Delete all artifact files for a given session.

    Args:
        artifacts_dir: Root directory for artifact storage.
        session_id: Session UUID whose artifacts to remove.

    Returns:
        Number of files deleted.
    """
    session_dir = Path(artifacts_dir) / str(session_id)
    if not session_dir.is_dir():
        return 0

    deleted = 0
    for file in session_dir.iterdir():
        if file.is_file():
            file.unlink()
            deleted += 1

    # Remove the empty directory
    with contextlib.suppress(OSError):
        session_dir.rmdir()

    _logger.info(
        "Artifact files deleted",
        session_id=str(session_id),
        count=deleted,
    )
    return deleted


def _format_size(size: int) -> str:
    """Format bytes into a human-readable size string."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
