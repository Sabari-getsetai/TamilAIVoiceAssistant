"""
Configuration settings for Tamil AI Voice Assistant
"""
from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Docker environment detection
    IS_DOCKER: bool = os.path.exists('/.dockerenv')

    # Project paths (Docker-aware)
    PROJECT_ROOT: Path = Path("/app") if os.path.exists('/.dockerenv') else Path(__file__).parent.parent
    BACKEND_ROOT: Path = PROJECT_ROOT / "backend"
    DATA_ROOT: Path = PROJECT_ROOT / "data"
    MODELS_ROOT: Path = PROJECT_ROOT / "models"

    # Data directories
    DOCS_DIR: Path = DATA_ROOT / "docs"
    FAISS_DIR: Path = DATA_ROOT / "faiss"
    CHUNKS_DIR: Path = DATA_ROOT / "chunks"
    LOGS_DIR: Path = DATA_ROOT / "logs"
    AUDIO_OUT_DIR: Path = DATA_ROOT / "out"

    # Model directories
    LLM_MODEL_DIR: Path = MODELS_ROOT / "llm"
    STT_MODEL_DIR: Path = MODELS_ROOT / "stt"
    TTS_MODEL_DIR: Path = MODELS_ROOT / "tts"

    # Model configuration
    LLM_MODEL_NAME: str = "bloom-560m.q8_0.gguf"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    STT_MODEL_NAME: str = "large-v2"  # Whisper model size

    # TTS Configuration
    USE_GOOGLE_CLOUD_TTS: bool = True  # True for Google Cloud TTS, False for gTTS fallback
    TTS_MODEL_NAME: str = "ta-IN-Chirp3-HD-Callirrhoe"  # Google Cloud TTS voice name
    # Options:
    # - ta-IN-Chirp3-HD-Callirrhoe (Latest Chirp3 HD, ultra-high quality, natural female)
    # - ta-IN-Chirp3-HD-Achernar (Latest Chirp3 HD, ultra-high quality, alternative female)
    # - ta-IN-Wavenet-B (WaveNet, high-quality female)
    # - ta-IN-Wavenet-A (WaveNet, high-quality male)
    # Fallback: "facebook/mms-tts-tam" for offline MMS TTS

    # Google Cloud TTS settings
    GOOGLE_CLOUD_PROJECT_ID: str = ""  # Set via environment variable
    GOOGLE_APPLICATION_CREDENTIALS: str = ""  # Path to service account JSON file

    # TTS Voice Customization (for Google Cloud TTS)
    # Default values match the voice_comparison reference samples EXACTLY
    TTS_SPEAKING_RATE: float = 1.10  # Speech speed (0.25-4.0) - 1.10 = 10% faster, matches reference with normalization
    TTS_PITCH: float = 0.0  # Voice pitch in semitones (-20 to +20) - NOTE: Chirp3 HD doesn't support pitch
    TTS_VOLUME_GAIN_DB: float = 0.0  # Volume adjustment in dB (-96 to +16, default 0.0 = natural)

    # RAG configuration
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_K: int = 4  # Number of documents to retrieve

    # LLM configuration (optimized for speed)
    LLM_MAX_TOKENS: int = 150  # Reduced from 512 for faster generation
    LLM_TEMPERATURE: float = 0.9  # Higher temp for faster sampling
    LLM_CONTEXT_LENGTH: int = 2048  # Reduced context for speed

    # Conversation settings
    MAX_CONVERSATION_HISTORY: int = 10  # Number of turns to keep
    SESSION_TIMEOUT_MINUTES: int = 30

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://frontend:3000",  # Docker container communication
        "http://localhost:8000",
    ]

    # Ollama settings (Docker-aware)
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://ollama:11434" if os.path.exists('/.dockerenv') else "http://localhost:11435"
    )

    # LLM Backend Configuration
    USE_LOCAL_LLM: bool = True  # True for local Ollama, False for HuggingFace API

    # HuggingFace Inference API settings
    HF_MODEL_NAME: str = os.getenv("HF_MODEL_NAME")  # Tamil instruction-tuned model
    # Alternative models:
    # - "bigscience/bloomz-560m" (Multilingual model with Tamil support)
    # - "sarvamai/sarvam-2b-v0.5" (Indian languages - may not have Inference API)
    # - "google/flan-t5-base" (instruction-tuned)
    # - "microsoft/DialoGPT-small" (smaller, faster)
    HF_TOKEN: str = os.getenv("HF_TOKEN")  # Set via environment variable or .env file

    # Audio settings
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_FORMAT: str = "wav"
    VAD_SILENCE_THRESHOLD: float = 0.5  # Voice Activity Detection threshold
    VAD_SILENCE_DURATION: float = 1.5  # Seconds of silence to detect end of speech (increased from 1.0 for better pause tolerance)
    MIN_AUDIO_DURATION: float = 1.0  # Minimum seconds of audio before allowing stop (prevents stopping on brief noise)

    # Noise Reduction settings
    ENABLE_NOISE_REDUCTION: bool = True  # Enable/disable noise reduction preprocessing
    NOISE_REDUCTION_STRENGTH: float = 0.6  # Reduction strength (0.0-1.0, 0.6 = balanced)
    NOISE_REDUCTION_STATIONARY: bool = False  # False = non-stationary (better quality, slightly slower)
    NOISE_REDUCTION_USE_TORCH: bool = False  # True for GPU acceleration (requires PyTorch)

    # Chat settings
    CHAT_SESSION_TIMEOUT_MINUTES: int = 30
    CHAT_MAX_HISTORY_TURNS: int = 10
    CHAT_DEFAULT_LANGUAGE: str = "ta"
    CHAT_ENABLE_RAG: bool = True
    CHAT_FALLBACK_RESPONSES: List[str] = [
        "மன்னிக்கவும், என்னால் இப்போது பதிலளிக்க முடியவில்லை.",
        "தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
        "தொழில்நுட்ப சிக்கல் காரணமாக சிறிது தாமதம்."
    ]

    # Database Configuration (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://tamil_user:tamil_password_dev@localhost:5432/tamil_assistant"
    POSTGRES_PASSWORD: str = "tamil_password_dev"
    DATABASE_ECHO: bool = False

    # Redis Configuration
    REDIS_URL: str = "redis://:tamil_redis_password_dev@localhost:6379/0"
    REDIS_PASSWORD: str = "tamil_redis_password_dev"

    # MinIO Configuration (Object Storage)
    MINIO_ROOT_USER: str = "tamil_admin"
    MINIO_ROOT_PASSWORD: str = "tamil_minio_password_dev"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "tamil_admin"
    MINIO_SECRET_KEY: str = "tamil_minio_password_dev"
    MINIO_SECURE: bool = False
    MINIO_DOCUMENTS_BUCKET: str = "tamil-assistant-documents"
    MINIO_AUDIO_BUCKET: str = "tamil-assistant-audio"

    # Audio Storage and Retention Configuration
    # Tier-based retention periods (in hours)
    AUDIO_RETENTION_FREE_TIER: int = 24        # 24 hours for free tier
    AUDIO_RETENTION_PRO_TIER: int = 168        # 7 days for pro tier
    AUDIO_RETENTION_ENTERPRISE_TIER: int = 720  # 30 days for enterprise tier

    # Audio debug and monitoring settings
    ENABLE_LOCAL_AUDIO_DEBUG: bool = False     # Save local copies for debugging
    AUDIO_PRESIGNED_URL_EXPIRY_MINUTES: int = 15  # MinIO presigned URL expiration
    ENABLE_AUDIO_METRICS: bool = True          # Enable audio upload/access metrics
    AUDIO_QUALITY_MONITORING: bool = True     # Monitor audio processing quality

    # Audio file size limits (in MB)
    MAX_AUDIO_FILE_SIZE_MB: int = 10          # Maximum single audio file size
    MAX_TOTAL_AUDIO_PER_SESSION_MB: int = 100  # Maximum total audio per session

    # Email/SMTP Configuration
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    FROM_EMAIL: str = "noreply@tamilvoiceassistant.com"
    FROM_NAME: str = "Tamil AI Voice Assistant"
    FRONTEND_URL: str = "http://localhost:3000"

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "tamil_jwt_secret_dev_change_in_production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 15)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7)
    

    # Admin User Seeding Configuration
    # Default admin user credentials for database seeding
    ADMIN_EMAIL: str = "admin@localhost"
    ADMIN_PASSWORD: str = "admin123"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_audio_retention_hours(user_tier: str) -> int:
    """
    Get audio retention period in hours based on user tier.

    Args:
        user_tier: User tier ('FREE', 'PRO', 'ENTERPRISE', or None for anonymous)

    Returns:
        Number of hours to retain audio files
    """
    tier_map = {
        'FREE': settings.AUDIO_RETENTION_FREE_TIER,
        'PRO': settings.AUDIO_RETENTION_PRO_TIER,
        'ENTERPRISE': settings.AUDIO_RETENTION_ENTERPRISE_TIER,
    }
    return tier_map.get(user_tier, settings.AUDIO_RETENTION_FREE_TIER)  # Default to FREE tier


def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        settings.DOCS_DIR,
        settings.FAISS_DIR,
        settings.CHUNKS_DIR,
        settings.LOGS_DIR,
        settings.AUDIO_OUT_DIR,
        settings.LLM_MODEL_DIR,
        settings.STT_MODEL_DIR,
        settings.TTS_MODEL_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Ensure directories exist on import
ensure_directories()
