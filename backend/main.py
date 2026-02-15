#from djmixer.Core.PlaySongs import PlaySongsAlt
from datetime import datetime, timezone
from pathlib import Path
import mimetypes
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import Response, StreamingResponse
from extractTrackMetaData import _extract_track_metadata
from streamAudio import validate_audio_file,resolve_track_path, parse_byte_range

app = FastAPI()

origins = [
    "http://localhost:3000", # vue3 app
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

class Command(BaseModel):
    ip_address: str
    component: str
    command: str
    data_type: str
    payload: int = None

class PlayRequest(BaseModel):
    path: str

@app.post("/api/toggle-shuffle")
def toggle_shuffle(command: Command):
    try:
        if command.payload == None:
            raise HTTPException(status_code=400, detail="Payload is required")
        
        response = {
            "message":
            "request acknowledge:\n"
            f"IP Address: {command.ip_address}\n"
            f"Component: {command.component}\n"
            f"Command: {command.command}\n"
            f"Data Type: {command.data_type}\n"
            f"Payload: {str(command.payload)}"
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/play")
def play(payload: PlayRequest):
    global CURRENT_TRACK

    if not payload.path:
        raise HTTPException(status_code=400, detail="path is required")

    track_file = resolve_track_path(payload.path)
    if not track_file.exists() or not track_file.is_file():
        raise HTTPException(status_code=404, detail="Track not found")

    validate_audio_file(track_file)
    metadata = _extract_track_metadata(track_file)
    CURRENT_TRACK = {
        "path": payload.path,
        "absolute_path": str(track_file),
        "title": metadata["title"],
        "artist": metadata["artist"],
        "cover_data": metadata["cover_data"],
        "cover_mime": metadata["cover_mime"],
        "startedAt": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "ok": True,
        "currentTrack": {
            "path": CURRENT_TRACK["path"],
            "title": CURRENT_TRACK["title"],
            "artist": CURRENT_TRACK["artist"],
            "coverUrl": "/api/audio/current/cover" if CURRENT_TRACK["cover_data"] else None,
        },
        "streamUrl": "/api/audio/current",
        "startedAt": CURRENT_TRACK["startedAt"],
    }

@app.get("/api/audio/current")
def stream_current_audio(request: Request):
    global CURRENT_TRACK

    if CURRENT_TRACK is None:
        raise HTTPException(status_code=404, detail="No current track selected")

    track_file = Path(CURRENT_TRACK["absolute_path"])
    if not track_file.exists() or not track_file.is_file():
        CURRENT_TRACK = None
        raise HTTPException(status_code=410, detail="Current track no longer exists")

    file_size = track_file.stat().st_size
    content_type = mimetypes.guess_type(track_file.name)[0] or "application/octet-stream"
    range_header = request.headers.get("range")

    start = 0
    end = file_size - 1
    status_code = 200 # whole file, all bytes are stream
    headers = {"Accept-Ranges": "bytes"}

    if range_header:
        start, end = parse_byte_range(range_header, file_size)
        status_code = 206 # return only that part of the file
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    content_length = end - start + 1
    headers["Content-Length"] = str(content_length)

    def file_iterator():
        chunk_size = 1024 * 1024
        with track_file.open("rb") as f:
            f.seek(start)
            remaining = content_length
            while remaining > 0:
                read_size = min(chunk_size, remaining)
                chunk = f.read(read_size)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    return StreamingResponse(
        file_iterator(),
        status_code=status_code,
        media_type=content_type,
        headers=headers,
    )


@app.get("/api/audio/current/cover")
def current_track_cover():
    if CURRENT_TRACK is None:
        raise HTTPException(status_code=404, detail="No current track selected")

    cover_data = CURRENT_TRACK.get("cover_data")
    if not cover_data:
        raise HTTPException(status_code=404, detail="No cover art available for current track")

    return Response(
        content=cover_data,
        media_type=CURRENT_TRACK.get("cover_mime") or "application/octet-stream",
    )

@app.get("/api/player/status")
def player_status():
    if CURRENT_TRACK is None:
        return {"state": "idle", "currentTrack": None}

    return {
        "state": "playing",
        "currentTrack": {
            "path": CURRENT_TRACK["path"],
            "title": CURRENT_TRACK["title"],
            "artist": CURRENT_TRACK["artist"],
            "coverUrl": "/api/audio/current/cover" if CURRENT_TRACK.get("cover_data") else None,
        },
        "startedAt": CURRENT_TRACK["startedAt"],
    }