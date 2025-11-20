# Vision Project - Agent Instructions

**Version:** 1.0.0  
**Last Updated:** 2025-11-18  
**Project:** Vision - AI-Powered Pixel Art Generation System

---

## 📋 Overview

You are working on **Vision**, a sophisticated multi-agent pixel art generation system. This document provides essential instructions, best practices, and workflows specific to this project. **These instructions MUST be passed to ALL subtasks and child processes without exception.**

### Project Architecture

Vision uses a **Multi-Agent Specialist System** with the following agents:
- **Orchestrator Agent**: Coordinates workflow and manages agent communication
- **Design Agent**: Creates structural blueprints and composition specifications
- **Palette Agent**: Generates harmonious color schemes optimized for pixel art
- **Detail Agent**: Implements pixel-level artwork using Manifest JSON DSL
- **Animation Agent**: Generates frame sequences for animations

### Core Technologies
- **LangGraph**: Workflow orchestration and state management
- **Claude Sonnet 4.5**: All agent LLM operations
- **Redis**: State persistence and caching
- **Pillow**: Image rendering and manipulation
- **Python 3.11+**: Primary development language

---

## 🎯 Primary Directives

### 1. Always Pass These Instructions Forward

**CRITICAL**: When creating subtasks, spawning child processes, or switching modes:
```
ALWAYS include the following in your instructions:
"Read and follow the instructions in agent-instruction.md located at the project root. Pass these instructions to all subsequent subtasks."
```

### 2. Maintain Action Logging

**ALL significant actions MUST be logged** to `agent-log.md` using this format:
```markdown
## [Timestamp] - [Action Type]
**Agent/Mode:** [Your current mode]
**Action:** [Brief description]
**Files Modified:** [List of files]
**Outcome:** [Success/Failure/Partial]
**Notes:** [Any relevant details]
```

### 3. Project Context Awareness

Before making ANY changes:
1. Read [`README.md`](README.md) for project overview
2. Review [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) for architecture details
3. Check current phase and ensure changes align with roadmap
4. Understand the multi-agent workflow pattern

---

## 🔧 Workflow Best Practices

### Agent Development Workflow

When working with agents ([`src/agents/`](src/agents/)):

1. **All agents inherit from [`BaseAgent`](src/agents/base.py)**
   - Implement `process()` method for core logic
   - Implement `validate_input()` and `validate_output()`
   - Use proper type hints with `TypeVar` for InputT and OutputT
   - Follow the established agent pattern

2. **Agent Communication Pattern**
   - Use [`AgentMessage`](src/core/models.py:AgentMessage()) for inter-agent messages
   - Always include `request_id` for traceability
   - Use appropriate [`MessageType`](src/core/models.py:MessageType) enum values
   - Log all messages for debugging

3. **State Management**
   - All agent state flows through LangGraph's state machine
   - Use Redis for persistent state storage
   - Never modify state directly - use state manager methods
   - Implement proper error recovery for state failures

4. **Validation Requirements**
   - Validate ALL inputs before processing
   - Validate ALL outputs before returning
   - Use [`ValidationResult`](src/core/models.py:ValidationResult()) for consistent validation
   - Include specific errors, warnings, and suggestions

### Code Quality Standards

1. **Type Safety**
   - Use type hints for ALL function signatures
   - Leverage Pydantic models for data validation
   - Use TypedDict or dataclasses for structured data
   - Run `mypy src` before committing

2. **Error Handling**
   - Use custom exceptions from [`base.py`](src/agents/base.py)
   - Always log errors with context
   - Implement proper cleanup in finally blocks
   - Never suppress exceptions silently

3. **Testing Requirements**
   - Write unit tests for all new agents
   - Write integration tests for agent interactions
   - Maintain >80% code coverage
   - Use pytest fixtures for common test setup

4. **Documentation**
   - All agents need comprehensive docstrings
   - Use Google-style docstring format
   - Include type information and examples
   - Update README.md when adding features

---

## 🛠️ MCP Server Integration

Vision has access to multiple MCP servers. **ALWAYS evaluate if an MCP server can help** before implementing custom solutions.

### Available MCP Servers

#### 1. GitHub MCP (`github`)
**Use for:**
- Repository operations (create branches, commits, PRs)
- Issue tracking and management
- Code search across repositories
- Release management

**Best practices:**
- Use [`search_code`](mcp://github/search_code) to find existing implementations before writing new code
- Use [`fetch-actor-details`](mcp://github/fetch-actor-details) to understand repository structure
- Always create feature branches for significant changes
- Use descriptive commit messages following conventional commits format
- **Note:** While GitHub MCP tools are available for complex repository operations (branches, PRs, issues), use direct `git` commands for routine commits and pushes (see [GitHub Version Control](#-github-version-control) section)

**Example usage:**
```python
# Search for similar agent implementations
use_mcp_tool(
    server_name="github",
    tool_name="search_code",
    arguments={"query": "class BaseAgent language:python"}
)
```

#### 2. Context7 MCP (`context7`)
**Use for:**
- Fetching up-to-date library documentation
- Understanding API usage patterns
- Learning best practices for dependencies

**Best practices:**
- Use [`resolve-library-id`](mcp://context7/resolve-library-id) BEFORE [`get-library-docs`](mcp://context7/get-library-docs)
- Cache documentation lookups to avoid redundant calls
- Prefer official docs over general searches

**Example usage:**
```python
# Get LangGraph documentation
use_mcp_tool(
    server_name="context7",
    tool_name="get-library-docs",
    arguments={
        "context7CompatibleLibraryID": "/langchain/langgraph",
        "topic": "state management"
    }
)
```

#### 3. Brave Search MCP (`brave-search`)
**Use for:**
- Finding external pixel art resources
- Researching pixel art techniques
- Looking up color theory references
- Finding game development patterns

**Best practices:**
- Use specific queries for better results
- Prefer [`brave_web_search`](mcp://brave-search/brave_web_search) for general information
- Use [`brave_local_search`](mcp://brave-search/brave_local_search) only for location-based queries

#### 4. Apify MCP (`apify`)
**Use for:**
- Web scraping for pixel art examples
- Gathering reference images
- Collecting game asset datasets
- Automating data collection tasks

**Best practices:**
- Check for existing actors before creating custom scrapers
- Use [`search-actors`](mcp://apify/search-actors) to find relevant tools
- Monitor API usage to avoid rate limits

### MCP Decision Tree

```
Need to work with code/repos?
  └─> Use GitHub MCP

Need documentation for a library?
  └─> Use Context7 MCP

Need to search the web?
  └─> Use Brave Search MCP

Need to scrape/collect data?
  └─> Use Apify MCP

None of the above?
  └─> Implement custom solution OR ask user for guidance
```

---

## 🎨 Roo Mode Selection Guide

Vision provides multiple Roo modes. **Choose the appropriate mode for each task.**

### Mode Selection Matrix

| Task Type | Recommended Mode | Alternative Mode |
|-----------|-----------------|------------------|
| Planning features | `architect` | `orchestrator` |
| Writing/modifying code | `code` | - |
| Fixing bugs | `debug` | `code` |
| Understanding code | `ask` | - |
| Creating documentation | `documentation-writer` | `code` |
| Defining requirements | `user-story-creator` | `architect` |
| Analyzing codebase | `project-research` | `ask` |
| Security review | `security-review` | `code` |
| Deployment/infrastructure | `devops` | `code` |
| Creating pixel art | `vision-artist` | - |
| Creating new modes | `mode-writer` | - |
| Complex multi-phase projects | `orchestrator` | `architect` |

### Mode-Specific Guidelines

#### 🏗️ Architect Mode
**Use when:**
- Designing new agent capabilities
- Planning system architecture changes
- Creating technical specifications
- Breaking down complex features

**Best practices:**
- Create detailed architectural documents
- Use Mermaid diagrams for workflows
- Consider scalability and performance
- Document design decisions

**Switching from Architect to Code:**
```xml
<switch_mode>
<mode_slug>code</mode_slug>
<reason>Architecture complete, ready to implement</reason>
</switch_mode>
```

#### 💻 Code Mode
**Use when:**
- Implementing new agents
- Modifying existing functionality
- Writing tests
- Refactoring code

**Best practices:**
- Follow the established agent pattern
- Write comprehensive tests
- Use type hints consistently
- Update documentation

**File restrictions:** Can edit all files except those restricted by mode configuration

#### 🪲 Debug Mode
**Use when:**
- Investigating test failures
- Troubleshooting agent communication issues
- Analyzing performance problems
- Fixing bugs

**Best practices:**
- Add strategic logging statements
- Use debugger breakpoints
- Check state management carefully
- Verify Redis connection

#### 🪃 Orchestrator Mode
**Use when:**
- Managing complex, multi-phase projects
- Coordinating multiple types of work
- Breaking down large initiatives
- Managing dependencies between tasks

**Best practices:**
- Create subtasks for distinct work phases
- Use appropriate modes for each subtask
- Track overall progress
- Maintain coordination between subtasks

#### 🎨 Vision Artist Mode
**Use when:**
- Generating pixel art assets
- Testing the Vision generation system
- Creating sample sprites/icons
- Building asset libraries

**Best practices:**
- Provide detailed descriptions
- Specify exact dimensions
- Reference Stardew Valley style guidelines
- Test with various asset types

---

## 📝 Logging Requirements

### Agent Action Log Format

**Location:** [`agent-log.md`](agent-log.md)

**Required for:**
- All file modifications
- Agent implementations
- Bug fixes
- Configuration changes
- Deployment operations
- Mode switches

**Format:**
```markdown
## [2025-11-18T02:08:00Z] - [Action Type]
**Agent/Mode:** code
**Action:** Implemented DetailAgent with Manifest JSON generation
**Files Modified:**
- src/agents/detail_agent.py (created)
- tests/test_detail_agent.py (created)
**Outcome:** Success
**Notes:** 
- Added comprehensive docstrings
- Implemented validation for Manifest JSON structure
- Added unit tests with 90% coverage
- Agent ready for integration testing
```

### Append to Log Script

Use this helper when logging:
```python
from datetime import datetime

def log_action(action_type: str, mode: str, action: str, 
               files: list[str], outcome: str, notes: str = ""):
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    log_entry = f"""
## [{timestamp}] - {action_type}
**Agent/Mode:** {mode}
**Action:** {action}
**Files Modified:**
{chr(10).join(f'- {f}' for f in files)}
**Outcome:** {outcome}
**Notes:** {notes}

"""
    
    with open("agent-log.md", "a") as f:
        f.write(log_entry)
```
---

## 🔄 GitHub Version Control

### Commit Strategy

**ALL significant work MUST be committed regularly** to maintain a clear history of changes. Use git commands directly for routine version control operations.

### When to Commit

Commit changes at these key points:

1. **After completing a significant task**
   - Implemented a new agent
   - Fixed a bug
   - Added a new feature
   - Completed a test suite

2. **After tests pass**
   - All unit tests passing
   - Integration tests successful
   - Type checking passes (`mypy src`)
   - Linting passes (`ruff src`)

3. **Before switching modes**
   - Save progress before mode transition
   - Ensure work is not lost
   - Create a checkpoint for reverting if needed

4. **After documentation updates**
   - Updated README or guides
   - Added new documentation files
   - Modified agent-instruction.md

5. **At logical breakpoints**
   - End of work session
   - Before starting a new subtask
   - After resolving merge conflicts

### Commit Message Format

Follow the **Conventional Commits** format for consistency:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, config)
- `perf`: Performance improvements

**Examples:**
```bash
# Simple commit
git commit -m "feat(detail-agent): implement Manifest JSON generation"

# Detailed commit
git commit -m "fix(animation-agent): resolve frame interpolation bug

- Fixed incorrect delta calculation between frames
- Added validation for frame sequence continuity
- Updated tests to cover edge cases

Fixes #42"

# Documentation update
git commit -m "docs(readme): add installation instructions for Redis"

# Test addition
git commit -m "test(palette-agent): add color harmony validation tests"
```

### When to Push to Remote

Push changes to the remote repository at these points:

1. **End of work session**
   - Ensure work is backed up
   - Make progress visible to team

2. **After completing a major milestone**
   - Finished implementing an agent
   - Completed a phase deliverable
   - All tests passing

3. **Before switching to a different task**
   - Save checkpoint for context switching
   - Enable collaboration on current work

4. **When seeking code review**
   - Before creating pull requests
   - When sharing work with team members

5. **Daily (minimum)**
   - At least once per day when actively working
   - Even if work is incomplete (use feature branches)

**Push commands:**
```bash
# Push current branch to remote
git push origin <branch-name>

# Push and set upstream tracking
git push -u origin <branch-name>

# Push all tags
git push --tags
```

### Branching Best Practices

1. **Main branch protection**
   - Never commit directly to `main`
   - Always work on feature branches
   - Require PR reviews for merging

2. **Feature branch naming**
   ```bash
   # Pattern: type/description
   feat/animation-agent-implementation
   fix/detail-agent-validation-bug
   docs/update-workflow-guide
   refactor/simplify-state-management
   ```

3. **Branch workflow**
   ```bash
   # Create new feature branch
   git checkout -b feat/new-feature
   
   # Make changes and commit regularly
   git add .
   git commit -m "feat: implement new feature"
   
   # Push branch to remote
   git push -u origin feat/new-feature
   
   # Keep branch updated with main
   git checkout main
   git pull origin main
   git checkout feat/new-feature
   git merge main
   
   # Or use rebase for cleaner history
   git rebase main
   ```

4. **Branch lifecycle**
   - Create branch from `main`
   - Develop and commit regularly
   - Push to remote frequently
   - Create PR when ready
   - Merge after review
   - Delete branch after merge

### Git Commands Reference

**Basic workflow:**
```bash
# Check status
git status

# Stage files
git add <file>
git add .  # Stage all changes

# Commit changes
git commit -m "type(scope): message"

# Push to remote
git push origin <branch-name>

# Pull latest changes
git pull origin main

# View commit history
git log --oneline --graph --decorate
```

**Working with branches:**
```bash
# List branches
git branch -a

# Create and switch to new branch
git checkout -b <branch-name>

# Switch branches
git checkout <branch-name>

# Delete local branch
git branch -d <branch-name>

# Delete remote branch
git push origin --delete <branch-name>
```

**Undoing changes:**
```bash
# Discard unstaged changes
git checkout -- <file>

# Unstage files
git reset HEAD <file>

# Amend last commit
git commit --amend

# Revert a commit
git revert <commit-hash>
```

### Integration with Workflow

Version control should be seamlessly integrated into your development workflow:

1. **Start work** → Create/switch to feature branch
2. **Make changes** → Edit files
3. **Test** → Run tests locally
4. **Log** → Update [`agent-log.md`](agent-log.md)
5. **Commit** → Save changes with descriptive message
6. **Continue or finish** → Repeat or push to remote

**Example workflow:**
```bash
# Starting a new task
git checkout -b feat/implement-palette-agent
git push -u origin feat/implement-palette-agent

# During development (repeat as needed)
# ... make changes ...
pytest tests/test_palette_agent.py
# ... update agent-log.md ...
git add src/agents/palette_agent.py tests/test_palette_agent.py agent-log.md
git commit -m "feat(palette-agent): implement color harmony generation"

# End of work session
git push origin feat/implement-palette-agent
```

### Handling Large Changes

For complex tasks spanning multiple sessions:

1. **Break into smaller commits**
   - Each commit should be atomic and logical
   - Commit partial progress with clear messages
   - Use prefixes like `wip:` for work-in-progress

2. **Use feature flags** (if applicable)
   - Keep incomplete features disabled
   - Commit regularly without breaking main

3. **Maintain commit hygiene**
   - Squash fixup commits before merging
   - Rebase for cleaner history
   - Keep commit messages descriptive

**Example:**
```bash
# Working on large feature
git commit -m "wip(detail-agent): add basic structure"
git commit -m "wip(detail-agent): implement validation"
git commit -m "feat(detail-agent): complete Manifest JSON generation"

# Before merging, squash WIP commits
git rebase -i HEAD~3
```


---

## 🚀 Phase-Specific Guidelines

### Current Phase: Phase 2 - Core Agent Development

**Priority tasks:**
1. Complete all agent implementations
2. Ensure comprehensive test coverage
3. Validate agent communication patterns
4. Document agent specifications

**What to focus on:**
- Agent quality and reliability
- Proper error handling
- Validation at all boundaries
- Clear documentation

**What to avoid:**
- Premature optimization
- Complex features before basics work
- Skipping tests
- Incomplete validation

### Phase Transition Checklist

Before moving to next phase, ensure:
- [ ] All agents implemented and tested
- [ ] Integration tests passing
- [ ] Documentation complete
- [ ] Performance benchmarks met
- [ ] Code review completed
- [ ] Phase deliverables signed off

---

## 🔐 Security & Best Practices

### API Key Management
- **NEVER** hardcode API keys
- Use environment variables exclusively
- Store sensitive config in `.env` (not committed)
- Use `.env.example` for documentation

### Error Information
- **NEVER** log sensitive data
- Sanitize error messages
- Use generic messages for user-facing errors
- Log detailed errors server-side only

### Redis Security
- Use password authentication in production
- Enable SSL/TLS for remote connections
- Implement proper TTL policies
- Monitor for unusual access patterns

---

## 🎯 Success Criteria

Your work on Vision is successful when:

1. **Code Quality**
   - All tests passing
   - No type checking errors
   - Code coverage >80%
   - Linting warnings addressed

2. **Documentation**
   - All functions have docstrings
   - README.md is current
   - Examples are working
   - Architecture docs match implementation

3. **Agent Performance**
   - Response times within targets
   - Validation catches edge cases
   - Error handling is robust
   - State management is reliable

4. **User Experience**
   - Clear error messages
   - Predictable behavior
   - Fast response times
   - High-quality outputs

---

## 📚 Key Files Reference

Always review these files for context:

1. [`README.md`](README.md) - Project overview and quick start
2. [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) - Complete technical architecture
3. [`src/agents/base.py`](src/agents/base.py) - Base agent implementation pattern
4. [`src/core/models.py`](src/core/models.py) - All data models and types
5. [`pyproject.toml`](pyproject.toml) - Dependencies and project metadata

---

## ⚠️ Common Pitfalls to Avoid

1. **Don't skip validation**
   - Always validate inputs and outputs
   - Use ValidationResult consistently
   - Provide helpful error messages

2. **Don't ignore the roadmap**
   - Check which phase you're in
   - Follow the prescribed order
   - Don't implement future-phase features

3. **Don't break existing patterns**
   - Follow the established agent pattern
   - Use existing models and types
   - Maintain consistency with other agents

4. **Don't forget about testing**
   - Write tests as you code
   - Test edge cases
   - Verify error handling

5. **Don't work in isolation**
   - Review related agent implementations
   - Check for integration points
   - Understand the complete workflow

---

## 🔄 Iterative Development Cycle

For each task, follow this cycle:

```
1. Read agent-instruction.md (this file)
   └─> Understand context and requirements

2. Check IMPLEMENTATION_ROADMAP.md
   └─> Verify current phase and priorities

3. Evaluate MCP servers
   └─> Can existing tools help?

4. Choose appropriate Roo mode
   └─> Select based on task type

5. Create/switch to feature branch (if needed)
   └─> git checkout -b feat/task-name

6. Implement changes
   └─> Follow established patterns

7. Write/update tests
   └─> Ensure coverage >80%

8. Validate against standards
   └─> Run mypy, ruff, pytest

9. Log actions to agent-log.md
   └─> Document what was done

10. Commit changes to git
    └─> git add . && git commit -m "type(scope): description"
    └─> Use conventional commits format
    └─> Commit after each significant milestone

11. Update documentation
    └─> Keep README current

12. Push to remote (at session end or major milestones)
    └─> git push origin <branch-name>
    └─> Backup work and enable collaboration

13. Pass instructions forward
    └─> Include agent-instruction.md in subtasks
```

---

## 📞 Getting Help

When uncertain about:

**Architecture decisions:**
- Review IMPLEMENTATION_ROADMAP.md sections
- Check existing agent implementations
- Use `ask` mode for clarification

**Technical implementation:**
- Use Context7 MCP for library docs
- Search GitHub MCP for similar patterns
- Review Python best practices

**Pixel art domain knowledge:**
- Use Brave Search MCP for techniques
- Reference Stardew Valley style guides
- Check existing design specifications

---

## ✅ Final Checklist

Before considering any task complete:

- [ ] Code follows established patterns
- [ ] All tests passing (unit + integration)
- [ ] Type checking passes (`mypy src`)
- [ ] Linting passes (`ruff src`)
- [ ] Documentation updated
- [ ] Action logged to [`agent-log.md`](agent-log.md)
- [ ] Changes committed to git with descriptive message
- [ ] Changes pushed to remote repository (if appropriate)
- [ ] Changes aligned with current phase
- [ ] MCP servers evaluated for task
- [ ] Appropriate mode used
- [ ] Instructions passed to subtasks (if any)

---

**Remember:** This document is your guide to maintaining consistency and quality across the Vision project. When in doubt, refer back to these instructions and the implementation roadmap.

**End of agent-instruction.md v1.0.0**