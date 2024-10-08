from passlib.context import CryptContext

DATABASE = "canvas/canvas.db"

uvicorn_domain = "0.0.0.0"  # Used to start uvicorn locally by running: `python canvas_app.py`
uvicorn_port = 9283

# Private key name: key.pem
# Public key name: cert.pem

NUM_OF_THREADS = 2  # 1 for running locally, (2*cores+1) for running on server

RELOAD = False  # True for development

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 2 * 24 * 60  # 1 day
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days

ALLOWED_EXTENSION = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "mp4",
    "mkv",
    "mov",
    "m4v",
    "avi",
    "wmv",
    "webm",
}  # svg removed to prevent XSS
