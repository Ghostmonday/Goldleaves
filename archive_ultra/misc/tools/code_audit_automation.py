#!/usr/bin/env python3
"""
Project-Wide Code Audit Script for Claude Opus
Automates the systematic audit process for any codebase
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse

class CodeAuditFramework:
    """
    Automated code audit framework that Claude Opus can use to systematically
    analyze large codebases for issues, patterns, and architectural integrity.
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.audit_results = {
            "project_info": {},
            "file_counts": {},
            "errors": [],
            "imports": [],
            "architecture": {},
            "severity_summary": {
                "critical": 0,
                "medium": 0,
                "low": 0,
                "clean": 0
            }
        }
    
    def discover_project_structure(self) -> Dict[str, Any]:
        """Phase 1: Project Discovery"""
        print("🔍 Phase 1: Discovering project structure...")
        
        # Count files by type
        file_extensions = {
            'python': ['*.py'],
            'javascript': ['*.js', '*.jsx'],
            'typescript': ['*.ts', '*.tsx'],
            'java': ['*.java', '*.kt'],
            'csharp': ['*.cs', '*.fs'],
            'go': ['*.go'],
            'rust': ['*.rs'],
            'cpp': ['*.cpp', '*.c', '*.h'],
            'config': ['*.json', '*.yaml', '*.yml', '*.toml', '*.ini'],
            'docs': ['*.md', '*.rst', '*.txt']
        }
        
        file_counts = {}
        for lang, patterns in file_extensions.items():
            count = 0
            for pattern in patterns:
                count += len(list(self.project_path.rglob(pattern)))
            file_counts[lang] = count
        
        # Find dependency files
        dependency_files = []
        dep_patterns = [
            'requirements.txt', 'pyproject.toml', 'setup.py',
            'package.json', 'package-lock.json', 'yarn.lock',
            'pom.xml', 'build.gradle', 'Cargo.toml',
            'go.mod', '*.csproj', 'composer.json'
        ]
        
        for pattern in dep_patterns:
            found = list(self.project_path.rglob(pattern))
            dependency_files.extend([str(f) for f in found])
        
        self.audit_results["file_counts"] = file_counts
        self.audit_results["project_info"] = {
            "total_files": sum(file_counts.values()),
            "dependency_files": dependency_files,
            "primary_language": max(file_counts, key=file_counts.get) if file_counts else "unknown"
        }
        
        return self.audit_results["project_info"]
    
    def analyze_imports_and_dependencies(self) -> List[Dict[str, Any]]:
        """Phase 2: Import & Dependency Analysis"""
        print("📦 Phase 2: Analyzing imports and dependencies...")
        
        import_issues = []
        
        # Search for common import problems
        error_patterns = [
            ("ImportError", "Python import failures"),
            ("ModuleNotFoundError", "Missing Python modules"),
            ("Cannot resolve", "TypeScript/JavaScript resolution issues"),
            ("Module not found", "Node.js missing modules"),
            ("circular", "Circular dependency warnings"),
            ("undefined", "JavaScript undefined references")
        ]
        
        for pattern, description in error_patterns:
            try:
                # Use grep to find patterns (simplified for demo)
                result = subprocess.run(
                    ['grep', '-r', '-n', pattern, str(self.project_path)],
                    capture_output=True, text=True, cwd=self.project_path
                )
                
                if result.stdout:
                    import_issues.append({
                        "type": "import_error",
                        "pattern": pattern,
                        "description": description,
                        "matches": result.stdout.split('\n')[:10]  # Limit output
                    })
            except Exception as e:
                # Fallback to Python-based search
                import_issues.append({
                    "type": "search_error",
                    "error": str(e),
                    "pattern": pattern
                })
        
        self.audit_results["imports"] = import_issues
        return import_issues
    
    def detect_code_issues(self) -> List[Dict[str, Any]]:
        """Phase 3: Error Detection"""
        print("🚨 Phase 3: Detecting code issues...")
        
        issues = []
        
        # Look for common code smells
        code_smell_patterns = [
            ("TODO", "Technical debt markers"),
            ("FIXME", "Known broken code"),
            ("HACK", "Temporary workarounds"),
            ("XXX", "Dangerous code sections"),
            ("@deprecated", "Deprecated code usage"),
            ("eslint-disable", "Linting rule bypasses"),
            ("@ts-ignore", "TypeScript error suppression"),
            ("# type: ignore", "Python type checking bypasses")
        ]
        
        for pattern, description in code_smell_patterns:
            try:
                result = subprocess.run(
                    ['grep', '-r', '-n', '-i', pattern, str(self.project_path)],
                    capture_output=True, text=True, cwd=self.project_path
                )
                
                if result.stdout:
                    matches = result.stdout.split('\n')
                    if matches and matches[0]:  # Has actual content
                        issues.append({
                            "type": "code_smell",
                            "pattern": pattern,
                            "description": description,
                            "count": len([m for m in matches if m.strip()]),
                            "severity": self._classify_severity(pattern),
                            "sample_matches": matches[:5]
                        })
            except Exception:
                continue
        
        self.audit_results["errors"] = issues
        return issues
    
    def assess_architecture(self) -> Dict[str, Any]:
        """Phase 4: Architectural Integrity Assessment"""
        print("🏗️ Phase 4: Assessing architectural integrity...")
        
        architecture = {
            "structure_score": 0,
            "separation_of_concerns": "unknown",
            "error_handling": "unknown",
            "testing_coverage": "unknown",
            "documentation": "unknown"
        }
        
        # Check for common architectural patterns
        structure_indicators = [
            ("models/", "routers/", "services/"),  # Clean separation
            ("src/", "tests/", "docs/"),  # Standard layout
            ("components/", "pages/", "utils/"),  # Frontend patterns
            ("controllers/", "models/", "views/")  # MVC pattern
        ]
        
        for pattern_group in structure_indicators:
            found_dirs = [
                d for d in pattern_group 
                if (self.project_path / d).exists()
            ]
            if len(found_dirs) >= 2:
                architecture["structure_score"] += 10
                architecture["separation_of_concerns"] = "good"
        
        # Check for test directories
        test_dirs = ['tests/', 'test/', '__tests__/', 'spec/']
        has_tests = any((self.project_path / d).exists() for d in test_dirs)
        architecture["testing_coverage"] = "present" if has_tests else "missing"
        
        # Check for documentation
        doc_files = ['README.md', 'docs/', 'CONTRIBUTING.md', 'API.md']
        has_docs = any(
            (self.project_path / f).exists() for f in doc_files
        )
        architecture["documentation"] = "present" if has_docs else "missing"
        
        self.audit_results["architecture"] = architecture
        return architecture
    
    def _classify_severity(self, pattern: str) -> str:
        """Classify issue severity based on pattern"""
        critical_patterns = ["FIXME", "HACK", "XXX", "security", "vulnerability"]
        medium_patterns = ["TODO", "@deprecated", "eslint-disable"]
        
        pattern_lower = pattern.lower()
        
        if any(crit in pattern_lower for crit in critical_patterns):
            return "critical"
        elif any(med in pattern_lower for med in medium_patterns):
            return "medium"
        else:
            return "low"
    
    def generate_audit_report(self) -> str:
        """Generate comprehensive audit report"""
        print("📊 Generating audit report...")
        
        # Calculate severity summary
        for issue in self.audit_results["errors"]:
            severity = issue.get("severity", "low")
            self.audit_results["severity_summary"][severity] += issue.get("count", 1)
        
        total_issues = sum(self.audit_results["severity_summary"].values())
        total_files = self.audit_results["project_info"]["total_files"]
        
        # Calculate health percentage
        if total_files > 0:
            health_percentage = max(0, ((total_files - total_issues) / total_files) * 100)
        else:
            health_percentage = 100
        
        report = f"""
# 🔍 PROJECT-WIDE CODE AUDIT REPORT

## 📊 AUDIT SUMMARY
- **Project Path**: {self.project_path}
- **Total Files Examined**: {total_files}
- **Primary Language**: {self.audit_results['project_info']['primary_language']}
- **Overall Health**: {health_percentage:.1f}%

## 🎯 SEVERITY BREAKDOWN
- **❌ Critical Issues**: {self.audit_results['severity_summary']['critical']}
- **⚠️ Medium Issues**: {self.audit_results['severity_summary']['medium']}
- **🔶 Low Issues**: {self.audit_results['severity_summary']['low']}
- **✅ Clean Areas**: {total_files - total_issues}

## 📁 FILE TYPE DISTRIBUTION
"""
        
        for lang, count in self.audit_results["file_counts"].items():
            if count > 0:
                report += f"- **{lang.title()}**: {count} files\n"
        
        report += "\n## 🚨 IDENTIFIED ISSUES\n"
        
        for issue in self.audit_results["errors"]:
            severity_icon = {"critical": "❌", "medium": "⚠️", "low": "🔶"}.get(issue["severity"], "📝")
            report += f"\n### {severity_icon} {issue['description']}\n"
            report += f"- **Pattern**: `{issue['pattern']}`\n"
            report += f"- **Count**: {issue.get('count', 0)}\n"
            report += f"- **Severity**: {issue['severity']}\n"
        
        report += f"\n## 🏗️ ARCHITECTURE ASSESSMENT\n"
        arch = self.audit_results["architecture"]
        report += f"- **Structure Score**: {arch['structure_score']}/30\n"
        report += f"- **Separation of Concerns**: {arch['separation_of_concerns']}\n"
        report += f"- **Testing Coverage**: {arch['testing_coverage']}\n"
        report += f"- **Documentation**: {arch['documentation']}\n"
        
        # Production readiness assessment
        critical_count = self.audit_results['severity_summary']['critical']
        medium_count = self.audit_results['severity_summary']['medium']
        
        if critical_count == 0 and medium_count < total_files * 0.05:
            readiness = "✅ READY FOR PRODUCTION"
        elif critical_count == 0 and medium_count < total_files * 0.1:
            readiness = "⚠️ NEEDS MINOR FIXES"
        else:
            readiness = "❌ NOT READY FOR PRODUCTION"
        
        report += f"\n## 🚀 PRODUCTION READINESS\n**Status**: {readiness}\n"
        
        return report
    
    def run_full_audit(self) -> str:
        """Run complete audit process"""
        print("🚀 Starting comprehensive code audit...")
        
        self.discover_project_structure()
        self.analyze_imports_and_dependencies()
        self.detect_code_issues()
        self.assess_architecture()
        
        return self.generate_audit_report()


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Project-wide code audit tool")
    parser.add_argument("project_path", help="Path to project directory")
    parser.add_argument("--output", "-o", help="Output file for audit report")
    
    args = parser.parse_args()
    
    # Run audit
    auditor = CodeAuditFramework(args.project_path)
    report = auditor.run_full_audit()
    
    print(report)
    
    # Save report if output specified
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {args.output}")


if __name__ == "__main__":
    main()
