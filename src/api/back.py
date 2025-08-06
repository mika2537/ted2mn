from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope
from starlette.middleware.base import BaseHTTPMiddleware
from enum import Enum
from uuid import uuid4
import os
import subprocess
import whisper
from googletrans import Translator

# File size validation middleware
class FileSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 200 * 1024 * 1024):  # 200MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.headers.get("content-type", "").startswith("multipart/form-data"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size allowed: {self.max_size // (1024*1024)}MB"
                )
        response = await call_next(request)
        return response

# CustomStaticFiles to force correct MIME for .vtt
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        if path.endswith(".vtt"):
            response.headers["Content-Type"] = "text/vtt; charset=utf-8"
        return response

# FastAPI app
app = FastAPI()

# Add file size middleware (200MB limit)
app.add_middleware(FileSizeMiddleware, max_size=200 * 1024 * 1024)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
if not os.path.exists("static"):
    os.makedirs("static")

# Mount with custom static file handler
app.mount("/static", CustomStaticFiles(directory="static"), name="static")

# File validation constants
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
MAX_VIDEO_DURATION = 30 * 60  # 30 minutes in seconds
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}

# Enum for supported languages
class Language(str, Enum):
    English = 'English'
    Mongolian = 'Mongolian'

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file size and type"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

def validate_file_size(file_path: str) -> None:
    """Validate file size after upload"""
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        os.remove(file_path)
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size // (1024*1024)}MB) exceeds maximum allowed size ({MAX_FILE_SIZE // (1024*1024)}MB)"
        )

def get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe"""
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
        return 0.0
    except:
        return 0.0

def validate_video_duration(video_path: str) -> None:
    """Validate video duration (max 30 minutes)"""
    duration = get_video_duration(video_path)
    
    if duration > MAX_VIDEO_DURATION:
        raise HTTPException(
            status_code=400,
            detail=f"Video duration ({duration/60:.1f} minutes) exceeds maximum allowed duration (30 minutes)"
        )

# Extract audio using ffmpeg
def extract_audio(video_path: str, audio_path: str):
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "mp3", "-ar", "16000",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr.decode()}")

def seconds_to_vtt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"

def generate_vtt(segments) -> str:
    lines = ["WEBVTT\n"]
    for i, seg in enumerate(segments, 1):
        start = seconds_to_vtt_timestamp(seg['start'])
        end = seconds_to_vtt_timestamp(seg['end'])
        text = seg['text'].strip()
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)

def burn_subtitles(video_path: str, vtt_path: str, output_path: str):
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"subtitles={vtt_path}",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-strict", "-2",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=1800)  # 30 min timeout
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg subtitle burn failed: {result.stderr.decode()}")

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...)
):
    video_path = None
    audio_path = None
    
    try:
        # Validate file type
        validate_file(file)
        
        # Generate unique filenames
        extension = os.path.splitext(file.filename)[1]
        base_filename = str(uuid4())
        video_path = os.path.join("static", f"{base_filename}{extension}")

        # Save uploaded video
        contents = await file.read()
        with open(video_path, "wb") as f:
            f.write(contents)

        # Validate file size and duration
        validate_file_size(video_path)
        validate_video_duration(video_path)

        # Extract audio
        audio_path = os.path.join("static", f"{base_filename}.mp3")
        extract_audio(video_path, audio_path)

        # Transcribe with appropriate model for longer videos
        model = whisper.load_model("base")  # Better for longer content
        result = model.transcribe(audio_path)
        segments = result["segments"]

        # Save original VTT
        original_vtt = generate_vtt(segments)
        original_vtt_path = os.path.join("static", f"{base_filename}_original.vtt")
        with open(original_vtt_path, "w", encoding="utf-8") as f:
            f.write(original_vtt)

        # Translate segments if needed
        translated_segments = segments.copy()
        if source_lang != target_lang:
            translator = Translator()
            lang_map = {
                "English": "en",
                "Mongolian": "mn"
            }
            src_code = lang_map.get(source_lang, "en")
            tgt_code = lang_map.get(target_lang, "mn")

            # Translate in batches to avoid rate limits
            for segment in translated_segments:
                try:
                    translated = translator.translate(segment['text'], src=src_code, dest=tgt_code)
                    segment['text'] = translated.text
                except Exception as e:
                    print(f"Translation failed for segment: {e}")
                    # Keep original text if translation fails
                    pass

        # Save translated VTT
        translated_vtt = generate_vtt(translated_segments)
        translated_vtt_path = os.path.join("static", f"{base_filename}_translated.vtt")
        with open(translated_vtt_path, "w", encoding="utf-8") as f:
            f.write(translated_vtt)

        # Burn translated subtitles into video
        subtitled_video_path = os.path.join("static", f"{base_filename}_subtitled.mp4")
        burn_subtitles(video_path, translated_vtt_path, subtitled_video_path)

        # Clean up temp files
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        if video_path and os.path.exists(video_path):
            os.remove(video_path)

        return {
            "status": "success",
            "video_url": f"/static/{os.path.basename(subtitled_video_path)}",
            "original_vtt_url": f"/static/{os.path.basename(original_vtt_path)}",
            "translated_vtt_url": f"/static/{os.path.basename(translated_vtt_path)}",
            "message": "Transcription and translation completed. Subtitles burned into video."
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Clean up files on error
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages")
async def get_languages():
    return {"languages": [lang.value for lang in Language]}

@app.get("/health")
async def health_check():
    return {"message": "API is running", "max_file_size_mb": MAX_FILE_SIZE // (1024*1024), "max_duration_minutes": MAX_VIDEO_DURATION // 60}

@app.get("/limits")
async def get_limits():
    return {
        "max_file_size_mb": MAX_FILE_SIZE // (1024*1024),
        "max_duration_minutes": MAX_VIDEO_DURATION // 60,
        "allowed_formats": list(ALLOWED_VIDEO_EXTENSIONS)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("back:app", host="0.0.0.0", port=8000, reload=True)
