# Vision Quick Start Guide

Get up and running with Vision's AI-powered pixel art generation in 5 minutes!

## Prerequisites

- Python 3.11+ installed
- Docker installed (for Redis)
- Anthropic API account

## Step 1: Get Your Anthropic API Key

### Option A: Create New Account

1. Go to https://console.anthropic.com/
2. Sign up for an account
3. Navigate to **Settings** → **API Keys**
4. Click **Create Key**
5. Give it a name (e.g., "Vision Project")
6. Copy the API key (starts with `sk-ant-`)
7. **Important**: Save this key securely - you won't see it again!

### Option B: Use Existing Account

1. Log in to https://console.anthropic.com/
2. Go to **Settings** → **API Keys**
3. Create a new key or use an existing one
4. Copy the key

### Pricing Note

- Claude 3.5 Sonnet: ~$3 per million input tokens, ~$15 per million output tokens
- Typical sprite generation: ~$0.10-0.50 per asset
- You get $5 free credits when you sign up
- See https://www.anthropic.com/pricing for latest pricing

## Step 2: Install Docker (if not already installed)

### macOS

```bash
# Using Homebrew
brew install --cask docker

# Or download from https://www.docker.com/products/docker-desktop/
```

### Linux (Ubuntu/Debian)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### Windows

1. Download Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Install and follow the setup wizard
3. Restart your computer if prompted

### Verify Docker Installation

```bash
docker --version
# Should output: Docker version X.X.X, build XXXXXXX
```

## Step 3: Clone and Set Up the Project

```bash
# Clone the repository
git clone https://github.com/Visecity/Vision.git
cd Vision

# Create and activate virtual environment
python3 -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
.\venv\Scripts\activate

# Install Vision with all dependencies
pip install -e ".[dev]"
```

## Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Open .env in your preferred editor
nano .env  # or: vim .env, code .env, etc.
```

Edit the `.env` file and add your Anthropic API key:

```bash
# Replace 'your_anthropic_api_key_here' with your actual key
ANTHROPIC_API_KEY=sk-ant-api03-...your-actual-key-here...

# Redis settings (defaults work fine)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Keep other settings as-is for now
DEBUG=false
LOG_LEVEL=INFO
```

**Important**: 
- Never commit your `.env` file to Git (it's already in `.gitignore`)
- Keep your API key secret

## Step 5: Start Redis

Redis is used for state management and caching.

```bash
# Start Redis using Docker Compose (from Vision directory)
docker-compose up -d

# Verify Redis is running
docker-compose ps

# You should see:
# NAME                IMAGE          STATUS
# vision-redis-1      redis:7-alpine Up X minutes
```

### Test Redis Connection

```bash
# Test Redis with docker
docker exec -it vision-redis-1 redis-cli ping

# Should output: PONG
```

## Step 6: Test Your Setup

### Test 1: Generate Sample Assets (No API Required)

```bash
# Generate sample assets using the rendering engine
python3 examples/create_sample_assets.py

# Check output
ls -la examples/output/
```

### Test 2: Test Configuration

Create a simple test script:

```bash
cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""Test Vision setup."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🔍 Testing Vision Setup...\n")

# Test 1: Import core modules
print("1️⃣ Testing imports...")
try:
    from src.core.config import get_settings
    from src.rendering import Color, PixelGrid
    from src.llm.client import LLMClient
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Check configuration
print("\n2️⃣ Testing configuration...")
try:
    settings = get_settings()
    if settings.anthropic_api_key and not settings.anthropic_api_key.startswith("your_"):
        print("   ✅ Anthropic API key configured")
    else:
        print("   ⚠️  Anthropic API key not set (add to .env)")
    
    print(f"   ✅ Redis host: {settings.redis_host}:{settings.redis_port}")
    print(f"   ✅ Model: {settings.orchestrator_model}")
except Exception as e:
    print(f"   ❌ Configuration error: {e}")
    sys.exit(1)

# Test 3: Test Redis connection
print("\n3️⃣ Testing Redis connection...")
try:
    import redis
    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
    )
    r.ping()
    print("   ✅ Redis connection successful")
except Exception as e:
    print(f"   ❌ Redis error: {e}")
    print("   💡 Make sure Redis is running: docker-compose up -d")
    sys.exit(1)

# Test 4: Test rendering engine
print("\n4️⃣ Testing rendering engine...")
try:
    grid = PixelGrid(16, 16)
    grid.set_pixel(8, 8, Color(255, 0, 0))
    pixel = grid.get_pixel(8, 8)
    assert pixel.r == 255
    print("   ✅ Rendering engine working")
except Exception as e:
    print(f"   ❌ Rendering error: {e}")
    sys.exit(1)

print("\n✅ All tests passed! Vision is ready to use.\n")
print("Next steps:")
print("  • Run: python3 examples/create_sample_assets.py")
print("  • Try: vision generate 'grass tile' --style stardew")
print("  • Read: docs/CLI_USAGE.md for more commands")
EOF

chmod +x test_setup.py
python3 test_setup.py
```

### Expected Output

```
🔍 Testing Vision Setup...

1️⃣ Testing imports...
   ✅ All imports successful

2️⃣ Testing configuration...
   ✅ Anthropic API key configured
   ✅ Redis host: localhost:6379
   ✅ Model: claude-3-5-sonnet-20241022

3️⃣ Testing Redis connection...
   ✅ Redis connection successful

4️⃣ Testing rendering engine...
   ✅ Rendering engine working

✅ All tests passed! Vision is ready to use.
```

## Step 7: Try It Out!

### Generate Sample Assets (No API required)

```bash
python3 examples/create_sample_assets.py
```

This creates 20+ pixel art assets without using the API.

### Use CLI (API required)

```bash
# Check CLI is working
vision --help

# Generate a simple sprite
vision generate "grass tile" --style stardew --size 16x16

# Check generation status
vision status

# List all generations
vision list
```

## Troubleshooting

### Issue: "ModuleNotFoundError"

```bash
# Make sure you installed Vision and dependencies
pip install -e ".[dev]"
```

### Issue: "Redis connection refused"

```bash
# Check if Redis is running
docker-compose ps

# If not running, start it
docker-compose up -d

# Check Redis logs
docker-compose logs redis
```

### Issue: "Anthropic API key not set"

```bash
# Check your .env file
cat .env | grep ANTHROPIC_API_KEY

# Should show: ANTHROPIC_API_KEY=sk-ant-...

# If not set, edit .env and add your key
nano .env
```

### Issue: "Rate limit exceeded"

```bash
# Anthropic has rate limits. Wait a few seconds and try again.
# Or check your usage at: https://console.anthropic.com/
```

### Issue: Docker not running

```bash
# macOS: Open Docker Desktop application
# Linux: sudo systemctl start docker
# Windows: Start Docker Desktop

# Verify docker is running
docker ps
```

## Stop Redis When Done

```bash
# Stop Redis container
docker-compose down

# Or stop but keep data
docker-compose stop
```

## Next Steps

1. **Read the Documentation**:
   - [`README.md`](README.md) - Project overview
   - [`docs/CLI_USAGE.md`](docs/CLI_USAGE.md) - CLI commands
   - [`docs/RENDERING_GUIDE.md`](docs/RENDERING_GUIDE.md) - Rendering API
   - [`examples/README.md`](examples/README.md) - Example assets

2. **Explore Examples**:
   ```bash
   # Generate sample assets
   python3 examples/create_sample_assets.py
   
   # View output
   open examples/output/
   ```

3. **Try the CLI**:
   ```bash
   # Generate assets with AI
   vision generate "wooden crate" --style stardew
   vision generate "health potion icon" --size 16x16
   vision generate "player idle animation" --frames 4
   ```

4. **Build Your Own**:
   ```python
   from src.rendering import PixelGrid, DrawingContext, Color
   
   grid = PixelGrid(16, 16)
   ctx = DrawingContext(grid)
   ctx.draw_circle(8, 8, 6, Color(255, 0, 0), filled=True)
   ```

## Configuration Options

### Available Models

You can change the AI models in `.env`:

```bash
# Use Claude 3.5 Sonnet (recommended, balanced)
ORCHESTRATOR_MODEL=claude-3-5-sonnet-20241022

# Use Claude 3 Opus (more creative, slower, more expensive)
ORCHESTRATOR_MODEL=claude-3-opus-20240229

# Use Claude 3 Haiku (faster, cheaper, less detailed)
ORCHESTRATOR_MODEL=claude-3-haiku-20240307
```

### Redis Configuration

Advanced Redis settings:

```bash
# Use remote Redis
REDIS_HOST=your-redis-host.com
REDIS_PORT=6379
REDIS_PASSWORD=your-password
REDIS_DB=0

# Or use Redis connection URL
REDIS_URL=redis://user:password@host:port/db
```

### Performance Tuning

```bash
# Increase concurrent agents (more parallelism)
MAX_CONCURRENT_AGENTS=10

# Enable more aggressive caching
ENABLE_CACHING=true
CACHE_TTL=7200  # 2 hours

# Increase timeout for complex generations
TIMEOUT=600  # 10 minutes
```

## Getting Help

- 🐛 **Issues**: https://github.com/Visecity/Vision/issues
- 📚 **Documentation**: See `docs/` directory
- 💬 **Discussions**: https://github.com/Visecity/Vision/discussions

## Security Best Practices

1. **Never commit `.env` file**: It contains your API key
2. **Rotate API keys regularly**: Create new keys periodically
3. **Use environment variables**: Don't hardcode keys in code
4. **Limit API key permissions**: Use read-only keys when possible
5. **Monitor API usage**: Check https://console.anthropic.com/ regularly

---

**You're all set!** 🎉 Start creating amazing pixel art with Vision!