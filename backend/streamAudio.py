from pathlib import Path
from typing import Optional
from fastapi import HTTPException
import mimetypes

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = Path(__file__).resolve().parent
CURRENT_TRACK: Optional[dict] = None 

ALLOWED_AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"
}
ALLOWED_AUDIO_MIME_PREFIXES = ("audio/",)

def validate_audio_file(track_file: Path) -> None:
    # 1) Extension allowlist
    ext = track_file.suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported audio type: {ext or 'none'}")

    # 2) MIME sanity check (defense-in-depth)
    mime_type, _ = mimetypes.guess_type(track_file.name)
    if mime_type is None or not mime_type.startswith(ALLOWED_AUDIO_MIME_PREFIXES):
        raise HTTPException(status_code=415, detail="File is not a supported audio MIME type")
    
def resolve_track_path(track_path: str) -> Path:
    candidate = Path(track_path)
    if candidate.is_absolute():
        return candidate
    project_candidate = (PROJECT_ROOT / candidate).resolve()
    if project_candidate.exists():
        return project_candidate
    return (BACKEND_ROOT / candidate).resolve()

def parse_byte_range(range_header: str, file_size: int) -> tuple[int, int]:
    if not range_header.startswith("bytes="):
        raise HTTPException(status_code=416, detail="Invalid range unit")

    ranges = range_header.replace("bytes=", "", 1).split(",", 1)[0].strip()
    if "-" not in ranges:
        raise HTTPException(status_code=416, detail="Invalid range format")

    start_str, end_str = ranges.split("-", 1)
    if start_str == "":
        try:
            suffix = int(end_str)
        except ValueError as exc:
            raise HTTPException(status_code=416, detail="Invalid suffix range") from exc
        if suffix <= 0:
            raise HTTPException(status_code=416, detail="Invalid suffix range")
        start = max(file_size - suffix, 0)
        end = file_size - 1
        return start, end

    try:
        start = int(start_str)
    except ValueError as exc:
        raise HTTPException(status_code=416, detail="Invalid range start") from exc

    if end_str == "":
        end = file_size - 1
    else:
        try:
            end = int(end_str)
        except ValueError as exc:
            raise HTTPException(status_code=416, detail="Invalid range end") from exc

    if start < 0 or end < start or start >= file_size:
        raise HTTPException(status_code=416, detail="Range not satisfiable")

    return start, min(end, file_size - 1)