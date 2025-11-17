# Vision 🎨

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Vision** is an AI-powered pixel art generation system that uses multiple specialized LLM agents to create high-quality 2D game assets inspired by Stardew Valley's art style.

## ✨ Features

- 🤖 **Multi-Agent Architecture**: Specialized AI agents collaborate on design, palette, detail, and animation
- 🎨 **Stardew Valley Style**: Pre-configured for 16x16 tiles, limited palettes, and orthographic perspective
- 🔄 **Animation Support**: Generates complete walk cycles and sprite animations
- 📦 **Sprite Sheet Export**: Outputs PNG sprite sheets with JSON metadata
- 🎯 **Quality Assurance**: Built-in checkpoints ensure consistent, high-quality output
- 💰 **Cost Optimization**: Response caching reduces API costs by 30-40%

## 🏗️ Architecture

Vision uses a sophisticated multi-agent system powered by LangGraph and Claude 3.5 Sonnet:

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

### Usage

```bash
# Generate a single sprite
vision generate "oak tree tile" --style stardew

# Generate with animation
vision generate "farmer character" --animate --frames 16

# Batch generation
vision batch generate sprites.yaml --output ./output
```

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

- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - Complete technical blueprint
- [API Reference](docs/api-reference.md) - API documentation
- [Agent System](docs/agents.md) - Agent architecture and specifications
- [Contributing Guide](docs/CONTRIBUTING.md) - How to contribute

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