import os
import tempfile
import yt_dlp
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.types import Scope
from pydantic import BaseModel
import aiohttp
from urllib.parse import urlparse
import uvicorn
import subprocess
import whisper
import google.generativeai as genai
from uuid import uuid4
from enum import Enum
import time
from contextlib import asynccontextmanager
import shutil
import logging
import aiofiles
import asyncio
from concurrent.futures import ThreadPoolExecutor
import torch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=2)

# CustomStaticFiles to force correct MIME for .vtt
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        if path.endswith(".vtt"):
            response.headers["Content-Type"] = "text/vtt; charset=utf-8"
        return response

# Global model variables
whisper_model = None
gemini_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global whisper_model, gemini_model
    
    logger.info("Loading Whisper model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    whisper_model = whisper.load_model("tiny", device=device)  # Use tiny model
    logger.info(f"Whisper model loaded on {device}")
    
    logger.info("Initializing Gemini model...")
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBc9LRIzgW7xLsvs1iD0joGCDQc06pfrtw")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    logger.info("Gemini model initialized")
    
    yield
    
    # Clean up
    whisper_model = None
    gemini_model = None
    executor.shutdown()

# Create FastAPI app with lifespan
app = FastAPI(
    title="Video Translation API",
    version="1.0.0",
    lifespan=lifespan
)

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

# Enum for supported languages
class Language(str, Enum):
    English = 'English'
    Mongolian = 'Mongolian'

# Pydantic models
class VideoUrlRequest(BaseModel):
    video_url: str
    source_lang: str
    target_lang: str
    test_mode: bool = False

# Exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": f"An error occurred: {str(exc)}"},
    )

# Check for ffmpeg availability
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("ffmpeg is not installed or not found in PATH")

# Video download functions
async def download_ted_talk(url: str, output_path: str) -> str:
    """Specialized downloader for TED Talks"""
    try:
        ydl_opts = {
            'format': 'best[ext=mp4][height<=480]/best[ext=webm][height<=480]',  # Lower resolution
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.ted.com/',
                'Origin': 'https://www.ted.com',
            },
            'extractor_args': {'ted': {'format': 'high'}},
            'retries': 3,  # Reduced retries
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise Exception("Failed to extract TED Talk info")
            
            for file in os.listdir(output_path):
                if file.endswith(('.mp4', '.webm')):
                    return os.path.join(output_path, file)
            
            raise Exception("Download completed but no video file found")
            
    except Exception as e:
        logger.error(f"TED Talk download failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to download TED Talk: {str(e)}")

async def download_with_ytdlp(url: str, output_path: str) -> str:
    """Download video using yt-dlp"""
    try:
        ydl_opts = {
            'format': 'best[ext=mp4][height<=480]/best[ext=webm][height<=480]',  # Lower resolution
            'outtmpl': os.path.join(output_path, f'video.%(ext)s'),
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': url if 'youtube.com' in url else 'https://www.google.com/',
            },
            'retries': 3,  # Reduced retries
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                }
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
            for file in os.listdir(output_path):
                if file.endswith(('.mp4', '.webm')):
                    return os.path.join(output_path, file)
            
            raise Exception("Download completed but no video file found")
                    
    except Exception as e:
        logger.error(f"yt-dlp download failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to download video: {str(e)}")

async def smart_video_download(url: str, output_path: str) -> str:
    """Smart download with fallbacks"""
    logger.info(f"Starting download for: {url}")
    
    if 'ted.com' in url.lower():
        try:
            logger.info("Detected TED Talk, using specialized downloader")
            return await download_ted_talk(url, output_path)
        except Exception as e:
            logger.warning(f"TED Talk download failed, falling back to generic method: {e}")
    
    return await download_with_ytdlp(url, output_path)

# Audio processing functions
def extract_audio(video_path: str, audio_path: str):
    """Extract audio using ffmpeg with stream copy"""
    check_ffmpeg()
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-c:a", "copy", audio_path  # Stream copy
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        logger.error(f"ffmpeg audio extraction failed: {result.stderr.decode()}")
        # Fallback to re-encoding if stream copy fails
        cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "mp3", "-ab", "128k", audio_path]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr.decode()}")

def seconds_to_vtt_timestamp(seconds: float) -> str:
    """Convert seconds to VTT timestamp"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"

def generate_vtt(segments) -> str:
    """Generate VTT content"""
    lines = ["WEBVTT\n"]
    for i, seg in enumerate(segments, 1):
        start = seconds_to_vtt_timestamp(seg['start'])
        end = seconds_to_vtt_timestamp(seg['end'])
        text = seg['text'].strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)

async def translate_with_gemini(segments: list, target_lang: str) -> list:
    """Batch translate segments using Gemini API"""
    if target_lang not in [lang.value for lang in Language]:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {target_lang}")
    
    try:
        # Combine segments into a single prompt
        text = "\n".join([f"{i+1}. {seg['text']}" for i, seg in enumerate(segments)])
        prompt = f"Translate the following numbered texts to {target_lang} accurately while preserving the original meaning, context, and conversational tone. Return the translations in the same numbered format:\n\n{text}"
        response = gemini_model.generate_content(prompt)
        translated_texts = response.text.strip().split("\n")
        
        # Parse numbered translations
        translated_segments = []
        for line in translated_texts:
            if line.strip() and line[0].isdigit():
                try:
                    idx = int(line.split(".", 1)[0]) - 1
                    translated_text = line.split(".", 1)[1].strip()
                    translated_segments.append({
                        'start': segments[idx]['start'],
                        'end': segments[idx]['end'],
                        'text': translated_text
                    })
                except (IndexError, ValueError) as e:
                    logger.warning(f"Failed to parse translation for line '{line}': {e}")
                    translated_segments.append(segments[idx])
        
        # Ensure all segments are translated
        while len(translated_segments) < len(segments):
            idx = len(translated_segments)
            logger.warning(f"Missing translation for segment {idx+1}: {segments[idx]['text']}")
            translated_segments.append({
                'start': segments[idx]['start'],
                'end': segments[idx]['end'],
                'text': f"[Untranslated: {segments[idx]['text']}]"
            })
        
        return translated_segments
    except Exception as e:
        logger.error(f"Gemini batch translation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch translation failed: {str(e)}")

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Video Translation API is running", "status": "healthy"}

@app.get("/test")
async def test():
    return {"message": "API is working", "endpoints": ["/analyze", "/analyze-url"]}

@app.post("/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...)
):
    """Handle file upload and processing"""
    if source_lang not in [lang.value for lang in Language] or target_lang not in [lang.value for lang in Language]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: source_lang={source_lang}, target_lang={target_lang}")
    
    try:
        start_time = time.time()
        
        # Generate unique filenames
        extension = os.path.splitext(file.filename)[1]
        base_filename = str(uuid4())
        video_path = os.path.join("static", f"{base_filename}{extension}")

        # Save uploaded video asynchronously
        async with aiofiles.open(video_path, "wb") as f:
            contents = await file.read()
            await f.write(contents)

        # Process the video
        return await process_video_file(video_path, source_lang, target_lang, start_time)
        
    except Exception as e:
        logger.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@app.post("/analyze-url")
async def analyze_url(request: VideoUrlRequest):
    """Handle URL analysis with video download"""
    if request.source_lang not in [lang.value for lang in Language] or request.target_lang not in [lang.value for lang in Language]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: source_lang={request.source_lang}, target_lang={request.target_lang}")
    
    try:
        start_time = time.time()
        
        if request.test_mode:
            return {
                "status": "success",
                "message": "Test mode - video processing simulation",
                "video_url": "/static/test_video.mp4",
                "original_vtt_url": "/static/test_original.vtt",
                "translated_vtt_url": "/static/test_translated.vtt"
            }
        
        if not request.video_url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Create temporary directory for downloads
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {temp_dir}")
        
        try:
            # Download the video
            logger.info("Starting video download...")
            video_path = await smart_video_download(request.video_url, temp_dir)
            
            if not os.path.exists(video_path):
                raise HTTPException(status_code=400, detail="Video download failed - file not found")
                
            # Move to static directory
            base_filename = str(uuid4())
            static_video_path = os.path.join("static", f"{base_filename}{os.path.splitext(video_path)[1]}")
            os.rename(video_path, static_video_path)
            video_path = static_video_path
            
            # Process the video
            result = await process_video_file(video_path, request.source_lang, request.target_lang, start_time)
            
            return result
            
        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request handling error: {str(e)}")
        error_msg = f"Processing failed: {str(e)}"
        if "403" in str(e) or "Forbidden" in str(e):
            error_msg += ". The video platform may be blocking downloads. Try uploading the file directly."
        raise HTTPException(status_code=500, detail=error_msg)

async def process_video_file(video_path: str, source_lang: str, target_lang: str, start_time: float):
    """Process video file with transcription and translation"""
    try:
        base_filename = os.path.splitext(os.path.basename(video_path))[0]
        
        logger.info("Extracting audio...")
        audio_path = os.path.join("static", f"{base_filename}.mp3")
        await asyncio.get_event_loop().run_in_executor(executor, lambda: extract_audio(video_path, audio_path))

        logger.info("Starting transcription...")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, lambda: whisper_model.transcribe(audio_path))
        segments = result["segments"]
        logger.info(f"Transcription completed in {time.time() - start_time:.2f} seconds")

        logger.info("Generating subtitles...")
        original_vtt = generate_vtt(segments)
        original_vtt_path = os.path.join("static", f"{base_filename}_original.vtt")
        async with aiofiles.open(original_vtt_path, "w", encoding="utf-8") as f:
            await f.write(original_vtt)

        if source_lang != target_lang:
            logger.info("Starting translation...")
            translated_segments = await translate_with_gemini(segments, target_lang)
        else:
            translated_segments = segments

        translated_vtt = generate_vtt(translated_segments)
        translated_vtt_path = os.path.join("static", f"{base_filename}_translated.vtt")
        async with aiofiles.open(translated_vtt_path, "w", encoding="utf-8") as f:
            await f.write(translated_vtt)

        # Clean up
        os.remove(audio_path)

        return {
            "status": "success",
            "video_url": f"/static/{os.path.basename(video_path)}",
            "original_vtt_url": f"/static/{os.path.basename(original_vtt_path)}",
            "translated_vtt_url": f"/static/{os.path.basename(translated_vtt_path)}",
            "message": "Processing completed successfully",
            "processing_time": f"{time.time() - start_time:.2f} seconds"
        }

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {str(e)}"
        )

@app.get("/languages")
async def get_languages():
    """List supported languages"""
    return {"languages": [lang.value for lang in Language]}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Video Translation API is running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    logger.info("Starting Video Translation API...")
    logger.info("Available endpoints:")
    logger.info("  GET  / - Root endpoint")
    logger.info("  GET  /test - Test endpoint")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /languages - List supported languages")
    logger.info("  POST /analyze - File upload analysis")
    logger.info("  POST /analyze-url - URL analysis")
    logger.info("\nServer starting on http://0.0.0.0:8000")
    
    uvicorn.run(
        "test:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=300
    )