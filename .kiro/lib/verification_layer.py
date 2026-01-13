from dataclasses import dataclass
from typing import List, Optional
import subprocess
import logging
import time
import re

@dataclass
class TestResult:
    status: str           # "pass", "fail", "flaky"
    test_count: int
    failures: List[str]
    duration_seconds: float
    output: str

class VerificationLayer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def run_smoke_tests(self) -> TestResult:
        """Run pytest tests/smoke/ -x --tb=short."""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/smoke/", "-x", "--tb=short", "-v"],
                shell=False,  # Prevent shell injection
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            output = result.stdout + result.stderr
            
            # Parse test results
            test_count = self._parse_test_count(output)
            failures = self._parse_failures(output)
            
            status = "pass" if result.returncode == 0 else "fail"
            
            self.logger.info(f"Smoke tests completed: {status} ({test_count} tests, {duration:.2f}s)")
            
            return TestResult(
                status=status,
                test_count=test_count,
                failures=failures,
                duration_seconds=duration,
                output=output
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.logger.error("Smoke tests timed out")
            return TestResult(
                status="fail",
                test_count=0,
                failures=["Test timeout after 300 seconds"],
                duration_seconds=duration,
                output="Test execution timed out"
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Smoke tests failed to run: {e}")
            return TestResult(
                status="fail",
                test_count=0,
                failures=[str(e)],
                duration_seconds=duration,
                output=str(e)
            )
    
    def run_full_suite(self) -> TestResult:
        """Run pytest tests/ --tb=short."""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/", "--tb=short", "-v"],
                shell=False,  # Prevent shell injection
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            duration = time.time() - start_time
            output = result.stdout + result.stderr
            
            # Parse test results
            test_count = self._parse_test_count(output)
            failures = self._parse_failures(output)
            
            status = "pass" if result.returncode == 0 else "fail"
            
            self.logger.info(f"Full test suite completed: {status} ({test_count} tests, {duration:.2f}s)")
            
            return TestResult(
                status=status,
                test_count=test_count,
                failures=failures,
                duration_seconds=duration,
                output=output
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.logger.error("Full test suite timed out")
            return TestResult(
                status="fail",
                test_count=0,
                failures=["Test timeout after 1800 seconds"],
                duration_seconds=duration,
                output="Test execution timed out"
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Full test suite failed to run: {e}")
            return TestResult(
                status="fail",
                test_count=0,
                failures=[str(e)],
                duration_seconds=duration,
                output=str(e)
            )
    
    def trigger_rca(self, failure_info: str) -> None:
        """Invoke @rca prompt for failure diagnosis."""
        self.logger.info("Triggering RCA analysis for test failures")
        
        # In a real implementation, this would invoke the RCA prompt
        # For now, just log the failure info
        rca_prompt = f"""
@rca

Test failures detected. Please analyze the following failure information and provide root cause analysis:

{failure_info}

Please identify:
1. Root cause of the failure
2. Immediate fix recommendations
3. Prevention strategies for similar failures
"""
        
        self.logger.info(f"RCA prompt generated: {len(rca_prompt)} characters")
        # TODO: Actually invoke the RCA prompt through the binding system
    
    def verify_evolution(self, agent_name: str, test_task: str, baseline_metrics: dict = None) -> bool:
        """Run agent on test task and compare metrics."""
        self.logger.info(f"Verifying evolution for {agent_name} with task: {test_task}")
        
        # Run smoke tests first to ensure basic functionality
        smoke_result = self.run_smoke_tests()
        if smoke_result.status != "pass":
            self.logger.error("Evolution verification failed: smoke tests failed")
            return False
        
        # Mock performance comparison - in reality would measure:
        # - Task completion time
        # - Success rate  
        # - Context efficiency
        # - Error rate
        
        if baseline_metrics:
            # Check for regression > 10%
            current_time = smoke_result.duration_seconds
            baseline_time = baseline_metrics.get('completion_time', current_time)
            
            if current_time > baseline_time * 1.1:  # 10% regression
                self.logger.warning(f"Performance regression detected: {current_time:.2f}s vs {baseline_time:.2f}s")
                return False
        
        self.logger.info("Evolution verification passed")
        return True
    
    def _parse_test_count(self, output: str) -> int:
        """Parse test count from pytest output."""
        # Look for patterns like "3 passed" or "2 failed, 1 passed"
        patterns = [
            r'(\d+) passed',
            r'(\d+) failed',
            r'(\d+) error',
            r'(\d+) skipped'
        ]
        
        total = 0
        for pattern in patterns:
            matches = re.findall(pattern, output)
            for match in matches:
                total += int(match)
        
        return total
    
    def _parse_failures(self, output: str) -> List[str]:
        """Parse failure messages from pytest output."""
        failures = []
        
        # Look for FAILED test names
        failed_tests = re.findall(r'FAILED (.*?) -', output)
        failures.extend(failed_tests)
        
        # Look for ERROR test names
        error_tests = re.findall(r'ERROR (.*?) -', output)
        failures.extend(error_tests)
        
        return failures
