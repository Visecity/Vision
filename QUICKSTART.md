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

- Claude Sonnet 4.5: ~$3 per million input tokens, ~$15 per million output tokens
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

Redis is used for state management and response caching to improve performance and reduce costs.

```bash
# Start Redis using Docker Compose (from Vision directory)
docker-compose up -d

# Verify Redis is running
docker-compose ps

# You should see:
# NAME                IMAGE          STATUS
# vision-redis-1      redis:7-alpine Up X minutes (healthy)
```

### Test Redis Connection

```bash
# Test Redis with docker
docker exec -it vision-redis-1 redis-cli ping

# Should output: PONG
```

### About Response Caching

Vision uses Redis to cache LLM responses, providing significant performance and cost benefits:

- **Speed**: 40% faster on cache hits (responses returned instantly)
- **Cost**: 30-40% reduction in API costs when cached responses are reused
- **Cache TTL**: Default 1 hour (configurable via `CACHE_TTL` in `.env`)
- **Automatic**: Caching works automatically when Redis is running and `ENABLE_CACHING=true`

The caching system intelligently caches identical requests, so if you generate the same sprite twice, the second generation will be nearly instant and free!

### About Parallel Execution

Vision automatically uses parallel execution for animation generation to dramatically improve performance:

- **Automatic Activation**: Animations with 4+ frames use parallel mode automatically
- **Speed Improvement**: 20-30% faster overall, 2-4x speedup for animation frames
- **Sequential Mode**: Animations with < 4 frames use sequential mode (less overhead)
- **No Configuration**: Works automatically, no setup required
- **Quality**: Same output quality as sequential mode

**Example**: An 8-frame animation that would take ~80s sequentially completes in ~12s with parallel execution (4-5x faster for the animation portion).

### About Adaptive Compression

Vision includes intelligent compression enhancements (Phases 1-3) that work automatically:

- **Phase 1: Palette Indexing** - 60-75% compression for sprites with ≤16 colors
- **Phase 2: Delta Encoding** - 70-90% compression for animation frames
- **Phase 3: Adaptive Thresholds** - Intelligent encoding selection (>90% optimal)
- **Result:** 80-95% compression for ideal cases, working automatically
- **Phase 4 (2D RLE):** Intentionally deferred as optional future enhancement

**No configuration needed** - the system analyzes sprites and selects optimal compression transparently.

See [`docs/ADAPTIVE_THRESHOLDS_GUIDE.md`](docs/ADAPTIVE_THRESHOLDS_GUIDE.md) for details.

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
   ✅ Model: claude-sonnet-4-5-20250929

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

#### Single Asset Generation

```bash
# Simple generation with auto-rendering
vision generate "wooden chest" --dimensions 16x16

# With custom name and category
vision generate "health potion" --name potion_health --category items --dimensions 16x16

# JSON only (no automatic rendering)
vision generate "background tile" --no-render --dimensions 32x32

# With scaling for preview
vision generate "player sprite" --render-scale 4 --dimensions 32x32
```

#### Batch Generation

```bash
# Generate multiple assets from YAML file
vision generate-batch examples/batch_examples/items_batch.yaml

# With parallel processing
vision generate-batch examples/batch_examples/items_batch.yaml --parallel 4

# Validate batch file first (dry run)
vision generate-batch items.yaml --dry-run
```

#### Create Texture Atlas

```bash
# Combine assets into atlas texture
vision create-atlas ./output/items ./atlases --name items_atlas

# With custom settings
vision create-atlas ./assets ./output \
  --name game_atlas \
  --algorithm MAXRECTS \
  --padding 2 \
  --power-of-two
```

#### Manual Rendering

```bash
# Render existing manifest
vision render output/*/sprite.json

# With custom scale
vision render manifest.json --scale 4 --output preview.png
```

#### Check Status

```bash
# Check generation status
vision status

# List recent generations
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

## Workflow Examples

### Single Asset Generation

```bash
vision generate "wooden sword" --dimensions 16x16 --category weapons
```

**Output**:
- `weapons/wooden_sword.json`
- `weapons/wooden_sword.png`

### Batch Generation

```bash
vision generate-batch game_items.yaml --parallel 4
```

**Output**:
- Individual assets in organized directories
- Optional combined texture atlas

### Creating Texture Atlases

```bash
vision create-atlas ./assets/items ./output --name items_atlas
```

**Output**:
- `items_atlas.png` - Combined texture
- `items_atlas.json` - Sprite coordinate metadata

### Animation Generation

```bash
vision generate "player walking" --animate --frames 8 --dimensions 32x32
```

**Output**:
- `player_walking.json` - Animation manifest
- `player_walking.png` - Sprite sheet (all frames)

## Next Steps

1. **Read the Documentation**:
   - [`README.md`](README.md) - Project overview
   - [`docs/WORKFLOW_GUIDE.md`](docs/WORKFLOW_GUIDE.md) - Complete workflow guide
   - [`docs/CLI_REFERENCE.md`](docs/CLI_REFERENCE.md) - CLI command reference
   - [`docs/BATCH_GENERATION_GUIDE.md`](docs/BATCH_GENERATION_GUIDE.md) - Batch operations
   - [`docs/MIGRATION_GUIDE.md`](docs/MIGRATION_GUIDE.md) - Upgrading from v1.x

2. **Explore Examples**:
   ```bash
   # Generate sample assets
   python3 examples/create_sample_assets.py
   
   # Try batch generation
   vision generate-batch examples/batch_examples/items_batch.yaml
   
   # View output
   open output/
   ```

3. **Try Advanced Features**:
   ```bash
   # Batch generation with atlas
   vision generate-batch items.yaml --parallel 4
   
   # Create texture atlas
   vision create-atlas ./output/items ./atlases --name items
   
   # Manual rendering with scaling
   vision render sprite.json --scale 4
   ```

4. **Build Your Own**:
   ```python
   from src.rendering import PixelGrid, DrawingContext, Color
   from src.rendering.manifest_renderer import ManifestRenderer
   
   # Render existing manifest
   renderer = ManifestRenderer(scale=2)
   renderer.render_manifest_sync("sprite.json", "sprite.png")
   ```

## Configuration Options

### Available Models

You can change the AI models in `.env`:

```bash
# Use Claude Sonnet 4.5 (latest, recommended, balanced)
ORCHESTRATOR_MODEL=claude-sonnet-4-5-20250929

# Use Claude 3.5 Sonnet (previous version, still good)
ORCHESTRATOR_MODEL=claude-3-5-sonnet-20241022

# Use Claude 3 Opus (more creative, slower, more expensive)
ORCHESTRATOR_MODEL=claude-3-opus-20240229
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