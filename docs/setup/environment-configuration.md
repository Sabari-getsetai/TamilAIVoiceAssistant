# Environment Configuration Guide - Tamil AI Voice Assistant

This guide covers the comprehensive environment-based configuration system implemented for secure, flexible deployment across different environments.

## Overview

The Tamil AI Voice Assistant uses environment variables for all configuration, enabling:
- **Zero hardcoded credentials** in source code
- **Automatic environment detection** (Docker vs local development)
- **Secure credential management** for production deployments
- **Flexible service configuration** without code changes

## Environment Files

### `.env` - Runtime Configuration

Create `.env` in the project root with your specific values:

```bash
# Copy template and customize
cp .env.example .env
# Edit .env with your configuration
```

### `.env.example` - Configuration Template

The `.env.example` file provides comprehensive documentation for all available environment variables, organized by service category.

## Service Configuration

### Database Configuration

**PostgreSQL with pgVector support:**

```bash
# Full database URL (recommended)
DATABASE_URL=postgresql+asyncpg://tamil_user:secure_password@localhost:5432/tamil_assistant

# Or individual components (auto-constructed)
POSTGRES_USER=tamil_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=tamil_assistant
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Additional settings
DATABASE_ECHO=false  # Set to true for SQL query logging
```

**Docker vs Local Detection:**
- **Docker**: Uses `postgres:5432` (service name)
- **Local**: Uses `localhost:5432` (localhost)
- **Auto-detection**: Based on `/.dockerenv` file presence

### Redis Configuration

**Session and cache management:**

```bash
# Full Redis URL (recommended)
REDIS_URL=redis://:redis_password@localhost:6379/0

# Or individual components (auto-constructed)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password
REDIS_DB=0

# Connection settings
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=5
```

**Docker vs Local Detection:**
- **Docker**: Uses `redis:6379` (service name)
- **Local**: Uses `localhost:6379` (localhost)

### MinIO Storage Configuration

**Object storage for files and documents:**

```bash
# MinIO endpoint
MINIO_ENDPOINT=localhost:9000

# Credentials (supports both formats)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
# OR
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Bucket configuration
MINIO_BUCKET_DOCUMENTS=documents
MINIO_BUCKET_AUDIO=audio-files
MINIO_BUCKET_MODELS=ai-models

# Connection settings
MINIO_SECURE=false  # Set to true for HTTPS
```

**Docker vs Local Detection:**
- **Docker**: Uses `minio:9000` (service name)
- **Local**: Uses `localhost:9000` (localhost)

### JWT Authentication

**Secure token management with organization context:**

```bash
# JWT secret key (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# Token expiration
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Algorithm
JWT_ALGORITHM=HS256

# Organization context in tokens
JWT_INCLUDE_ORGANIZATION_CONTEXT=true
JWT_ORGANIZATION_CLAIM_KEY=org_id
```

### Organization Platform Configuration

**Multi-tenant organization platform settings:**

```bash
# Organization platform features
ENABLE_ORGANIZATION_PLATFORM=true
ENABLE_ORGANIZATION_REGISTRATION=true
ENABLE_ORGANIZATION_INVITATIONS=true
REQUIRE_ORGANIZATION_MEMBERSHIP=true  # Users must belong to an organization

# Organization creation and validation
ENABLE_EMAIL_VERIFICATION_FOR_ORG_CREATION=true
ORGANIZATION_NAME_MIN_LENGTH=3
ORGANIZATION_NAME_MAX_LENGTH=100
ORGANIZATION_NAME_UNIQUE_GLOBALLY=true
ORGANIZATION_DESCRIPTION_MAX_LENGTH=500

# Organization limits and quotas
DEFAULT_ORGANIZATION_USER_LIMIT=50
DEFAULT_ORGANIZATION_STORAGE_LIMIT_GB=10
DEFAULT_ORGANIZATION_API_RATE_LIMIT=1000
MAX_ORGANIZATIONS_PER_USER=10

# Organization invitation settings
ORGANIZATION_INVITATION_EXPIRE_DAYS=7
ORGANIZATION_INVITATION_EMAIL_FROM=noreply@tamilai.com
ORGANIZATION_INVITATION_BASE_URL=https://app.tamilai.com
ORGANIZATION_INVITATION_CODE_LENGTH=32

# Organization ownership and roles
AUTO_ASSIGN_CREATOR_AS_OWNER=true
ALLOW_MULTIPLE_OWNERS=false
DEFAULT_MEMBER_ROLE=member
AVAILABLE_ROLES=owner,admin,member

# Multi-tenant database isolation
ENABLE_ORGANIZATION_DATA_ISOLATION=true
ORGANIZATION_SCHEMA_PREFIX=org_
ORGANIZATION_CONTEXT_REQUIRED=true

# Organization features and permissions
ORGANIZATION_FEATURES_CHAT=true
ORGANIZATION_FEATURES_VOICE=true
ORGANIZATION_FEATURES_DOCUMENTS=true
ORGANIZATION_FEATURES_ANALYTICS=true
ORGANIZATION_FEATURES_API_ACCESS=false
```

### Email Configuration

**Email service for organization invitations, OTP verification, and notifications:**

```bash
# SMTP configuration for organization emails
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# Email verification and OTP settings
ENABLE_EMAIL_VERIFICATION=true
OTP_EXPIRATION_MINUTES=10
OTP_LENGTH=6
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_MINUTES=2

# Email templates
EMAIL_TEMPLATE_DIR=backend/templates/email
ORGANIZATION_INVITATION_TEMPLATE=organization_invitation.html
ORGANIZATION_WELCOME_TEMPLATE=organization_welcome.html
EMAIL_VERIFICATION_TEMPLATE=email_verification.html
OTP_VERIFICATION_TEMPLATE=otp_verification.html

# Email sending settings
EMAIL_SEND_TIMEOUT=30
EMAIL_MAX_RETRIES=3
EMAIL_FROM_NAME=Tamil AI Voice Assistant
EMAIL_FROM_ADDRESS=noreply@tamilai.com

# Email service provider settings (choose one)
# Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true

# SendGrid SMTP
# SMTP_HOST=smtp.sendgrid.net
# SMTP_PORT=587
# SMTP_USERNAME=apikey
# SMTP_PASSWORD=your-sendgrid-api-key

# AWS SES SMTP
# SMTP_HOST=email-smtp.us-east-1.amazonaws.com
# SMTP_PORT=587
# SMTP_USERNAME=your-ses-access-key
# SMTP_PASSWORD=your-ses-secret-key
```

### LLM Configuration

**Language model backend selection:**

```bash
# Backend selection
USE_LOCAL_LLM=true  # true=Ollama, false=HuggingFace

# Ollama configuration (when USE_LOCAL_LLM=true)
OLLAMA_BASE_URL=http://localhost:11435
LLM_MODEL_NAME=sarvam-2b-v0.5

# HuggingFace configuration (when USE_LOCAL_LLM=false)
HF_TOKEN=hf_your_token_here
HF_MODEL_NAME=akdiwahar/KavithaSaaram-2b-it
```

### Speech Services

**Text-to-Speech configuration:**

```bash
# Google Cloud TTS (premium)
USE_GOOGLE_CLOUD_TTS=true
TTS_MODEL_NAME=ta-IN-Chirp3-HD-Callirrhoe
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GOOGLE_CLOUD_PROJECT_ID=your-project-id

# TTS customization
TTS_SPEAKING_RATE=1.10
TTS_PITCH=0.0
TTS_VOLUME_GAIN_DB=0.0

# Noise reduction
ENABLE_NOISE_REDUCTION=true
NOISE_REDUCTION_STRENGTH=0.6
```

## Environment Detection

The system automatically detects the runtime environment and adjusts configuration accordingly.

### Docker Environment Detection

**Detection Method:**
```python
import os
from pathlib import Path

IS_DOCKER = Path("/.dockerenv").exists()
```

**Configuration Adjustments:**

| Service | Docker | Local |
|---------|--------|-------|
| Database | `postgres:5432` | `localhost:5432` |
| Redis | `redis:6379` | `localhost:6379` |
| MinIO | `minio:9000` | `localhost:9000` |
| Ollama | `ollama:11434` | `localhost:11435` |

### Intelligent Fallback Logic

**Database URL Construction:**
```python
if DATABASE_URL:
    # Use provided URL directly
    url = DATABASE_URL
else:
    # Construct from components
    host = "postgres" if IS_DOCKER else "localhost"
    url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
```

**Redis URL Construction:**
```python
if REDIS_URL:
    # Use provided URL directly
    url = REDIS_URL
else:
    # Construct from components
    host = "redis" if IS_DOCKER else "localhost"
    url = f"redis://:{password}@{host}:{port}/{db}"
```

## Configuration Examples

### Development Environment

**Local development with Docker services:**

```bash
# .env for local development
DATABASE_URL=postgresql+asyncpg://tamil_user:dev_password@localhost:5432/tamil_assistant_dev
REDIS_URL=redis://:dev_password@localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://localhost:11435

USE_GOOGLE_CLOUD_TTS=false  # Use free gTTS for development
JWT_SECRET_KEY=dev-secret-key-not-for-production

# Organization platform (development)
ENABLE_ORGANIZATION_PLATFORM=true
ENABLE_ORGANIZATION_REGISTRATION=true
ENABLE_ORGANIZATION_INVITATIONS=false  # Disable email for dev
REQUIRE_ORGANIZATION_MEMBERSHIP=true
ENABLE_EMAIL_VERIFICATION_FOR_ORG_CREATION=false  # Skip email verification in dev
DEFAULT_ORGANIZATION_USER_LIMIT=10
DEFAULT_ORGANIZATION_STORAGE_LIMIT_GB=1
ORGANIZATION_INVITATION_BASE_URL=http://localhost:3000
ORGANIZATION_NAME_UNIQUE_GLOBALLY=true
AUTO_ASSIGN_CREATOR_AS_OWNER=true

# Email settings (development - use console backend)
ENABLE_EMAIL_VERIFICATION=false
EMAIL_BACKEND=console  # Print emails to console instead of sending
SMTP_HOST=localhost
SMTP_PORT=1025  # MailHog for local email testing
OTP_EXPIRATION_MINUTES=10
```

### Docker Compose Environment

**Full containerized stack:**

```bash
# .env for Docker Compose
DATABASE_URL=postgresql+asyncpg://tamil_user:docker_password@postgres:5432/tamil_assistant
REDIS_URL=redis://:docker_password@redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://ollama:11434

USE_GOOGLE_CLOUD_TTS=true
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-key.json
JWT_SECRET_KEY=secure-production-jwt-key
```

### Production Environment

**Production deployment with external services:**

```bash
# .env for production
DATABASE_URL=postgresql+asyncpg://tamil_user:prod_password@db.example.com:5432/tamil_assistant
REDIS_URL=redis://:prod_password@cache.example.com:6379/0
MINIO_ENDPOINT=storage.example.com:9000
MINIO_ACCESS_KEY=prod_access_key
MINIO_SECRET_KEY=prod_secret_key

USE_LOCAL_LLM=false  # Use HuggingFace for scalability
HF_TOKEN=hf_production_token
HF_MODEL_NAME=akdiwahar/KavithaSaaram-2b-it

USE_GOOGLE_CLOUD_TTS=true
GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/gcp-service-account.json
JWT_SECRET_KEY=super-secure-production-jwt-key-32-chars

# Organization platform (production)
ENABLE_ORGANIZATION_PLATFORM=true
ENABLE_ORGANIZATION_REGISTRATION=true
ENABLE_ORGANIZATION_INVITATIONS=true
REQUIRE_ORGANIZATION_MEMBERSHIP=true
ENABLE_EMAIL_VERIFICATION_FOR_ORG_CREATION=true
DEFAULT_ORGANIZATION_USER_LIMIT=100
DEFAULT_ORGANIZATION_STORAGE_LIMIT_GB=50
DEFAULT_ORGANIZATION_API_RATE_LIMIT=5000
MAX_ORGANIZATIONS_PER_USER=5
ORGANIZATION_INVITATION_BASE_URL=https://app.tamilai.com
ORGANIZATION_NAME_UNIQUE_GLOBALLY=true
AUTO_ASSIGN_CREATOR_AS_OWNER=true

# Production email configuration
ENABLE_EMAIL_VERIFICATION=true
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true
EMAIL_FROM_NAME=Tamil AI Voice Assistant
EMAIL_FROM_ADDRESS=noreply@tamilai.com
ORGANIZATION_INVITATION_EMAIL_FROM=noreply@tamilai.com

# OTP and email verification settings
OTP_EXPIRATION_MINUTES=10
OTP_LENGTH=6
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_MINUTES=2
EMAIL_SEND_TIMEOUT=30
EMAIL_MAX_RETRIES=3

# Multi-tenant security
ENABLE_ORGANIZATION_DATA_ISOLATION=true
ORGANIZATION_SCHEMA_PREFIX=org_
ORGANIZATION_CONTEXT_REQUIRED=true
JWT_INCLUDE_ORGANIZATION_CONTEXT=true
```

## Security Best Practices

### Credential Management

**DO:**
- ✅ Use strong, unique passwords for each service
- ✅ Generate JWT secrets with `openssl rand -hex 32`
- ✅ Store credentials in `.env` files (not in code)
- ✅ Use different credentials for dev/staging/production
- ✅ Rotate credentials regularly

**DON'T:**
- ❌ Commit `.env` files to version control
- ❌ Use default passwords in production
- ❌ Share credentials in plain text
- ❌ Use the same credentials across environments

### Environment File Security

**File Permissions:**
```bash
# Restrict access to .env file
chmod 600 .env
chown app:app .env  # In production
```

**Git Configuration:**
```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.production" >> .gitignore
```

### Production Secrets Management

**Docker Secrets:**
```yaml
# docker-compose.prod.yml
services:
  backend:
    secrets:
      - db_password
      - jwt_secret
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      JWT_SECRET_KEY_FILE: /run/secrets/jwt_secret

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

**Kubernetes Secrets:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tamil-assistant-secrets
type: Opaque
data:
  database-url: <base64-encoded-url>
  redis-url: <base64-encoded-url>
  jwt-secret: <base64-encoded-secret>
```

## Troubleshooting

### Configuration Issues

**Check environment detection:**
```python
from backend.settings import settings
print(f"Docker environment: {settings.IS_DOCKER}")
print(f"Database URL: {settings.DATABASE_URL}")
print(f"Redis URL: {settings.REDIS_URL}")
```

**Verify service connections:**
```bash
# Test database connection
python -c "
from backend.database.connection import get_db_info
print(get_db_info())
"

# Test Redis connection
python -c "
from backend.cache.redis_client import get_redis_info
print(get_redis_info())
"

# Test MinIO connection
python -c "
from backend.storage.minio_client import get_minio_info
print(get_minio_info())
"
```

### Common Configuration Errors

**Database Connection Failed:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution:** Check `DATABASE_URL` and ensure PostgreSQL is running

**Redis Connection Failed:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```
**Solution:** Check `REDIS_URL` and ensure Redis is running

**MinIO Connection Failed:**
```
minio.error.ServerError: Server not found
```
**Solution:** Check `MINIO_ENDPOINT` and ensure MinIO is running

**JWT Token Invalid:**
```
jose.exceptions.JWTError: Invalid token
```
**Solution:** Check `JWT_SECRET_KEY` is set and consistent across restarts

### Environment Variable Debugging

**List all environment variables:**
```bash
# In container
docker exec tamil-assistant-backend env | grep -E "(DATABASE|REDIS|MINIO|JWT)"

# On host
env | grep -E "(DATABASE|REDIS|MINIO|JWT)"
```

**Check specific variables:**
```python
import os
print("DATABASE_URL:", os.getenv("DATABASE_URL", "NOT SET"))
print("REDIS_URL:", os.getenv("REDIS_URL", "NOT SET"))
print("JWT_SECRET_KEY:", "SET" if os.getenv("JWT_SECRET_KEY") else "NOT SET")
```

## Migration Guide

### From Hardcoded to Environment-Based

**Before (hardcoded):**
```python
DATABASE_URL = "postgresql://user:pass@localhost:5432/db"
REDIS_URL = "redis://localhost:6379/0"
```

**After (environment-based):**
```python
from backend.settings import settings
DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL
```

### Updating Existing Deployments

1. **Create `.env` file** with current configuration
2. **Update environment variables** in deployment scripts
3. **Test configuration** in staging environment
4. **Deploy to production** with new environment setup
5. **Verify all services** connect properly

## Reference

### Complete Environment Variable List

See `.env.example` for the complete, up-to-date list of all available environment variables with detailed documentation.

### Related Documentation

- **[Docker Setup Guide](docker-setup.md)** - Containerized deployment
- **[Getting Started](../getting-started/README.md)** - Initial setup
- **[Troubleshooting](../troubleshooting/)** - Common issues and solutions
- **[Security Guide](../security/)** - Security best practices

### Configuration Files

- **`.env`** - Your runtime configuration (create from template)
- **`.env.example`** - Configuration template with documentation
- **`backend/settings.py`** - Settings schema and validation
- **`docker-compose.dev.yml`** - Docker environment configuration
