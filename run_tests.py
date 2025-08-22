#!/usr/bin/env python3
"""
Test runner script for MQTT2Yandex Bridge
"""
import sys
import os
import subprocess
import argparse

def run_tests(args):
    """Run tests with various options"""

    # Set PYTHONPATH to include app directory
    env = os.environ.copy()
    app_dir = os.path.join(os.path.dirname(__file__), 'app')
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{app_dir}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = app_dir

    # Base pytest command
    cmd = ['pytest']

    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    elif args.slow:
        cmd.extend(['-m', 'slow'])
    else:
        # Run all tests by default
        pass

    if args.coverage:
        cmd.extend([
            '--cov=app',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-fail-under=80'
        ])

    if args.verbose:
        cmd.append('-v')

    if args.fail_fast:
        cmd.append('-x')

    if args.test_path:
        cmd.append(args.test_path)
    else:
        cmd.append('app/tests/')

    print(f"Running command: {' '.join(cmd)}")
    print(f"With PYTHONPATH: {env['PYTHONPATH']}")

    result = subprocess.run(cmd, env=env, cwd=os.path.dirname(__file__))

    return result.returncode

def run_specific_test_suite(test_type):
    """Run specific test suites"""
    print(f"Running {test_type} tests...")

    env = os.environ.copy()
    app_dir = os.path.join(os.path.dirname(__file__), 'app')
    env['PYTHONPATH'] = app_dir

    test_mapping = {
        'api': 'app/tests/test_api.py app/tests/test_api_integration.py',
        'models': 'app/tests/test_models.py',
        'schemas': 'app/tests/test_schemas.py',
        'services': 'app/tests/test_services.py',
        'config': 'app/tests/test_config.py',
        'all': 'app/tests/'
    }

    if test_type in test_mapping:
        cmd = ['pytest', '-v', test_mapping[test_type]]
        result = subprocess.run(cmd, env=env, cwd=os.path.dirname(__file__))
        return result.returncode
    else:
        print(f"Unknown test type: {test_type}")
        return 1

def main():
    parser = argparse.ArgumentParser(description='Run tests for MQTT2Yandex Bridge')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--slow', action='store_true', help='Run only slow tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--fail-fast', '-x', action='store_true', help='Stop on first failure')
    parser.add_argument('--test-path', help='Specific test file or directory to run')
    parser.add_argument('--type', choices=['api', 'models', 'schemas', 'services', 'config', 'all'],
                       help='Run specific test suite')

    args = parser.parse_args()

    if args.type:
        exit_code = run_specific_test_suite(args.type)
    else:
        exit_code = run_tests(args)

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
