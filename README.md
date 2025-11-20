# Vision 🎨

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Vision** is an AI-powered pixel art generation system that uses multiple specialized LLM agents to create high-quality 2D game assets inspired by Stardew Valley's art style.

## ✨ Features

### 🎯 Complete Workflow Automation
- **Idea → PNG**: Single command from description to rendered asset
- **Batch Generation**: Create multiple related assets from YAML/JSON definitions
- **Atlas Textures**: Automatic sprite sheet/texture atlas creation
- **Consistent Naming**: Matching .json and .png filenames

### 🚀 Enhanced CLI
- [`vision generate`](docs/CLI_REFERENCE.md#vision-generate) - Enhanced with auto-rendering and organization
- [`vision generate-batch`](docs/CLI_REFERENCE.md#vision-generate-batch) - Batch generation from definition files
- [`vision create-atlas`](docs/CLI_REFERENCE.md#vision-create-atlas) - Combine assets into texture atlases
- [`vision render`](docs/CLI_REFERENCE.md#vision-render) - Manual rendering with custom settings

### 🎯 Intelligent Compression (Phases 1-3 Complete)
- **Phase 1: Palette Indexing** - 60-75% compression for low-color sprites (≤16 colors)
- **Phase 2: Delta Encoding** - 70-90% compression for animation frames
- **Phase 3: Adaptive Thresholds** - Intelligent encoding selection with >90% optimal rate
- **System Status** - Production-ready with 80-95% compression for ideal cases
- **Automatic Operation** - Works transparently, no configuration needed
- **Phase 4 (2D RLE)** - Intentionally deferred as optional future enhancement

See [`COMPRESSION_ENHANCEMENTS_ARCHITECTURE.md`](COMPRESSION_ENHANCEMENTS_ARCHITECTURE.md) for technical details.

### 🤖 Multi-Agent Architecture
- **Specialized AI Agents**: Collaborate on design, palette, detail, and animation
- **Stardew Valley Style**: Pre-configured for 16x16 tiles, limited palettes, orthographic perspective
- **Animation Support**: Complete walk cycles and sprite animations
- **Quality Assurance**: Built-in checkpoints ensure consistent output

### ⚡ Performance & Reliability
- **Parallel Execution**: Automatic parallel frame generation (20-30% faster, 2-4x for 4+ frames)
- **Response Caching**: Redis-powered caching (40% faster responses, 30-40% cost reduction on hits)
- **Batch Processing**: 2-10 concurrent asset generations
- **State Persistence**: Reliable workflow state management with Redis

## 🏗️ Architecture

Vision uses a sophisticated multi-agent system powered by LangGraph and Claude Sonnet 4.5:

- **Orchestrator Agent**: Manages workflow and coordinates other agents
- **Design Agent**: Creates structural blueprints and composition
- **Palette Agent**: Selects harmonious color schemes
- **Detail Agent**: Implements pixel-level artwork
- **Animation Agent**: Generates frame sequences

See [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) for detailed technical specifications.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker (for Redis)
- Anthropic API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/vision.git
cd vision
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -e ".[dev]"
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

5. **Start Redis**
```bash
docker-compose up -d
```

### Generate Your First Asset

```bash
# Simple generation with auto-rendering
vision generate "wooden chest" --dimensions 16x16

# With custom name and category
vision generate "health potion" --name health_pot --category items

# Batch generation from YAML file
vision generate-batch examples/batch_examples/items_batch.yaml
```

### More Examples

See [`docs/WORKFLOW_GUIDE.md`](docs/WORKFLOW_GUIDE.md) for comprehensive workflow examples.
See [`docs/BATCH_GENERATION_GUIDE.md`](docs/BATCH_GENERATION_GUIDE.md) for batch operation details.
See [`docs/CLI_REFERENCE.md`](docs/CLI_REFERENCE.md) for complete command reference.

## 📊 Project Status

**Current Phase**: Phase 1 - Foundation & Infrastructure

See the [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) for:
- Detailed phase breakdown (8-10 week MVP)
- Agent specifications
- Technical architecture
- Success metrics

## 📁 Project Structure

```
vision/
├── src/                    # Source code
│   ├── agents/            # Specialized LLM agents
│   ├── core/              # Core functionality
│   ├── llm/               # LLM integration
│   ├── rendering/         # Pixel rendering engine
│   ├── state/             # State management
│   └── cli/               # Command-line interface
├── assets/                # Asset resources
│   ├── palettes/          # Color palettes
│   ├── templates/         # Sprite templates
│   └── examples/          # Example outputs
├── tests/                 # Test suite
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

## 🛠️ Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src tests
ruff src tests
```

### Type Checking

```bash
mypy src
```

## 📖 Documentation

### User Guides
- [Workflow Guide](docs/WORKFLOW_GUIDE.md) - Complete workflow examples and best practices
- [CLI Reference](docs/CLI_REFERENCE.md) - Comprehensive command documentation
- [Batch Generation Guide](docs/BATCH_GENERATION_GUIDE.md) - Batch operations and atlas creation
- [Migration Guide](docs/MIGRATION_GUIDE.md) - Upgrading from v1.x
- [Quick Start](QUICKSTART.md) - Get started in 5 minutes

### Technical Documentation
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - Complete technical blueprint
- [Workflow Improvements Design](WORKFLOW_IMPROVEMENTS_DESIGN.md) - v2.0 technical specification
- [Contributing Guide](docs/CONTRIBUTING.md) - How to contribute
- [Rendering Guide](docs/RENDERING_GUIDE.md) - Rendering system documentation

### Compression Documentation
- [Palette Indexing Guide](PALETTE_INDEXING_GUIDE.md) - Phase 1 compression (60-75% reduction)
- [Delta Encoding Guide](DELTA_ENCODING_GUIDE.md) - Phase 2 animation compression (70-90% reduction)
- [Adaptive Thresholds Guide](docs/ADAPTIVE_THRESHOLDS_GUIDE.md) - Phase 3 intelligent optimization
- [Compression Architecture](COMPRESSION_ENHANCEMENTS_ARCHITECTURE.md) - Complete technical architecture

## 🎯 Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅
- [x] Project structure setup
- [x] Configuration and dependencies
- [x] Documentation foundation

### Phase 2: Core Development (Weeks 3-4) 🚧
- [ ] Agent base classes
- [ ] LLM integration layer
- [ ] Basic rendering engine

### Phase 3: Agent Coordination (Weeks 5-6)
- [ ] LangGraph workflows
- [ ] State management
- [ ] Agent communication

### Phase 4: Integration (Weeks 7-8)
- [ ] CLI interface
- [ ] Sprite sheet generation
- [ ] Quality assurance

### Phase 5: Testing & Optimization (Weeks 9-10)
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Documentation completion

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [Stardew Valley](https://www.stardewvalley.net/) by ConcernedApe
- Built with [Anthropic's Claude](https://www.anthropic.com/)
- Powered by [LangGraph](https://github.com/langchain-ai/langgraph)
- Referenced [pixel-sprite-generator](https://github.com/zfedoran/pixel-sprite-generator) algorithms

## 📞 Support

- 📧 Email: support@vision-project.dev
- 💬 Discord: [Join our community](https://discord.gg/vision)
- 🐛 Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/vision/issues)

---

Made with ❤️ by the Vision Team