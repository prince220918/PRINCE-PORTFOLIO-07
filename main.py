from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import shutil
import re
import httpx
import time
from typing import List, Optional
from supabase import create_client, Client

import models, database, schemas

# Load environment variables
load_dotenv()

# Initialize database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Prince Portfolio Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supabase Client Setup (for production file uploads)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase_client: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Admin passcode for security (can be set via env var, defaults to 'prince123' if not set)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "prince123")

def verify_admin(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    if token != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin passcode",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

# Helper functions to extract IDs
def extract_youtube_id(url: str) -> Optional[str]:
    pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^"&?\/ ]{11})'
    match = re.search(pattern, url, re.IGNORECASE)
    return match.group(1) if match else None

def extract_instagram_code(url: str) -> Optional[str]:
    pattern = r'(?:instagram\.com\/(?:p|reel|tv)\/)([^"&?\/ ]+)'
    match = re.search(pattern, url, re.IGNORECASE)
    return match.group(1) if match else None

async def scrape_instagram_thumbnail(shortcode: str) -> Optional[str]:
    url = f"https://www.instagram.com/reel/{shortcode}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                # Look for og:image
                match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', response.text)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return None

@app.get("/api/videos", response_model=List[schemas.VideoResponse])
def get_videos(db: Session = Depends(database.get_db)):
    return db.query(models.Video).order_by(models.Video.created_at.desc()).all()

@app.post("/api/videos/upload", response_model=schemas.VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    duration: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    admin: bool = Depends(verify_admin)
):
    # Sanitize filename
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
    base, ext = os.path.splitext(filename)

    # Hybrid Upload Approach
    if supabase_client:
        # Production: Upload to Supabase Storage Bucket 'videos'
        unique_filename = f"{base}_{int(time.time())}{ext}"
        try:
            file_bytes = await file.read()
            supabase_client.storage.from_("videos").upload(
                path=unique_filename,
                file=file_bytes,
                file_options={"content-type": file.content_type}
            )
            public_url = supabase_client.storage.from_("videos").get_public_url(unique_filename)
            video_url = public_url
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Supabase upload failed: {str(e)}"
            )
    else:
        # Local Development: Save on Disk
        counter = 1
        file_path = os.path.join(UPLOAD_DIR, filename)
        while os.path.exists(file_path):
            filename = f"{base}_{counter}{ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            counter += 1

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        video_url = f"/uploads/{filename}"

    db_video = models.Video(
        title=title,
        type="local",
        url=video_url,
        duration=duration
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

@app.post("/api/videos/link", response_model=schemas.VideoResponse)
async def add_video_link(
    payload: schemas.VideoLinkCreate,
    db: Session = Depends(database.get_db),
    admin: bool = Depends(verify_admin)
):
    url = payload.url
    yt_id = extract_youtube_id(url)
    insta_code = extract_instagram_code(url)

    if yt_id:
        video_type = "youtube"
        video_url = f"https://www.youtube.com/embed/{yt_id}"
        thumbnail_url = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
    elif insta_code:
        video_type = "instagram"
        video_url = f"https://www.instagram.com/reel/{insta_code}/embed/"
        thumbnail_url = await scrape_instagram_thumbnail(insta_code)
    else:
        raise HTTPException(status_code=400, detail="Invalid video link. Must be a valid YouTube or Instagram URL.")

    db_video = models.Video(
        title=payload.title,
        type=video_type,
        url=video_url,
        duration=payload.duration or "--:--",
        thumbnail_url=thumbnail_url
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

@app.delete("/api/videos/{video_id}")
def delete_video(
    video_id: int,
    db: Session = Depends(database.get_db),
    admin: bool = Depends(verify_admin)
):
    db_video = db.query(models.Video).filter(models.Video.id == video_id).first()
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")

    if db_video.type == "local":
        if supabase_client and db_video.url.startswith("http"):
            # Deleting from Supabase Storage
            try:
                # Extract filename from Supabase public URL
                filename = db_video.url.split("/")[-1]
                supabase_client.storage.from_("videos").remove(filename)
            except Exception:
                pass
        else:
            # Deleting from Local Disk
            filename = db_video.url.replace("/uploads/", "")
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    db.delete(db_video)
    db.commit()
    return {"detail": "Video deleted successfully"}

# Serve uploads directory (statically serve local clips if running locally)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Serve portfolio.html at root route
@app.get("/")
def read_root():
    return FileResponse("portfolio.html")

# Serve admin.html at /prince route
@app.get("/prince")
def read_admin():
    return FileResponse("admin.html")
