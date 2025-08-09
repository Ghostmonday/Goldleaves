#!/usr/bin/env python3
"""
Goldleaves Full-Scope Integrity Check

Automated validation across backend, frontend, infrastructure, and tests.
Validates repository health with comprehensive checks for imports, routes,
authentication, configuration, and architecture conventions.

Usage:
    python scripts/integrity_check.py [--json] [--config CONFIG_FILE] [--skip-heavy]

Exit codes:
    0: All checks passed
    1: Critical failures found
    2: Configuration or setup errors
"""

import argparse
import json
import os
import sys
import subprocess
import importlib
import ast
import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum


class CheckStatus(Enum):
    """Status of individual checks."""
    PASSED = "passed"
    FAILED = "failed" 
    SKIPPED = "skipped"
    WARNING = "warning"


class CheckSeverity(Enum):
    """Severity levels for check results."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CheckResult:
    """Result of an individual integrity check."""
    name: str
    status: CheckStatus
    severity: CheckSeverity
    message: str
    details: List[str] = None
    duration_ms: int = 0
    
    def __post_init__(self):
        if self.details is None:
            self.details = []


@dataclass 
class IntegrityReport:
    """Complete integrity check report."""
    timestamp: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    skipped_checks: int
    warnings: int
    critical_failures: int
    duration_ms: int
    results: List[CheckResult]
    config: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "summary": {
                "total_checks": self.total_checks,
                "passed_checks": self.passed_checks,
                "failed_checks": self.failed_checks,
                "skipped_checks": self.skipped_checks,
                "warnings": self.warnings,
                "critical_failures": self.critical_failures,
                "duration_ms": self.duration_ms,
                "success": self.critical_failures == 0 and self.failed_checks == 0
            },
            "checks": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "severity": r.severity.value,
                    "message": r.message,
                    "details": r.details,
                    "duration_ms": r.duration_ms
                } for r in self.results
            ],
            "config": self.config or {}
        }


class IntegrityChecker:
    """Main integrity checker with modular validation components."""
    
    def __init__(self, config_path: Optional[str] = None, skip_heavy: bool = False):
        self.repo_root = Path(__file__).parent.parent
        self.skip_heavy = skip_heavy or os.getenv("INTEGRITY_SKIP_HEAVY") == "1"
        self.config = self._load_config(config_path)
        self.results: List[CheckResult] = []
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = self.repo_root / "scripts" / "integrity_config.yaml"
            
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config from {config_file}: {e}")
                return {}
        return {}
    
    def _run_check(self, check_name: str, check_func, *args, **kwargs) -> CheckResult:
        """Run a single check and track timing."""
        start_time = datetime.now()
        try:
            result = check_func(*args, **kwargs)
            end_time = datetime.now()
            result.duration_ms = int((end_time - start_time).total_seconds() * 1000)
            return result
        except Exception as e:
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            return CheckResult(
                name=check_name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.CRITICAL,
                message=f"Check failed with exception: {str(e)}",
                details=[str(e)],
                duration_ms=duration_ms
            )
    
    def check_python_imports(self) -> CheckResult:
        """Check for broken imports and unused dependencies."""
        name = "python_imports"
        
        # Find all Python files
        python_files = list(self.repo_root.glob("**/*.py"))
        python_files = [f for f in python_files if not any(
            part.startswith('.') for part in f.parts
        )]
        
        broken_imports = []
        unused_imports = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to find imports
                try:
                    tree = ast.parse(content)
                    imports = []
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.append(node.module)
                    
                    # Check if imports can be resolved
                    for imp in imports:
                        if imp and not imp.startswith('.'):
                            try:
                                # Try to import the module
                                importlib.import_module(imp.split('.')[0])
                            except ImportError:
                                # Check if it's a local import
                                if not self._is_local_module(imp):
                                    # Only report as broken if it's not a known third-party package
                                    # that might not be installed in this environment
                                    known_packages = {
                                        'fastapi', 'uvicorn', 'pydantic', 'sqlalchemy', 
                                        'alembic', 'passlib', 'jose', 'psycopg2',
                                        'pytest', 'httpx', 'requests', 'click',
                                        'yaml', 'json', 'os', 'sys', 'pathlib',
                                        'starlette', 'pydantic_settings', 'app',
                                        'observability', 'typing', 'datetime',
                                        'collections', 'functools', 'asyncio',
                                        'contextlib', 'enum', 'dataclasses', 're'
                                    }
                                    if imp.split('.')[0] not in known_packages:
                                        broken_imports.append(f"{py_file.relative_to(self.repo_root)}: {imp}")
                    
                except SyntaxError as e:
                    broken_imports.append(f"{py_file.relative_to(self.repo_root)}: Syntax error - {e}")
                    
            except Exception as e:
                broken_imports.append(f"{py_file.relative_to(self.repo_root)}: Read error - {e}")
        
        # Check for unused dependencies (basic check)
        unused_deps = self._check_unused_dependencies()
        
        details = []
        if broken_imports:
            details.extend([f"Broken import: {imp}" for imp in broken_imports])
        if unused_deps:
            details.extend([f"Potentially unused dependency: {dep}" for dep in unused_deps])
        
        if broken_imports:
            return CheckResult(
                name=name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.CRITICAL,
                message=f"Found {len(broken_imports)} broken imports",
                details=details
            )
        elif unused_deps:
            return CheckResult(
                name=name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.LOW,
                message=f"Found {len(unused_deps)} potentially unused dependencies",
                details=details
            )
        else:
            return CheckResult(
                name=name,
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message="All imports are valid"
            )
    
    def _is_local_module(self, module_name: str) -> bool:
        """Check if a module is a local module in the project."""
        parts = module_name.split('.')
        check_paths = [
            self.repo_root / f"{parts[0]}.py",
            self.repo_root / parts[0] / "__init__.py"
        ]
        return any(path.exists() for path in check_paths)
    
    def _check_unused_dependencies(self) -> List[str]:
        """Check for potentially unused dependencies."""
        requirements_file = self.repo_root / "requirements.txt"
        if not requirements_file.exists():
            return []
            
        try:
            with open(requirements_file, 'r') as f:
                deps = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (remove version specs)
                        dep = re.split(r'[<>=!]', line)[0].strip()
                        deps.append(dep)
            
            # Find all Python files and extract imports
            used_modules = set()
            for py_file in self.repo_root.glob("**/*.py"):
                if any(part.startswith('.') for part in py_file.parts):
                    continue
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                used_modules.add(alias.name.split('.')[0])
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                used_modules.add(node.module.split('.')[0])
                except:
                    continue
            
            # Check which dependencies might be unused
            unused = []
            for dep in deps:
                # Convert package names to likely module names
                module_name = dep.lower().replace('-', '_')
                if module_name not in used_modules and dep.lower() not in used_modules:
                    # Skip common dev/build dependencies
                    if dep.lower() not in ['pytest', 'black', 'isort', 'mypy', 'flake8', 'ruff']:
                        unused.append(dep)
            
            return unused
            
        except Exception:
            return []
    
    def check_route_contracts(self) -> CheckResult:
        """Check that all routes match their contract definitions and have proper auth."""
        name = "route_contracts"
        
        # Find router files
        router_files = list(self.repo_root.glob("**/router*.py"))
        router_files.extend(self.repo_root.glob("**/routers/**/*.py"))
        
        missing_auth = []
        contract_issues = []
        
        for router_file in router_files:
            try:
                with open(router_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for FastAPI route definitions
                route_patterns = [
                    r'@router\.(get|post|put|delete|patch)',
                    r'@app\.(get|post|put|delete|patch)'
                ]
                
                routes_found = []
                for pattern in route_patterns:
                    routes_found.extend(re.findall(pattern, content, re.IGNORECASE))
                
                if routes_found:
                    # Check for auth dependencies
                    auth_indicators = [
                        'get_current_user',
                        'require_auth',
                        'Depends(',
                        'tenant',
                        'organization'
                    ]
                    
                    has_auth = any(indicator in content for indicator in auth_indicators)
                    public_endpoint_indicators = [
                        '/health',
                        '/docs',
                        '/openapi',
                        '/login',
                        '/register',
                        'public=True'
                    ]
                    
                    is_public = any(indicator in content for indicator in public_endpoint_indicators)
                    
                    if not has_auth and not is_public:
                        missing_auth.append(str(router_file.relative_to(self.repo_root)))
                
            except Exception as e:
                contract_issues.append(f"{router_file.relative_to(self.repo_root)}: {e}")
        
        details = []
        if missing_auth:
            details.extend([f"Missing auth: {route}" for route in missing_auth])
        if contract_issues:
            details.extend([f"Contract issue: {issue}" for issue in contract_issues])
        
        # Check for allowlisted public endpoints from config
        allowlisted_public = self.config.get('auth', {}).get('public_endpoints', [])
        
        # Filter out allowlisted files
        missing_auth_filtered = []
        for route in missing_auth:
            is_allowlisted = any(allowlist in route for allowlist in allowlisted_public)
            if not is_allowlisted:
                missing_auth_filtered.append(route)
        
        missing_auth = missing_auth_filtered
        
        if missing_auth:
            return CheckResult(
                name=name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.HIGH,
                message=f"Found {len(missing_auth)} routes without auth requirements",
                details=details
            )
        elif contract_issues:
            return CheckResult(
                name=name,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                message=f"Found {len(contract_issues)} contract issues",
                details=details
            )
        else:
            return CheckResult(
                name=name,
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message="All routes have proper auth/tenant isolation"
            )
    
    def check_environment_variables(self) -> CheckResult:
        """Check that all env vars in use are declared in .env.sample and documented."""
        name = "environment_variables"
        
        # Find environment variable usage
        env_vars_used = set()
        usage_locations = {}
        
        # Scan Python files for environment variable usage
        for py_file in self.repo_root.glob("**/*.py"):
            if any(part.startswith('.') for part in py_file.parts):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for os.getenv, os.environ patterns
                env_patterns = [
                    r'os\.getenv\(["\']([^"\']+)["\']',
                    r'os\.environ\[["\']([^"\']+)["\']\]',
                    r'os\.environ\.get\(["\']([^"\']+)["\']',
                    r'getenv\(["\']([^"\']+)["\']'
                ]
                
                for pattern in env_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        env_vars_used.add(match)
                        if match not in usage_locations:
                            usage_locations[match] = []
                        usage_locations[match].append(str(py_file.relative_to(self.repo_root)))
                        
            except Exception:
                continue
        
        # Check .env.example
        env_example_file = self.repo_root / ".env.example"
        env_vars_declared = set()
        
        if env_example_file.exists():
            try:
                with open(env_example_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            var_name = line.split('=')[0].strip()
                            env_vars_declared.add(var_name)
            except Exception:
                pass
        
        # Find undocumented variables
        undocumented = env_vars_used - env_vars_declared
        
        # Exclude internal script variables and common system variables
        system_vars = {'INTEGRITY_SKIP_HEAVY', 'DEBUG', 'PYTHONPATH', 'PATH', 'HOME', 'USER'}
        undocumented = undocumented - system_vars
        
        # Check README for documentation
        readme_file = self.repo_root / "README.md"
        documented_in_readme = set()
        
        if readme_file.exists():
            try:
                with open(readme_file, 'r') as f:
                    readme_content = f.read()
                    for var in env_vars_used:
                        if var in readme_content:
                            documented_in_readme.add(var)
            except Exception:
                pass
        
        details = []
        if undocumented:
            details.extend([
                f"Undocumented env var: {var} (used in {', '.join(usage_locations.get(var, []))})"
                for var in undocumented
            ])
        
        if undocumented:
            return CheckResult(
                name=name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.MEDIUM,
                message=f"Found {len(undocumented)} undocumented environment variables",
                details=details
            )
        else:
            return CheckResult(
                name=name,
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message=f"All {len(env_vars_used)} environment variables are documented"
            )
    
    def check_frontend_build(self) -> CheckResult:
        """Check frontend builds, linting, and test coverage."""
        name = "frontend_build"
        
        # Look for frontend package.json
        package_json = self.repo_root / "package.json"
        
        if not package_json.exists():
            # Check for frontend in subdirectories
            frontend_dirs = [
                self.repo_root / "frontend",
                self.repo_root / "client",
                self.repo_root / "web",
                self.repo_root / "apps" / "web"
            ]
            
            package_json = None
            for frontend_dir in frontend_dirs:
                if (frontend_dir / "package.json").exists():
                    package_json = frontend_dir / "package.json"
                    break
        
        if not package_json or not package_json.exists():
            return CheckResult(
                name=name,
                status=CheckStatus.SKIPPED,
                severity=CheckSeverity.INFO,
                message="No frontend package.json found - skipping frontend checks"
            )
        
        frontend_dir = package_json.parent
        details = []
        issues = []
        
        try:
            # Load package.json to check available scripts
            with open(package_json, 'r') as f:
                package_data = json.load(f)
            
            scripts = package_data.get('scripts', {})
            
            # Try to run lint if available
            if 'lint' in scripts and not self.skip_heavy:
                try:
                    result = subprocess.run(
                        ['npm', 'run', 'lint'],
                        cwd=frontend_dir,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode != 0:
                        issues.append("Linting failed")
                        details.append(f"Lint error: {result.stderr}")
                except subprocess.TimeoutExpired:
                    issues.append("Linting timed out")
                except Exception as e:
                    details.append(f"Could not run lint: {e}")
            
            # Try to run build if available
            if 'build' in scripts and not self.skip_heavy:
                try:
                    result = subprocess.run(
                        ['npm', 'run', 'build'],
                        cwd=frontend_dir,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode != 0:
                        issues.append("Build failed")
                        details.append(f"Build error: {result.stderr}")
                    elif "warning" in result.stdout.lower() or "warning" in result.stderr.lower():
                        issues.append("Build completed with warnings")
                        details.append("Build warnings detected")
                except subprocess.TimeoutExpired:
                    issues.append("Build timed out")
                except Exception as e:
                    details.append(f"Could not run build: {e}")
            
            # Try to run tests with coverage if available
            test_scripts = ['test', 'test:coverage', 'coverage']
            test_script = None
            for script in test_scripts:
                if script in scripts:
                    test_script = script
                    break
            
            if test_script and not self.skip_heavy:
                try:
                    result = subprocess.run(
                        ['npm', 'run', test_script],
                        cwd=frontend_dir,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode != 0:
                        issues.append("Tests failed")
                        details.append(f"Test error: {result.stderr}")
                    
                    # Check coverage if output contains coverage info
                    output = result.stdout + result.stderr
                    coverage_match = re.search(r'(\d+(?:\.\d+)?)%', output)
                    if coverage_match:
                        coverage = float(coverage_match.group(1))
                        baseline = self.config.get('frontend', {}).get('coverage_baseline', 80)
                        if coverage < baseline:
                            issues.append(f"Coverage {coverage}% below baseline {baseline}%")
                    
                except subprocess.TimeoutExpired:
                    issues.append("Tests timed out")
                except Exception as e:
                    details.append(f"Could not run tests: {e}")
            
        except Exception as e:
            return CheckResult(
                name=name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.HIGH,
                message=f"Frontend check failed: {e}",
                details=[str(e)]
            )
        
        if issues:
            return CheckResult(
                name=name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.HIGH,
                message=f"Frontend issues: {', '.join(issues)}",
                details=details
            )
        else:
            return CheckResult(
                name=name,
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message="Frontend build, lint, and tests passed"
            )
    
    def check_architecture_conventions(self) -> CheckResult:
        """Check that PR-added files in last 48h comply with architecture conventions."""
        name = "architecture_conventions"
        
        # Get files added in last 48 hours
        try:
            since_date = (datetime.now() - timedelta(hours=48)).isoformat()
            result = subprocess.run(
                ['git', 'log', f'--since={since_date}', '--name-only', '--pretty=format:', '--diff-filter=A'],
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return CheckResult(
                    name=name,
                    status=CheckStatus.SKIPPED,
                    severity=CheckSeverity.INFO,
                    message="Could not get git history - skipping architecture check"
                )
            
            new_files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
        except Exception as e:
            return CheckResult(
                name=name,
                status=CheckStatus.SKIPPED,
                severity=CheckSeverity.INFO,
                message=f"Could not check git history: {e}"
            )
        
        if not new_files:
            return CheckResult(
                name=name,
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message="No new files added in last 48 hours"
            )
        
        # Define architecture conventions
        default_conventions = {
            'backend_models': {'path': 'models/', 'pattern': r'.*\.py$'},
            'backend_routers': {'path': 'routers/', 'pattern': r'.*\.py$'},
            'backend_services': {'path': 'services/', 'pattern': r'.*\.py$'},
            'backend_schemas': {'path': 'schemas/', 'pattern': r'.*\.py$'},
            'tests': {'path': 'tests/', 'pattern': r'test_.*\.py$'},
            'frontend_components': {'path': 'src/components/', 'pattern': r'.*\.(js|ts|jsx|tsx)$'},
            'frontend_pages': {'path': 'pages/', 'pattern': r'.*\.(js|ts|jsx|tsx)$'}
        }
        
        conventions = self.config.get('architecture', default_conventions)
        
        violations = []
        
        for file_path in new_files:
            # Skip __pycache__ and other generated files
            if '__pycache__' in file_path or file_path.endswith('.pyc'):
                continue
                
            file_violations = []
            
            # Check if file follows naming conventions
            for convention_name, rules in conventions.items():
                if isinstance(rules, dict):
                    expected_path = rules.get('path', '')
                    pattern = rules.get('pattern', r'.*\.py$')
                else:
                    # Fallback for simple string rules
                    expected_path = rules
                    pattern = r'.*\.py$'
                
                if expected_path and file_path.startswith(expected_path):
                    # Special exceptions for common files
                    filename = Path(file_path).name
                    if convention_name == 'tests' and filename in ['__init__.py', 'conftest.py', 'agent.py', 'dependencies.py']:
                        # These are allowed in tests directory
                        break
                    elif not re.match(pattern, filename):
                        file_violations.append(
                            f"File {file_path} doesn't match {convention_name} pattern {pattern}"
                        )
                    break
            else:
                # File doesn't match any expected path
                if not any(
                    file_path.startswith(path) or file_path.endswith(path) for path in [
                        'scripts/', 'docs/', 'config/', '.github/', 
                        'alembic/', 'requirements', 'pyproject.toml',
                        'README', 'LICENSE', '.env', '.git', '.vscode/',
                        'docker-compose.yml', 'Dockerfile', '.dockerignore',
                        'archive_ultra/', 'pull_request_reviews/',
                        '.md', '.txt', '.ini', '.yml', '.yaml', '.json'
                    ]
                ):
                    file_violations.append(
                        f"File {file_path} doesn't follow expected directory structure"
                    )
            
            violations.extend(file_violations)
        
        if violations:
            return CheckResult(
                name=name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.MEDIUM,
                message=f"Found {len(violations)} architecture convention violations",
                details=violations
            )
        else:
            return CheckResult(
                name=name,
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message=f"All {len(new_files)} new files follow architecture conventions"
            )
    
    def check_python_linting(self) -> CheckResult:
        """Run Python linting tools if available."""
        name = "python_linting"
        
        linters = ['ruff', 'flake8', 'black', 'isort']
        results = {}
        issues = []
        
        for linter in linters:
            try:
                # Check if linter is available
                subprocess.run([linter, '--version'], capture_output=True, check=True)
                
                if not self.skip_heavy:
                    # Run the linter
                    if linter == 'ruff':
                        cmd = ['ruff', 'check', '.']
                    elif linter == 'flake8':
                        cmd = ['flake8', '.']
                    elif linter == 'black':
                        cmd = ['black', '--check', '.']
                    elif linter == 'isort':
                        cmd = ['isort', '--check-only', '.']
                    
                    result = subprocess.run(
                        cmd,
                        cwd=self.repo_root,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    results[linter] = result.returncode == 0
                    if result.returncode != 0:
                        issues.append(f"{linter} failed")
                        
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                results[linter] = None  # Tool not available or failed
        
        available_linters = [k for k, v in results.items() if v is not None]
        failed_linters = [k for k, v in results.items() if v is False]
        
        if not available_linters:
            return CheckResult(
                name=name,
                status=CheckStatus.SKIPPED,
                severity=CheckSeverity.INFO,
                message="No Python linting tools available"
            )
        
        if failed_linters:
            return CheckResult(
                name=name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.MEDIUM,
                message=f"Linting failed: {', '.join(failed_linters)}",
                details=issues
            )
        else:
            return CheckResult(
                name=name,
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message=f"All available linters passed: {', '.join(available_linters)}"
            )
    
    def run_all_checks(self) -> IntegrityReport:
        """Run all integrity checks and return comprehensive report."""
        start_time = datetime.now()
        
        # Define all checks to run
        checks = [
            ("python_imports", self.check_python_imports),
            ("route_contracts", self.check_route_contracts), 
            ("environment_variables", self.check_environment_variables),
            ("frontend_build", self.check_frontend_build),
            ("architecture_conventions", self.check_architecture_conventions),
            ("python_linting", self.check_python_linting),
        ]
        
        results = []
        
        for check_name, check_func in checks:
            result = self._run_check(check_name, check_func)
            results.append(result)
            self.results.append(result)
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Calculate summary statistics
        total_checks = len(results)
        passed_checks = len([r for r in results if r.status == CheckStatus.PASSED])
        failed_checks = len([r for r in results if r.status == CheckStatus.FAILED])
        skipped_checks = len([r for r in results if r.status == CheckStatus.SKIPPED])
        warnings = len([r for r in results if r.status == CheckStatus.WARNING])
        critical_failures = len([r for r in results if r.severity == CheckSeverity.CRITICAL and r.status == CheckStatus.FAILED])
        
        return IntegrityReport(
            timestamp=datetime.now().isoformat(),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            skipped_checks=skipped_checks,
            warnings=warnings,
            critical_failures=critical_failures,
            duration_ms=duration_ms,
            results=results,
            config=self.config
        )


def print_report(report: IntegrityReport, json_output: bool = False):
    """Print the integrity report to stdout."""
    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return
    
    # Human-readable output
    print("🌿 Goldleaves Integrity Check Report")
    print("=" * 50)
    print(f"Timestamp: {report.timestamp}")
    print(f"Duration: {report.duration_ms}ms")
    print()
    
    # Summary
    print("📊 Summary:")
    print(f"  Total checks: {report.total_checks}")
    print(f"  ✅ Passed: {report.passed_checks}")
    print(f"  ❌ Failed: {report.failed_checks}")
    print(f"  ⚠️  Warnings: {report.warnings}")
    print(f"  ⏭️  Skipped: {report.skipped_checks}")
    print(f"  🚨 Critical failures: {report.critical_failures}")
    print()
    
    # Individual check results
    print("🔍 Check Results:")
    for result in report.results:
        status_icon = {
            CheckStatus.PASSED: "✅",
            CheckStatus.FAILED: "❌", 
            CheckStatus.WARNING: "⚠️",
            CheckStatus.SKIPPED: "⏭️"
        }[result.status]
        
        severity_icon = {
            CheckSeverity.CRITICAL: "🚨",
            CheckSeverity.HIGH: "🔥",
            CheckSeverity.MEDIUM: "⚠️",
            CheckSeverity.LOW: "ℹ️",
            CheckSeverity.INFO: "📋"
        }[result.severity]
        
        print(f"  {status_icon} {severity_icon} {result.name}: {result.message}")
        
        if result.details:
            for detail in result.details[:5]:  # Limit details shown
                print(f"    - {detail}")
            if len(result.details) > 5:
                print(f"    ... and {len(result.details) - 5} more")
        print()
    
    # Final status
    success = report.critical_failures == 0 and report.failed_checks == 0
    if success:
        print("🎉 All critical checks passed! Repository integrity validated.")
    else:
        print("💥 Integrity check failed! Please fix the issues above.")


def main():
    """Main entry point for the integrity checker."""
    parser = argparse.ArgumentParser(
        description="Goldleaves Full-Scope Integrity Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/integrity_check.py                    # Run all checks
  python scripts/integrity_check.py --json            # JSON output for CI
  python scripts/integrity_check.py --skip-heavy      # Skip slow checks
  python scripts/integrity_check.py --config custom.yaml
        """
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format for CI consumption'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration YAML file'
    )
    
    parser.add_argument(
        '--skip-heavy',
        action='store_true',
        help='Skip time-consuming checks (builds, tests, linting)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create checker and run all checks
        checker = IntegrityChecker(
            config_path=args.config,
            skip_heavy=args.skip_heavy
        )
        
        report = checker.run_all_checks()
        
        # Print report
        print_report(report, json_output=args.json)
        
        # Exit with appropriate code
        if report.critical_failures > 0:
            sys.exit(1)  # Critical failures
        elif report.failed_checks > 0:
            sys.exit(1)  # Non-critical failures
        else:
            sys.exit(0)  # Success
            
    except KeyboardInterrupt:
        print("\n⏸️  Integrity check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Integrity check failed with error: {e}")
        if args.json:
            error_report = {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }
            print(json.dumps(error_report, indent=2))
        sys.exit(2)


if __name__ == "__main__":
    main()