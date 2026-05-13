from fastapi import UploadFile, HTTPException
import uuid
import os
from PIL import Image
from io import BytesIO

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
BASE_UPLOAD_DIR = r"E:\repos\mealmaster_backend\uploads"

async def validate_image(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=403, detail="Invalid file type")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=403, detail="File too large")

    return contents

def generate_filename(extension: str):
    return f"{uuid.uuid4()}.{extension}"

def process_image(contents: bytes):
    image = Image.open(BytesIO(contents))

    # Convert to RGB (important for PNG/WebP → JPG)
    image = image.convert("RGB")

    # Resize (max 512x512 for profile pics)
    image.thumbnail((512, 512))

    output = BytesIO()
    image.save(output, format="JPEG", quality=85)  # compression

    output.seek(0)
    return output

def save_image(file_data, filename, upload_dir: str):
    path = os.path.join(os.path.join(BASE_UPLOAD_DIR, upload_dir), filename)

    with open(path, "wb") as f:
        f.write(file_data.read())

    return path