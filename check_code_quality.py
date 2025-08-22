#!/usr/bin/env python3
"""
Code quality checker for MQTT2Yandex Bridge
"""
import sys
import os
import subprocess
import argparse

def run_flake8():
    """Run flake8 linter"""
    print("Running flake8...")
    cmd = ['flake8', 'app/', '--max-line-length=88', '--extend-ignore=E203,W503']
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_black_check():
    """Run black formatter check"""
    print("Running black check...")
    cmd = ['black', '--check', 'app/']
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_black_format():
    """Run black formatter"""
    print("Running black format...")
    cmd = ['black', 'app/']
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_isort_check():
    """Run isort import sorting check"""
    print("Running isort check...")
    cmd = ['isort', '--check-only', 'app/']
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_isort_format():
    """Run isort import sorting"""
    print("Running isort format...")
    cmd = ['isort', 'app/']
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_mypy():
    """Run mypy type checking"""
    print("Running mypy...")
    cmd = ['mypy', 'app/', '--ignore-missing-imports']
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def run_all_checks():
    """Run all code quality checks"""
    checks = [
        run_flake8,
        run_black_check,
        run_isort_check,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except FileNotFoundError as e:
            print(f"Tool not found: {e}")
            results.append(1)

    return max(results) if results else 0

def format_code():
    """Format code with all tools"""
    formatters = [
        run_black_format,
        run_isort_format,
    ]

    results = []
    for formatter in formatters:
        try:
            result = formatter()
            results.append(result)
        except FileNotFoundError as e:
            print(f"Tool not found: {e}")
            results.append(1)

    return max(results) if results else 0

def main():
    parser = argparse.ArgumentParser(description='Check code quality for MQTT2Yandex Bridge')
    parser.add_argument('--check', action='store_true', help='Run all code quality checks')
    parser.add_argument('--format', action='store_true', help='Format code with all tools')
    parser.add_argument('--flake8', action='store_true', help='Run only flake8')
    parser.add_argument('--black', action='store_true', help='Run only black')
    parser.add_argument('--isort', action='store_true', help='Run only isort')
    parser.add_argument('--mypy', action='store_true', help='Run only mypy')

    args = parser.parse_args()

    if args.check:
        exit_code = run_all_checks()
    elif args.format:
        exit_code = format_code()
    elif args.flake8:
        exit_code = run_flake8()
    elif args.black:
        exit_code = run_black_check()
    elif args.isort:
        exit_code = run_isort_check()
    elif args.mypy:
        exit_code = run_mypy()
    else:
        # Default: run checks
        exit_code = run_all_checks()

    if exit_code == 0:
        print("✅ All checks passed!")
    else:
        print("❌ Some checks failed!")

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
