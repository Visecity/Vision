"""
Comprehensive test script for parallel execution in Vision workflow.

Tests sequential vs parallel animation generation, measures performance improvements,
and validates output quality and error handling.

Usage:
    python test_parallel_execution.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import get_settings
from src.core.models import AnimationConfig, SpriteRequest
from src.llm.client import LLMClient
from src.state.workflow import create_workflow_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResults:
    """Container for test results and metrics."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.performance_data = []
        self.errors = []
    
    def add_test(self, name: str, passed: bool, details: dict[str, Any] = None):
        """Record test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
            self.errors.append({"test": name, "details": details})
        
        logger.info(f"Test '{name}': {'PASSED' if passed else 'FAILED'}")
        if details:
            logger.info(f"  Details: {json.dumps(details, indent=2)}")
    
    def add_performance_data(self, data: dict[str, Any]):
        """Record performance metrics."""
        self.performance_data.append(data)
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.errors:
            print("\nFAILURES:")
            for error in self.errors:
                print(f"  - {error['test']}: {error['details']}")
        
        if self.performance_data:
            print("\nPERFORMANCE METRICS:")
            for data in self.performance_data:
                print(f"\n  {data['name']}:")
                for key, value in data.items():
                    if key != 'name':
                        print(f"    {key}: {value}")
        
        print("="*80)


async def create_test_request(
    description: str,
    frames: int,
    width: int = 16,
    height: int = 16
) -> SpriteRequest:
    """Create a test sprite request."""
    from src.core.models import AssetType, AssetStyle, Dimensions
    
    animation_config = AnimationConfig(
        frame_count=frames,
        frame_duration=100,
        loop=True
    ) if frames > 1 else None
    
    return SpriteRequest(
        description=description,
        asset_type=AssetType.CHARACTER,
        style=AssetStyle.PIXEL_ART,
        dimensions=Dimensions(width=width, height=height),
        animation=animation_config
    )


async def test_sequential_mode(llm_client: LLMClient, results: TestResults):
    """Test 1: Sequential mode (< 4 frames)."""
    logger.info("\n=== Test 1: Sequential Mode (2 frames) ===")
    
    try:
        # Create request
        request = await create_test_request(
            description="walking character",
            frames=2,
            width=16,
            height=16
        )
        
        # Create workflow
        workflow = create_workflow_graph(llm_client, enable_parallel=True)
        
        # Execute
        start_time = time.time()
        initial_state = {
            "request": request,
            "messages": [],
            "retry_count": 0,
            "timing": {},
        }
        
        result = await workflow.ainvoke(initial_state)
        elapsed = time.time() - start_time
        
        # Validate
        has_animation = result.get("animation") is not None
        frame_count = len(result.get("animation", [])) if has_animation else 0
        used_sequential = "animation_sequential" in result.get("timing", {})
        used_parallel = "animation_parallel_max" in result.get("timing", {})
        
        passed = (
            has_animation and
            frame_count >= 2 and
            used_sequential and
            not used_parallel
        )
        
        results.add_test("Sequential Mode", passed, {
            "frames_generated": frame_count,
            "used_sequential": used_sequential,
            "used_parallel": used_parallel,
            "total_time": f"{elapsed:.2f}s",
            "timing": result.get("timing", {})
        })
        
        results.add_performance_data({
            "name": "Sequential Mode (2 frames)",
            "total_time": f"{elapsed:.2f}s",
            "frames": frame_count,
            "mode": "sequential"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Sequential mode test failed: {e}")
        results.add_test("Sequential Mode", False, {"error": str(e)})
        return None


async def test_parallel_mode(llm_client: LLMClient, results: TestResults):
    """Test 2: Parallel mode (>= 4 frames)."""
    logger.info("\n=== Test 2: Parallel Mode (4 frames) ===")
    
    try:
        # Create request
        request = await create_test_request(
            description="walking character",
            frames=4,
            width=16,
            height=16
        )
        
        # Create workflow
        workflow = create_workflow_graph(llm_client, enable_parallel=True)
        
        # Execute
        start_time = time.time()
        initial_state = {
            "request": request,
            "messages": [],
            "retry_count": 0,
            "timing": {},
        }
        
        result = await workflow.ainvoke(initial_state)
        elapsed = time.time() - start_time
        
        # Validate
        has_animation = result.get("animation") is not None
        frame_count = len(result.get("animation", [])) if has_animation else 0
        used_sequential = "animation_sequential" in result.get("timing", {})
        used_parallel = "animation_parallel_max" in result.get("timing", {})
        timing = result.get("timing", {})
        
        # Calculate speedup
        if used_parallel:
            parallel_total = timing.get("animation_parallel_total", 0)
            parallel_max = timing.get("animation_parallel_max", 0)
            speedup = parallel_total / parallel_max if parallel_max > 0 else 0
        else:
            speedup = 0
        
        passed = (
            has_animation and
            frame_count >= 4 and
            not used_sequential and
            used_parallel and
            speedup > 1.0  # Should have some speedup
        )
        
        results.add_test("Parallel Mode", passed, {
            "frames_generated": frame_count,
            "used_sequential": used_sequential,
            "used_parallel": used_parallel,
            "speedup": f"{speedup:.2f}x",
            "total_time": f"{elapsed:.2f}s",
            "timing": timing
        })
        
        results.add_performance_data({
            "name": "Parallel Mode (4 frames)",
            "total_time": f"{elapsed:.2f}s",
            "frames": frame_count,
            "mode": "parallel",
            "speedup": f"{speedup:.2f}x",
            "parallel_max": f"{timing.get('animation_parallel_max', 0):.2f}s",
            "parallel_total": f"{timing.get('animation_parallel_total', 0):.2f}s"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Parallel mode test failed: {e}")
        results.add_test("Parallel Mode", False, {"error": str(e)})
        return None


async def test_performance_comparison(llm_client: LLMClient, results: TestResults):
    """Test 3: Performance comparison (8 frames parallel vs sequential simulation)."""
    logger.info("\n=== Test 3: Performance Comparison (8 frames) ===")
    
    try:
        # Create request
        request = await create_test_request(
            description="walking character",
            frames=8,
            width=16,
            height=16
        )
        
        # Test with parallel enabled
        workflow_parallel = create_workflow_graph(llm_client, enable_parallel=True)
        start_time = time.time()
        initial_state = {
            "request": request,
            "messages": [],
            "retry_count": 0,
            "timing": {},
        }
        
        result_parallel = await workflow_parallel.ainvoke(initial_state)
        parallel_time = time.time() - start_time
        
        # Extract timing metrics
        timing = result_parallel.get("timing", {})
        parallel_max = timing.get("animation_parallel_max", 0)
        parallel_total = timing.get("animation_parallel_total", 0)
        speedup = parallel_total / parallel_max if parallel_max > 0 else 0
        
        # Estimate sequential time (sum of parallel times)
        estimated_sequential = parallel_total
        time_saved = estimated_sequential - parallel_max
        improvement_pct = (time_saved / estimated_sequential * 100) if estimated_sequential > 0 else 0
        
        # Validate
        frame_count = len(result_parallel.get("animation", []))
        passed = (
            frame_count >= 8 and
            speedup >= 1.5 and  # Expect at least 1.5x speedup with 8 frames
            improvement_pct >= 20  # Expect at least 20% improvement
        )
        
        results.add_test("Performance Comparison", passed, {
            "frames": frame_count,
            "parallel_time": f"{parallel_max:.2f}s",
            "estimated_sequential": f"{estimated_sequential:.2f}s",
            "speedup": f"{speedup:.2f}x",
            "time_saved": f"{time_saved:.2f}s",
            "improvement": f"{improvement_pct:.1f}%"
        })
        
        results.add_performance_data({
            "name": "8-Frame Performance",
            "parallel_execution": f"{parallel_max:.2f}s",
            "sequential_equivalent": f"{estimated_sequential:.2f}s",
            "speedup": f"{speedup:.2f}x",
            "improvement": f"{improvement_pct:.1f}%",
            "time_saved": f"{time_saved:.2f}s"
        })
        
        return result_parallel
        
    except Exception as e:
        logger.error(f"Performance comparison test failed: {e}")
        results.add_test("Performance Comparison", False, {"error": str(e)})
        return None


async def test_quality_verification(
    sequential_result: dict[str, Any],
    parallel_result: dict[str, Any],
    results: TestResults
):
    """Test 4: Quality verification - ensure parallel output matches sequential quality."""
    logger.info("\n=== Test 4: Quality Verification ===")
    
    try:
        # Check both results exist
        if not sequential_result or not parallel_result:
            results.add_test("Quality Verification", False, {
                "error": "Missing results from previous tests"
            })
            return
        
        # Validate structure
        seq_anim = sequential_result.get("animation", [])
        par_anim = parallel_result.get("animation", [])
        
        seq_has_frames = len(seq_anim) > 0
        par_has_frames = len(par_anim) > 0
        
        # Check frame structure
        seq_valid = all(isinstance(frame, dict) for frame in seq_anim)
        par_valid = all(isinstance(frame, dict) for frame in par_anim)
        
        # Check for no corruption
        seq_no_error = sequential_result.get("error") is None
        par_no_error = parallel_result.get("error") is None
        
        # Validate ordering (frames should be in correct order)
        par_frames = parallel_result.get("animation_frames", {})
        correct_order = all(i in par_frames for i in range(len(par_anim)))
        
        passed = (
            seq_has_frames and
            par_has_frames and
            seq_valid and
            par_valid and
            seq_no_error and
            par_no_error and
            correct_order
        )
        
        results.add_test("Quality Verification", passed, {
            "sequential_frames": len(seq_anim),
            "parallel_frames": len(par_anim),
            "sequential_valid": seq_valid,
            "parallel_valid": par_valid,
            "no_errors": seq_no_error and par_no_error,
            "correct_order": correct_order
        })
        
    except Exception as e:
        logger.error(f"Quality verification test failed: {e}")
        results.add_test("Quality Verification", False, {"error": str(e)})


async def test_error_handling(llm_client: LLMClient, results: TestResults):
    """Test 5: Error handling and graceful degradation."""
    logger.info("\n=== Test 5: Error Handling ===")
    
    try:
        # Test with edge cases
        test_cases = [
            ("0 frames", 0),
            ("1 frame", 1),
            ("3 frames (boundary)", 3),
            ("4 frames (boundary)", 4),
        ]
        
        all_passed = True
        details = {}
        
        for name, frame_count in test_cases:
            try:
                request = await create_test_request(
                    description="test character",
                    frames=frame_count,
                    width=8,
                    height=8
                )
                
                workflow = create_workflow_graph(llm_client, enable_parallel=True)
                initial_state = {
                    "request": request,
                    "messages": [],
                    "retry_count": 0,
                    "timing": {},
                }
                
                result = await workflow.ainvoke(initial_state)
                
                # Check no crash occurred
                no_error = result.get("error") is None or frame_count < 2
                details[name] = {
                    "status": "ok" if no_error else "error",
                    "animation": result.get("animation") is not None,
                    "frame_count": len(result.get("animation", []))
                }
                
                if not no_error and frame_count >= 2:
                    all_passed = False
                    
            except Exception as e:
                logger.warning(f"Edge case '{name}' raised exception: {e}")
                details[name] = {"status": "exception", "error": str(e)}
                # Don't fail test for expected edge cases (0, 1 frame)
                if frame_count >= 2:
                    all_passed = False
        
        results.add_test("Error Handling", all_passed, details)
        
    except Exception as e:
        logger.error(f"Error handling test failed: {e}")
        results.add_test("Error Handling", False, {"error": str(e)})


async def main():
    """Run all tests."""
    logger.info("="*80)
    logger.info("PARALLEL EXECUTION TEST SUITE")
    logger.info("="*80)
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    
    # Initialize
    results = TestResults()
    
    try:
        # Load settings
        settings = get_settings()
        
        # Check API key
        if not settings.anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY not set. Please set it in .env file.")
            print("\n❌ ERROR: ANTHROPIC_API_KEY not configured")
            print("Please copy .env.example to .env and add your API key")
            return
        
        # Create LLM client
        llm_client = LLMClient(settings=settings)
        
        # Run tests
        sequential_result = await test_sequential_mode(llm_client, results)
        parallel_result = await test_parallel_mode(llm_client, results)
        performance_result = await test_performance_comparison(llm_client, results)
        
        await test_quality_verification(sequential_result, parallel_result, results)
        await test_error_handling(llm_client, results)
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        results.add_test("Test Suite", False, {"error": str(e)})
    
    # Print results
    results.print_summary()
    
    logger.info(f"\nEnd Time: {datetime.now().isoformat()}")
    
    # Return exit code
    return 0 if results.tests_failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)