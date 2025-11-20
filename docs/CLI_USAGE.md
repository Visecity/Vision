# Vision CLI Usage Guide

This guide provides comprehensive documentation for using the Vision CLI to generate pixel art sprites.

## Installation

After installing the Vision package, the `vision` command will be available:

```bash
pip install -e .
```

## Quick Start

Generate your first sprite:

```bash
# Set your API key (if not in .env)
export ANTHROPIC_API_KEY=sk-ant-...

# Generate a simple sprite
vision generate "oak tree"

# Check the status
vision status <workflow-id>

# List all workflows
vision list
```

## Commands

### Generate Command

Generate pixel art sprites from natural language descriptions.

```bash
vision generate DESCRIPTION [OPTIONS]
```

**Arguments:**
- `DESCRIPTION`: Natural language description of the sprite (required)

**Options:**
- `--dimensions, -d TEXT`: Sprite dimensions (default: "16x16")
- `--style, -s TEXT`: Art style (default: "stardew_valley")
  - Choices: `stardew_valley`, `retro_8bit`, `retro_16bit`, `pixel_art`, `custom`
- `--type, -t TEXT`: Asset type (default: "sprite")
  - Choices: `sprite`, `tile`, `icon`, `character`, `object`, `ui_element`
- `--animate, -a`: Generate animation frames
- `--frames, -f INTEGER`: Number of animation frames (default: 4)
- `--frame-duration INTEGER`: Frame duration in milliseconds (default: 200)
- `--session-id TEXT`: Session ID for grouping workflows
- `--output-dir, -o PATH`: Output directory for generated files
- `--interactive, -i`: Interactive mode with prompts
- `--json`: Output results as JSON
- `--verbose, -v`: Enable verbose output

**Examples:**

```bash
# Basic sprite generation
vision generate "oak tree"

# Custom dimensions and style
vision generate "warrior character" --dimensions 32x32 --style retro_8bit

# Animated sprite
vision generate "walking farmer" --animate --frames 8

# With custom output directory
vision generate "health potion" --output-dir ./my_sprites

# Interactive mode
vision generate --interactive

# JSON output
vision generate "sword icon" --json
```

### Status Command

Check the status of a workflow execution.

```bash
vision status WORKFLOW_ID [OPTIONS]
```

**Arguments:**
- `WORKFLOW_ID`: UUID of the workflow to check (required)

**Options:**
- `--json`: Output status as JSON
- `--watch, -w`: Watch status updates (refresh every 2 seconds)
- `--verbose, -v`: Enable verbose output

**Examples:**

```bash
# Check workflow status
vision status 123e4567-e89b-12d3-a456-426614174000

# Watch status updates
vision status <workflow-id> --watch

# JSON output
vision status <workflow-id> --json
```

### List Command

List all workflows, optionally filtered by session.

```bash
vision list [OPTIONS]
```

**Options:**
- `--session-id, -s TEXT`: Filter by session ID
- `--limit, -l INTEGER`: Maximum number of workflows to display (default: 100)
- `--json`: Output workflows as JSON
- `--verbose, -v`: Enable verbose output

**Examples:**

```bash
# List all workflows
vision list

# List workflows for a specific session
vision list --session-id user-123

# Limit results
vision list --limit 20

# JSON output
vision list --json
```

### Config Command

Manage Vision configuration settings.

#### Show Configuration

Display current configuration settings.

```bash
vision config show [OPTIONS]
```

**Options:**
- `--json`: Output configuration as JSON
- `--verbose, -v`: Show all configuration details

**Example:**

```bash
# Show configuration
vision config show

# Show as JSON
vision config show --json

# Show verbose output
vision config show --verbose
```

#### Validate Configuration

Validate configuration and test connections.

```bash
vision config validate [OPTIONS]
```

**Options:**
- `--verbose, -v`: Show detailed validation results

**Example:**

```bash
# Validate configuration
vision config validate

# Validate with verbose output
vision config validate --verbose
```

#### Set Configuration

Set a configuration value in .env file.

```bash
vision config set KEY VALUE [OPTIONS]
```

**Arguments:**
- `KEY`: Configuration key to set (required)
- `VALUE`: Value to set (required)

**Options:**
- `--env-file PATH`: Path to .env file (default: .env in current directory)

**Examples:**

```bash
# Set API key
vision config set ANTHROPIC_API_KEY sk-ant-...

# Set Redis host
vision config set REDIS_HOST localhost

# Use custom .env file
vision config set REDIS_PORT 6380 --env-file /path/to/.env
```

### Info Command

Display system information and configuration status.

```bash
vision info [OPTIONS]
```

**Options:**
- `--json`: Output information as JSON
- `--verbose, -v`: Show detailed system information

**Examples:**

```bash
# Show system info
vision info

# Show as JSON
vision info --json

# Show verbose output
vision info --verbose
```

## Global Options

These options are available for all commands:

- `--version, -v`: Show version and exit
- `--verbose`: Enable verbose logging
- `--debug`: Enable debug logging

## Environment Variables

Vision uses the following environment variables:

### Required
- `ANTHROPIC_API_KEY`: Your Anthropic API key

### Optional - Redis & Caching
- `REDIS_HOST`: Redis server host (default: localhost)
- `REDIS_PORT`: Redis server port (default: 6379)
- `REDIS_PASSWORD`: Redis password (if required)
- `REDIS_DB`: Redis database number (default: 0)
- `ENABLE_CACHING`: Enable response caching (default: true)
- `CACHE_TTL`: Cache time-to-live in seconds (default: 3600, recommended: 604800 for 7 days)

### Optional - Other
- `VISION_SESSION_ID`: Default session ID
- `MAX_RETRIES`: Maximum API retry attempts (default: 3)
- `TIMEOUT`: API call timeout in seconds (default: 300)

### Response Caching

Vision automatically caches LLM responses in Redis to improve performance and reduce costs:

- **How it works**: Identical requests return cached responses instantly
- **Performance**: 40% faster on cache hits
- **Cost savings**: 30-40% reduction on cached responses
- **Cache keys**: Generated from request parameters (model, messages, temperature, etc.)
- **TTL**: Configurable via `CACHE_TTL` (default: 1 hour, recommended: 7 days)
- **Monitoring**: Check cache stats with `docker exec vision-redis-1 redis-cli INFO stats`
- **Clear cache**: `docker exec vision-redis-1 redis-cli FLUSHDB` (if needed)

**When caching helps most**:
- Iterating on prompts or designs
- Generating similar sprites with slight variations
- Re-running failed workflows
- Testing and development

### Automatic Metadata Collection

Vision automatically collects comprehensive metadata for all sprite generation to enable intelligent optimization:

**What's Collected**:
- **Complexity Metrics**: Entropy, repetition, structure analysis
- **Encoding Decisions**: Selected strategy and reasoning
- **Performance Data**: Analysis time, compression ratios
- **Prediction Accuracy**: Estimated vs actual compression

**How It Works**:
- **Automatic**: Metadata collected transparently during generation
- **Non-Blocking**: Collection failures don't affect generation
- **Storage**: JSON files in `metadata/` directory
- **Analytics**: Use [`scripts/validate_phase3.py`](../scripts/validate_phase3.py) to analyze

**Benefits**:
- **Monitoring**: Track encoding performance over time
- **Optimization**: Data-driven threshold tuning
- **Debugging**: Full visibility into encoding decisions
- **Reporting**: Generate performance reports

See [`docs/ADAPTIVE_THRESHOLDS_GUIDE.md`](ADAPTIVE_THRESHOLDS_GUIDE.md) for details.

### Parallel Execution

Vision automatically uses parallel execution for animation generation to dramatically improve performance:

**How It Works**:
- **Automatic**: Animations with ≥ 4 frames use parallel mode automatically
- **Threshold**: < 4 frames use sequential mode (less overhead)
- **Concurrent Frames**: Up to 8 frames generated simultaneously
- **Implementation**: Uses LangGraph's parallel node execution

**Performance Characteristics**:

| Animation Frames | Mode | Expected Speedup | Overall Improvement |
|------------------|------|------------------|---------------------|
| 1-3 frames | Sequential | N/A | N/A (optimized for overhead) |
| 4 frames | Parallel | 2.5-3x | ~25-30% faster |
| 8 frames | Parallel | 4-5x | ~50-55% faster |

**Monitoring Parallel Execution**:

The workflow logs provide detailed timing metrics:

```bash
# Example log output for 4-frame parallel animation
INFO - Routing to parallel animation generation (4 frames)
INFO - Frame 0 completed in 10.5s
INFO - Frame 1 completed in 10.2s
INFO - Frame 2 completed in 10.8s
INFO - Frame 3 completed in 10.1s
INFO - Parallel execution: 4 frames in 10.8s (sequential would be ~41.6s, speedup: 3.85x)
```

**CLI Examples**:

```bash
# Sequential mode (2 frames) - automatic
vision generate "walking character" --frames 2 --dimensions 16x32

# Parallel mode (4 frames) - automatic
vision generate "walking character" --frames 4 --dimensions 16x32

# Max parallel (8 frames) - automatic
vision generate "walking character" --frames 8 --dimensions 16x32
```

**Configuration**:

Parallel execution is enabled by default and requires no configuration. It activates automatically based on frame count.

**Technical Details**:

See [`PARALLEL_EXECUTION_TEST_RESULTS.md`](../PARALLEL_EXECUTION_TEST_RESULTS.md) for comprehensive performance analysis and test results.

### Configuration Files

Vision looks for configuration in:
1. Environment variables
2. `.env` file in current directory
3. Default values

## Output Structure

When you generate a sprite, Vision creates the following structure:

```
output/
└── <request-id>/
    ├── manifest.json      # Manifest JSON DSL
    └── metadata.json      # Generation metadata
```

## Workflow States

Workflows can be in the following states:
- `pending`: Workflow is queued
- `in_progress`: Workflow is currently executing
- `completed`: Workflow completed successfully
- `failed`: Workflow failed with an error
- `cancelled`: Workflow was cancelled by user

## Tips and Best Practices

1. **Use Session IDs**: Group related workflows with `--session-id`
2. **Check Status**: Use `vision status --watch` to monitor long-running workflows
3. **Interactive Mode**: Use `--interactive` when you're not sure about parameters
4. **Output Organization**: Specify `--output-dir` to organize your sprites
5. **Validate First**: Run `vision config validate` before starting generation

## Troubleshooting

### API Key Issues
```bash
# Check if API key is set
vision config show

# Set API key
vision config set ANTHROPIC_API_KEY sk-ant-...
```

### Redis Connection Issues
```bash
# Validate configuration
vision config validate

# Check Redis is running
docker ps | grep redis
```

### Workflow Not Found
```bash
# List all workflows
vision list

# Check specific session
vision list --session-id <your-session>
```

## Examples

### Complete Workflow

```bash
# 1. Validate configuration
vision config validate

# 2. Generate sprite
vision generate "medieval castle" --dimensions 64x64 --style pixel_art

# 3. Check status (use workflow ID from step 2)
vision status <workflow-id>

# 4. List all your workflows
vision list

# 5. View system info
vision info
```

### Animated Sprite Workflow

```bash
# Generate animated character
vision generate "running hero" \
  --dimensions 32x32 \
  --style retro_16bit \
  --animate \
  --frames 12 \
  --frame-duration 150 \
  --session-id game-heroes \
  --output-dir ./sprites/heroes

# Watch progress
vision status <workflow-id> --watch
```

### Batch Generation

```bash
# Generate multiple sprites with same session
vision generate "oak tree" --session-id forest-pack
vision generate "pine tree" --session-id forest-pack
vision generate "birch tree" --session-id forest-pack

# List all forest sprites
vision list --session-id forest-pack
```

## Next Steps

- Review generated manifests in the output directory
- Use the manifest JSON with the rendering engine (Phase 5)
- Organize sprites by session IDs for game projects
- Experiment with different styles and dimensions

For more information, see the [main README](../README.md) and [CONTRIBUTING guide](./CONTRIBUTING.md).