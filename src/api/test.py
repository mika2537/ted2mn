from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope
from enum import Enum
from uuid import uuid4
import os
import subprocess
import whisper
from googletrans import Translator

# ✅ CustomStaticFiles to force correct MIME for .vtt
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        if path.endswith(".vtt"):
            response.headers["Content-Type"] = "text/vtt; charset=utf-8"
        return response

# ✅ FastAPI app
app = FastAPI()

# ✅ CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Ensure static directory exists
if not os.path.exists("static"):
    os.makedirs("static")

# ✅ Mount with custom static file handler

app.mount("/static", CustomStaticFiles(directory="static"), name="static")

# ✅ Enum for supported languages
class Language(str, Enum):
    English = 'English'
    Mongolian = 'Mongolian'

# ✅ Extract audio using ffmpeg
def extract_audio(video_path: str, audio_path: str):
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "mp3", audio_path
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr.decode()}")

def seconds_to_vtt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"  # Use dot, not comma

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
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg subtitle burn failed: {result.stderr.decode()}")

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...)
):
    try:
        # Generate unique filenames
        extension = os.path.splitext(file.filename)[1]
        base_filename = str(uuid4())
        video_path = os.path.join("static", f"{base_filename}{extension}")

        # Save uploaded video
        contents = await file.read()
        with open(video_path, "wb") as f:
            f.write(contents)

        # Extract audio
        audio_path = os.path.join("static", f"{base_filename}.mp3")
        extract_audio(video_path, audio_path)

        # Transcribe
        model = whisper.load_model("small")
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

            for segment in translated_segments:
                translated = translator.translate(segment['text'], src=src_code, dest=tgt_code)
                segment['text'] = translated.text

        # Save translated VTT
        translated_vtt = generate_vtt(translated_segments)
        translated_vtt_path = os.path.join("static", f"{base_filename}_translated.vtt")
        with open(translated_vtt_path, "w", encoding="utf-8") as f:
            f.write(translated_vtt)

        # Burn translated subtitles into video
        subtitled_video_path = os.path.join("static", f"{base_filename}_subtitled.mp4")
        burn_subtitles(video_path, translated_vtt_path, subtitled_video_path)

        # Clean up temp files
        os.remove(audio_path)
        os.remove(video_path)

        return {
            "status": "success",
            "video_url": f"/static/{os.path.basename(subtitled_video_path)}",
            "original_vtt_url": f"/static/{os.path.basename(original_vtt_path)}",
            "translated_vtt_url": f"/static/{os.path.basename(translated_vtt_path)}",
            "message": "Transcription and translation done. Subtitles burned into video."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/languages")
async def get_languages():
    return {"languages": [lang.value for lang in Language]}

@app.get("/url")
async def check_api():
    return {"message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test:app", host="0.0.0.0", port=8000, reload=True)