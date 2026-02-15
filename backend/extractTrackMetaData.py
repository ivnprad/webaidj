from typing import Optional
from pathlib import Path

try:
    from mutagen._file import File as MutagenFile
except ImportError:  # pragma: no cover - runtime dependency may be missing locally
    MutagenFile = None

def _read_text_tag(tags, key: str) -> Optional[str]:
    if not tags:
        return None
    value = tags.get(key)
    if not value:
        return None
    if isinstance(value, list):
        item = value[0]
    else:
        item = value
    if isinstance(item, bytes):
        return item.decode("utf-8", errors="ignore").strip() or None
    return str(item).strip() or None

def _detect_image_mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    return "application/octet-stream"

def _extract_track_metadata(track_file: Path) -> dict:
    metadata = {
        "title": track_file.stem,
        "artist": "Unknown Artist",
        "cover_data": None,
        "cover_mime": None,
    }
    if MutagenFile is None:
        print("Mutagen is none")
        return metadata

    try:
        easy_audio = MutagenFile(track_file, easy=True)
        if easy_audio and getattr(easy_audio, "tags", None):
            metadata["title"] = _read_text_tag(easy_audio.tags, "title") or metadata["title"]
            metadata["artist"] = _read_text_tag(easy_audio.tags, "artist") or metadata["artist"]
    except Exception:
        pass

    try:
        full_audio = MutagenFile(track_file)
        tags = getattr(full_audio, "tags", None)
        if not tags:
            return metadata

        cover_bytes = None
        cover_mime = None

        if hasattr(tags, "getall"):
            apic_frames = tags.getall("APIC")
            if apic_frames:
                frame = apic_frames[0]
                cover_bytes = getattr(frame, "data", None)
                cover_mime = getattr(frame, "mime", None)

        if cover_bytes is None and isinstance(tags, dict):
            covr_items = tags.get("covr")
            if covr_items:
                cover_item = covr_items[0]
                cover_bytes = bytes(cover_item)

        if cover_bytes:
            metadata["cover_data"] = cover_bytes
            metadata["cover_mime"] = cover_mime or _detect_image_mime(cover_bytes)
    except Exception:
        pass

    return metadata