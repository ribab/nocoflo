#!/usr/bin/env python3
"""
Test runner for datasource plugin tests.
"""
import sys
import os
import subprocess
import pytest

def run_tests():
    """Run all datasource plugin tests."""
    # Get the directory containing this script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the parent directory to Python path
    parent_dir = os.path.dirname(os.path.dirname(test_dir))
    sys.path.insert(0, parent_dir)
    
    # Run pytest with specific options
    args = [
        "pytest",
        test_dir,
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable warnings
        "--color=yes",  # Colored output
    ]
    
    # Add coverage if available
    try:
        import coverage
        args.extend([
            "--cov=src/components/datasources",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=90"
        ])
    except ImportError:
        print("Coverage not available, running without coverage")
    
    # Run the tests
    result = subprocess.run(args, cwd=parent_dir)
    return result.returncode

def run_specific_test(test_file):
    """Run a specific test file."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(test_dir))
    sys.path.insert(0, parent_dir)
    
    args = [
        "pytest",
        os.path.join(test_dir, test_file),
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    result = subprocess.run(args, cwd=parent_dir)
    return result.returncode

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        exit_code = run_specific_test(test_file)
    else:
        # Run all tests
        exit_code = run_tests()
    
    sys.exit(exit_code) 