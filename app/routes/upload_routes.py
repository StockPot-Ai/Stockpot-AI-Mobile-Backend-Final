import os
import uuid
import base64
from flask import Blueprint, request, send_from_directory
from app.utils.response import success_response, error_response
from app.extensions import get_supabase
from app.config import Config

upload_bp = Blueprint("upload", __name__, url_prefix="/api/upload")

# Directory to save local media uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@upload_bp.route("/image", methods=["POST"])
def upload_image():
    """Accepts base64 or multipart/form-data image, uploads to Supabase Storage or local static folder, and returns a public URL."""
    data = request.get_json(silent=True) or {}
    image_data = data.get("image")
    img_type = data.get("type", "general") # 'avatar', 'recipe', 'store'
    
    unique_id = uuid.uuid4().hex[:12]
    filename = f"{img_type}_{unique_id}.jpg"
    binary_data = None

    if image_data:
        # Base64 string
        try:
            if "," in image_data:
                image_data = image_data.split(",")[1]
            binary_data = base64.b64decode(image_data)
        except Exception as e:
            return error_response(f"Invalid base64 image data: {str(e)}", 400)
    elif "file" in request.files:
        # Multipart form file
        file = request.files["file"]
        if file.filename != "":
            binary_data = file.read()
            if "." in file.filename:
                ext = file.filename.rsplit(".", 1)[1].lower()
                filename = f"{img_type}_{unique_id}.{ext}"

    if not binary_data:
        return error_response("No image provided. Pass 'image' (base64) or 'file' (multipart).", 400)

    # 1. Try uploading to Supabase Storage bucket 'images' or 'avatars'
    supabase = get_supabase()
    if supabase is not None and Config.SUPABASE_URL and Config.SUPABASE_SERVICE_ROLE_KEY:
        bucket_name = "avatars" if img_type == "avatar" else "images"
        try:
            supabase.storage.from_(bucket_name).upload(
                path=filename,
                file=binary_data,
                file_options={"content-type": "image/jpeg", "upsert": "true"}
            )
            public_url = f"{Config.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
            return success_response({
                "url": public_url,
                "filename": filename,
                "storage": "supabase"
            }, 201)
        except Exception:
            pass # fallback to local/hosted static storage

    # 2. Local fallback storage served by Flask
    local_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(local_path, "wb") as f:
        f.write(binary_data)

    # Construct public hosted URL based on request host
    host = request.host_url.rstrip("/")
    public_url = f"{host}/api/upload/file/{filename}"

    return success_response({
        "url": public_url,
        "filename": filename,
        "storage": "local"
    }, 201)


@upload_bp.route("/file/<filename>", methods=["GET"])
def get_uploaded_file(filename):
    """Serve locally uploaded images."""
    return send_from_directory(UPLOAD_FOLDER, filename)
