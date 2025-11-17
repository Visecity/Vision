#!/bin/bash
# GitHub Repository Setup Script for Vision

set -e

echo "🚀 Vision GitHub Setup"
echo "====================="
echo ""

# Check if repository exists on GitHub
echo "⚠️  Please create the repository on GitHub first:"
echo "   1. Go to https://github.com/new"
echo "   2. Repository name: Vision"
echo "   3. Description: AI-powered pixel art generation system using multi-agent LLMs for creating 2D game assets inspired by Stardew Valley"
echo "   4. Public repository"
echo "   5. DO NOT initialize with README, .gitignore, or license (we have these already)"
echo "   6. Click 'Create repository'"
echo ""
read -p "Press Enter once you've created the repository on GitHub..."

# Set up git remote
echo ""
echo "📡 Configuring git remote..."
git remote add origin https://github.com/Visecity/Vision.git

# Verify remote
echo "✓ Remote configured:"
git remote -v

# Stage all files
echo ""
echo "📦 Staging files..."
git add .

# Create initial commit
echo ""
echo "💾 Creating initial commit..."
git commit -m "feat: initial project structure

- Add multi-agent architecture for pixel art generation
- Include implementation roadmap and documentation
- Set up Python project with pyproject.toml
- Configure development environment
- Add README, LICENSE, and contributing guidelines
- Include Docker Compose for Redis
- Set up directory structure for agents, rendering, and state management

This establishes the foundation for the Vision pixel art generation system."

# Set main branch
echo ""
echo "🌿 Setting up main branch..."
git branch -M main

# Push to GitHub
echo ""
echo "⬆️  Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo "🔗 Repository: https://github.com/Visecity/Vision"
echo ""
echo "Next steps:"
echo "  1. Visit your repository at https://github.com/Visecity/Vision"
echo "  2. Configure branch protection rules (optional)"
echo "  3. Set up GitHub Actions (optional)"
echo "  4. Add topics: pixel-art, game-development, ai, llm, python"
echo ""