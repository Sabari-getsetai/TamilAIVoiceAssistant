#!/usr/bin/env python3
"""
Comprehensive Test Runner for Tamil AI Voice Assistant

This script runs all test suites in the correct order:
1. Infrastructure tests (PostgreSQL, Redis, MinIO)
2. Unit tests (Individual component testing)
3. Integration tests (End-to-end workflow testing)
4. Performance tests (Optional benchmarking)

Usage:
    python tests/run_all_tests.py                    # Run all tests
    python tests/run_all_tests.py --quick            # Run infrastructure + integration only
    python tests/run_all_tests.py --unit-only        # Run unit tests only
    python tests/run_all_tests.py --integration-only # Run integration tests only
    python tests/run_all_tests.py --no-performance   # Skip performance tests
"""

import asyncio
import sys
import os
import argparse
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Print test runner banner."""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║            Tamil AI Voice Assistant - Test Suite Runner           ║")
    print("║                                                                   ║")
    print("║  Comprehensive testing of database integration, APIs, workflows   ║")
    print("║  and end-to-end functionality validation                         ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

def print_section_header(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🔬 {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_step(message: str):
    """Print step message."""
    print(f"{Colors.WHITE}→ {message}{Colors.END}")

class TestResult:
    """Test result container."""

    def __init__(self, name: str, passed: bool, duration: float, details: str = ""):
        self.name = name
        self.passed = passed
        self.duration = duration
        self.details = details

class TestRunner:
    """Comprehensive test runner for the Tamil AI Voice Assistant."""

    def __init__(self):
        self.test_results: List[TestResult] = []
        self.start_time = time.time()

    def run_python_test(self, test_path: str, test_name: str) -> TestResult:
        """Run a Python test script and return the result."""
        print_step(f"Running {test_name}...")

        start_time = time.time()
        try:
            # Run the test
            result = subprocess.run(
                [sys.executable, test_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                print_success(f"{test_name} passed ({duration:.1f}s)")
                return TestResult(test_name, True, duration, result.stdout)
            else:
                print_error(f"{test_name} failed ({duration:.1f}s)")
                print(f"{Colors.RED}Error output:{Colors.END}")
                print(result.stderr)
                return TestResult(test_name, False, duration, result.stderr)

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print_error(f"{test_name} timed out after {duration:.1f}s")
            return TestResult(test_name, False, duration, "Test timed out")

        except Exception as e:
            duration = time.time() - start_time
            print_error(f"{test_name} crashed: {e}")
            return TestResult(test_name, False, duration, str(e))

    async def run_async_test(self, test_func, test_name: str) -> TestResult:
        """Run an async test function and return the result."""
        print_step(f"Running {test_name}...")

        start_time = time.time()
        try:
            result = await test_func()
            duration = time.time() - start_time

            if result:
                print_success(f"{test_name} passed ({duration:.1f}s)")
                return TestResult(test_name, True, duration)
            else:
                print_error(f"{test_name} failed ({duration:.1f}s)")
                return TestResult(test_name, False, duration)

        except Exception as e:
            duration = time.time() - start_time
            print_error(f"{test_name} crashed: {e}")
            return TestResult(test_name, False, duration, str(e))

    def run_infrastructure_tests(self) -> List[TestResult]:
        """Run infrastructure tests."""
        print_section_header("INFRASTRUCTURE TESTS")

        results = []

        # Test 1: Infrastructure connectivity
        test_path = project_root / "tests" / "integration" / "test-infrastructure.py"
        if test_path.exists():
            result = self.run_python_test(str(test_path), "Infrastructure Connectivity")
            results.append(result)
        else:
            print_warning("Infrastructure test not found - skipping")

        return results

    def run_unit_tests(self) -> List[TestResult]:
        """Run unit tests."""
        print_section_header("UNIT TESTS")

        results = []

        # Test 1: Session Service Unit Tests
        test_path = project_root / "tests" / "unit" / "test_session_service.py"
        if test_path.exists():
            result = self.run_python_test(str(test_path), "Session Service Unit Tests")
            results.append(result)
        else:
            print_warning("Session service unit tests not found - skipping")

        # Look for other unit tests
        unit_test_dir = project_root / "tests" / "unit"
        if unit_test_dir.exists():
            for test_file in unit_test_dir.glob("test_*.py"):
                if test_file.name != "test_session_service.py":  # Already ran this one
                    result = self.run_python_test(str(test_file), f"Unit Test: {test_file.stem}")
                    results.append(result)

        return results

    def run_integration_tests(self) -> List[TestResult]:
        """Run integration tests."""
        print_section_header("INTEGRATION TESTS")

        results = []

        # Test 1: End-to-End Integration
        test_path = project_root / "tests" / "integration" / "test_end_to_end.py"
        if test_path.exists():
            result = self.run_python_test(str(test_path), "End-to-End Integration")
            results.append(result)
        else:
            print_warning("End-to-end integration test not found - skipping")

        # Look for other integration tests
        integration_test_dir = project_root / "tests" / "integration"
        if integration_test_dir.exists():
            for test_file in integration_test_dir.glob("test_*.py"):
                if test_file.name not in ["test_end_to_end.py", "test-infrastructure.py"]:
                    result = self.run_python_test(str(test_file), f"Integration Test: {test_file.stem}")
                    results.append(result)

        return results

    def run_performance_tests(self) -> List[TestResult]:
        """Run performance tests."""
        print_section_header("PERFORMANCE TESTS")

        results = []

        # Look for performance tests
        perf_test_dir = project_root / "tests" / "performance"
        if perf_test_dir.exists():
            for test_file in perf_test_dir.glob("test_*.py"):
                result = self.run_python_test(str(test_file), f"Performance Test: {test_file.stem}")
                results.append(result)
        else:
            print_info("No performance tests found - creating performance test placeholder")
            # Create a simple performance test placeholder
            self.create_performance_test_placeholder()

        return results

    def create_performance_test_placeholder(self):
        """Create a basic performance test placeholder."""
        perf_test_dir = project_root / "tests" / "performance"
        perf_test_dir.mkdir(exist_ok=True)

        perf_test_content = '''#!/usr/bin/env python3
"""
Performance test placeholder for Tamil AI Voice Assistant.

This test measures basic API response times and throughput.
"""

import asyncio
import time
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

async def test_api_response_times():
    """Test API response times."""
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            # Test health endpoint response time
            start = time.time()
            async with session.get("http://localhost:8000/health") as resp:
                if resp.status == 200:
                    duration = time.time() - start
                    print(f"✓ Health endpoint: {duration:.3f}s")
                    return duration < 1.0  # Should be under 1 second
                else:
                    print(f"✗ Health endpoint failed: {resp.status}")
                    return False

    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False

async def main():
    """Run performance tests."""
    print("🚀 Basic Performance Test")
    print("=" * 30)

    result = await test_api_response_times()

    if result:
        print("\\n✅ Performance tests passed")
        return 0
    else:
        print("\\n❌ Performance tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
'''

        perf_test_file = perf_test_dir / "test_basic_performance.py"
        with open(perf_test_file, 'w') as f:
            f.write(perf_test_content)

        print_info(f"Created performance test: {perf_test_file}")

    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met for running tests."""
        print_section_header("PREREQUISITE CHECKS")

        checks_passed = True

        # Check if backend is running
        print_step("Checking if backend is running...")
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print_success("Backend is running")
            else:
                print_error(f"Backend returned status {response.status_code}")
                checks_passed = False
        except Exception as e:
            print_error(f"Backend not accessible: {e}")
            print_info("Start backend with: python -m uvicorn backend.main:app --reload")
            checks_passed = False

        # Check if Docker services are running
        print_step("Checking Docker services...")
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", "docker-compose.dev.yml", "ps"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print_success("Docker services status checked")
            else:
                print_warning("Docker services check failed - some tests may fail")
        except Exception as e:
            print_warning(f"Could not check Docker services: {e}")

        # Check Python environment
        print_step("Checking Python environment...")
        required_packages = ["fastapi", "sqlalchemy", "redis", "aiohttp", "websockets"]
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            print_error(f"Missing packages: {', '.join(missing_packages)}")
            print_info("Install with: pip install -r requirements.txt")
            checks_passed = False
        else:
            print_success("Python environment ready")

        return checks_passed

    def print_summary(self):
        """Print test summary."""
        total_duration = time.time() - self.start_time

        print_section_header("TEST SUMMARY")

        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        pass_percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n{Colors.BOLD}Overall Results:{Colors.END}")
        print(f"  Total Tests:     {total_tests}")
        print(f"  Passed:          {Colors.GREEN}{passed_tests}{Colors.END}")
        print(f"  Failed:          {Colors.RED}{failed_tests}{Colors.END}")
        print(f"  Pass Rate:       {Colors.GREEN if pass_percentage >= 80 else Colors.YELLOW}{pass_percentage:.1f}%{Colors.END}")
        print(f"  Total Duration:  {total_duration:.1f}s")

        # Print individual test results
        print(f"\n{Colors.BOLD}Individual Test Results:{Colors.END}")
        for result in self.test_results:
            status = f"{Colors.GREEN}PASS{Colors.END}" if result.passed else f"{Colors.RED}FAIL{Colors.END}"
            print(f"  {status} {result.name:<40} ({result.duration:.1f}s)")

        # Print recommendations
        print(f"\n{Colors.BOLD}Recommendations:{Colors.END}")

        if pass_percentage == 100:
            print(f"{Colors.GREEN}🎉 Excellent! All tests passed. System is ready for production.{Colors.END}")
        elif pass_percentage >= 80:
            print(f"{Colors.YELLOW}⚠️  Good! Most tests passed. Review failures before production.{Colors.END}")
        elif pass_percentage >= 60:
            print(f"{Colors.YELLOW}⚠️  Fair. Significant issues need attention before deployment.{Colors.END}")
        else:
            print(f"{Colors.RED}❌ Poor. Major issues detected. System needs debugging.{Colors.END}")

        # Print specific recommendations
        if failed_tests > 0:
            print(f"\n{Colors.YELLOW}Failed Test Analysis:{Colors.END}")
            for result in self.test_results:
                if not result.passed:
                    print(f"  • {result.name}: {result.details[:100]}...")

        return 0 if pass_percentage >= 80 else 1

async def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Tamil AI Voice Assistant Test Runner")
    parser.add_argument("--quick", action="store_true", help="Run infrastructure + integration tests only")
    parser.add_argument("--unit-only", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration-only", action="store_true", help="Run integration tests only")
    parser.add_argument("--no-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--no-prereq-check", action="store_true", help="Skip prerequisite checks")

    args = parser.parse_args()

    print_banner()

    runner = TestRunner()

    # Check prerequisites unless skipped
    if not args.no_prereq_check:
        if not runner.check_prerequisites():
            print_error("Prerequisites not met. Fix issues above and retry.")
            return 1

    # Determine which tests to run
    if args.unit_only:
        runner.test_results.extend(runner.run_unit_tests())
    elif args.integration_only:
        runner.test_results.extend(runner.run_integration_tests())
    elif args.quick:
        runner.test_results.extend(runner.run_infrastructure_tests())
        runner.test_results.extend(runner.run_integration_tests())
    else:
        # Run all tests
        runner.test_results.extend(runner.run_infrastructure_tests())
        runner.test_results.extend(runner.run_unit_tests())
        runner.test_results.extend(runner.run_integration_tests())

        if not args.no_performance:
            runner.test_results.extend(runner.run_performance_tests())

    # Print summary and return exit code
    return runner.print_summary()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test execution interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test runner crashed: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)