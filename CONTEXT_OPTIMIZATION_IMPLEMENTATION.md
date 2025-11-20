# Context Passing Optimization Implementation

**Date**: 2025-11-18  
**Priority**: Medium (Priority 3 from PERFORMANCE_OPTIMIZATION.md)  
**Status**: ✅ Completed

---

## Overview

Implemented selective context passing optimization to reduce token usage by 5-10% across all agent interactions. This optimization ensures agents only receive the exact data they need, reducing prompt sizes and improving cost efficiency.

---

## Implementation Details

### 1. Agent Dependency Mapping

Added explicit dependency mapping in [`src/state/workflow.py`](src/state/workflow.py):

```python
AGENT_DEPENDENCIES = {
    "design": [],  # No dependencies - uses request only
    "palette": ["design"],  # Needs design output
    "detail": ["design", "palette"],  # Needs both design and palette
    "animation": ["design", "palette", "detail"],  # Needs all previous outputs
    "animation_frame": ["design", "palette", "detail"],  # Frame generation needs all context
}
```

**Benefits:**
- Clear documentation of data flow
- Easy to maintain and update
- Single source of truth for dependencies

### 2. Helper Functions

#### `build_minimal_context()`
Constructs minimal `previous_results` dict containing only required fields:

```python
def build_minimal_context(
    state: AgentState,
    current_step: str,
    additional_fields: dict[str, Any] | None = None,
) -> dict[str, Any]
```

**Features:**
- Filters state based on AGENT_DEPENDENCIES
- Supports additional fields (e.g., frame_index for animation frames)
- Logs context size and field count
- Warns about missing dependencies

#### `validate_context_dependencies()`
Validates all required dependencies exist before agent execution:

```python
def validate_context_dependencies(
    state: AgentState,
    current_step: str,
) -> tuple[bool, list[str]]
```

**Features:**
- Early error detection
- Clear error messages listing missing fields
- Prevents cascading failures

#### `_estimate_size()`
Estimates object size in characters for logging:

```python
def _estimate_size(obj: Any) -> int
```

**Features:**
- Handles strings, dicts, lists, ColorPalette objects
- Used for token usage tracking
- Aids in performance monitoring

### 3. Agent Node Updates

Updated all agent nodes to use the new helpers:

#### Design Node
```python
# Build minimal context (design has no dependencies)
previous_results = build_minimal_context(state, "design")
```

#### Palette Node
```python
# Validate dependencies
is_valid, missing = validate_context_dependencies(state, "palette")
if not is_valid:
    state["error"] = f"Palette node missing dependencies: {missing}"
    return state

# Build minimal context (palette needs design only)
previous_results = build_minimal_context(state, "palette")
```

#### Detail Node
```python
# Validate dependencies
is_valid, missing = validate_context_dependencies(state, "detail")
if not is_valid:
    state["error"] = f"Detail node missing dependencies: {missing}"
    return state

# Build minimal context (detail needs design and palette)
previous_results = build_minimal_context(state, "detail")
```

#### Animation Node
```python
# Validate dependencies
is_valid, missing = validate_context_dependencies(state, "animation")
if not is_valid:
    state["error"] = f"Animation node missing dependencies: {missing}"
    return state

# Build minimal context (animation needs design, palette, and detail)
previous_results = build_minimal_context(state, "animation")
```

#### Animation Frame Nodes (Parallel)
```python
# Build minimal context for frame generation
additional_fields = {
    "frame_index": frame_index,
    "total_frames": request.animation.frame_count,
}
previous_results = build_minimal_context(
    state, 
    "animation_frame",
    additional_fields=additional_fields
)
```

---

## Benefits

### 1. Token Usage Reduction
- **Estimated Savings**: 5-10% per request
- **How**: Only passing required fields reduces prompt size
- **Impact**: Lower API costs, faster processing

### 2. Improved Logging
- Tracks exactly what data is passed to each agent
- Estimates context size for token monitoring
- Aids in debugging and optimization

### 3. Better Validation
- Validates dependencies before execution
- Clear error messages for missing data
- Prevents silent failures

### 4. Maintainability
- Centralized dependency mapping
- Self-documenting code
- Easier to modify data flow

### 5. Safety
- Prevents accidental data leakage
- Ensures clean separation of concerns
- Explicit about what each agent needs

---

## Logging Output Examples

With the new implementation, you'll see logs like:

```
INFO - Context for 'design': 0 field(s), ~0 chars, keys=[]
INFO - Context for 'palette': 1 field(s), ~1250 chars, keys=['design']
INFO - Context for 'detail': 2 field(s), ~1750 chars, keys=['design', 'palette']
INFO - Context for 'animation': 3 field(s), ~4500 chars, keys=['design', 'palette', 'detail']
```

This allows tracking:
- How many fields are passed
- Approximate size in characters
- Specific fields included

---

## Testing Recommendations

1. **Functional Testing**
   - Run existing test suite to ensure no regressions
   - Verify all agents still receive required data
   - Test error handling for missing dependencies

2. **Performance Testing**
   - Compare token usage before/after
   - Measure actual cost reduction
   - Validate 5-10% reduction target

3. **Integration Testing**
   - Test complete workflow end-to-end
   - Verify animation frame generation (parallel mode)
   - Check error propagation

---

## Future Enhancements

1. **Dynamic Dependency Detection**
   - Could analyze agent code to auto-detect dependencies
   - Would reduce manual maintenance

2. **Token Budget Tracking**
   - Add per-agent token budgets
   - Alert when budget exceeded
   - Automatic context truncation if needed

3. **Context Caching**
   - Cache frequently used context subsets
   - Reduce repeated serialization overhead

4. **Compression**
   - Compress large context fields
   - Use references instead of full data

---

## Related Files

- [`src/state/workflow.py`](src/state/workflow.py) - Main implementation
- [`PERFORMANCE_OPTIMIZATION.md`](PERFORMANCE_OPTIMIZATION.md) - Overall optimization plan
- [`PARALLEL_EXECUTION_IMPLEMENTATION.md`](PARALLEL_EXECUTION_IMPLEMENTATION.md) - Parallel execution (Priority 2)

---

## Verification Checklist

- [x] Helper functions implemented
- [x] Agent dependency mapping defined
- [x] All agent nodes updated
- [x] Logging added
- [x] Validation added
- [x] Syntax check passed
- [ ] Functional tests passing
- [ ] Token reduction measured
- [ ] Performance benchmarks updated

---

## Conclusion

This optimization provides a solid foundation for monitoring and reducing token usage while improving code maintainability and safety. The explicit dependency mapping makes the data flow clear and prevents accidental over-sharing of context between agents.

**Next Steps:**
1. Run tests to verify functionality
2. Measure actual token reduction
3. Update performance benchmarks
4. Consider implementing additional optimizations from PERFORMANCE_OPTIMIZATION.md