"""
Code Change Analyzer Service
Extracts and analyzes code changes from git repositories
Reduces AI token usage by preprocessing code changes locally
"""

import os
import re
import ast
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass
class FileChange:
    """Represents a single file change"""
    file_path: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    lines_added: int
    lines_removed: int
    language: str
    functions_changed: List[str]
    classes_changed: List[str]
    complexity_delta: int  # Change in cyclomatic complexity
    diff_summary: str  # Concise summary of changes


@dataclass
class CodeChangeAnalysis:
    """Complete analysis of code changes"""
    commit_sha: str
    commit_message: str
    author: str
    timestamp: str
    files_changed: List[FileChange]
    total_lines_added: int
    total_lines_removed: int
    risk_score: float  # 0-100, based on complexity and scope
    affected_modules: List[str]
    test_files_modified: bool
    suggested_test_areas: List[str]


class CodeAnalyzer:
    """Analyzes code changes from git repositories"""

    # File extensions by language
    LANGUAGE_EXTENSIONS = {
        'python': ['.py'],
        'javascript': ['.js', '.jsx'],
        'typescript': ['.ts', '.tsx'],
        'java': ['.java'],
        'go': ['.go'],
        'rust': ['.rs'],
        'cpp': ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
        'c': ['.c', '.h'],
        'ruby': ['.rb'],
        'php': ['.php'],
    }

    # Test file patterns
    TEST_PATTERNS = [
        r'test_.*\.py$',
        r'.*_test\.py$',
        r'.*\.test\.(js|ts)$',
        r'.*\.spec\.(js|ts)$',
        r'.*/tests?/.*',
        r'.*/spec/.*',
    ]

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def analyze_commit(self, commit_ref: str = "HEAD") -> CodeChangeAnalysis:
        """Analyze a specific commit"""
        # Get commit info
        commit_info = self._get_commit_info(commit_ref)

        # Get changed files
        changed_files = self._get_changed_files(commit_ref)

        # Analyze each file
        file_analyses = []
        total_added = 0
        total_removed = 0
        test_files_modified = False
        affected_modules = set()

        for file_path, change_type in changed_files:
            analysis = self._analyze_file_change(file_path, change_type, commit_ref)
            if analysis:
                file_analyses.append(analysis)
                total_added += analysis.lines_added
                total_removed += analysis.lines_removed

                # Check if test file
                if self._is_test_file(file_path):
                    test_files_modified = True

                # Extract module
                module = self._extract_module(file_path)
                if module:
                    affected_modules.add(module)

        # Calculate risk score
        risk_score = self._calculate_risk_score(file_analyses, total_added, total_removed)

        # Suggest test areas
        suggested_test_areas = self._suggest_test_areas(file_analyses)

        return CodeChangeAnalysis(
            commit_sha=commit_info['sha'],
            commit_message=commit_info['message'],
            author=commit_info['author'],
            timestamp=commit_info['timestamp'],
            files_changed=file_analyses,
            total_lines_added=total_added,
            total_lines_removed=total_removed,
            risk_score=risk_score,
            affected_modules=list(affected_modules),
            test_files_modified=test_files_modified,
            suggested_test_areas=suggested_test_areas
        )

    def analyze_diff(self, base_ref: str = "main", head_ref: str = "HEAD") -> CodeChangeAnalysis:
        """Analyze diff between two refs (for PRs)"""
        # Get diff stats
        diff_info = self._get_diff_info(base_ref, head_ref)

        # Get changed files in range
        changed_files = self._get_changed_files_range(base_ref, head_ref)

        # Analyze each file
        file_analyses = []
        total_added = 0
        total_removed = 0
        test_files_modified = False
        affected_modules = set()

        for file_path, change_type in changed_files:
            analysis = self._analyze_file_diff(file_path, change_type, base_ref, head_ref)
            if analysis:
                file_analyses.append(analysis)
                total_added += analysis.lines_added
                total_removed += analysis.lines_removed

                if self._is_test_file(file_path):
                    test_files_modified = True

                module = self._extract_module(file_path)
                if module:
                    affected_modules.add(module)

        risk_score = self._calculate_risk_score(file_analyses, total_added, total_removed)
        suggested_test_areas = self._suggest_test_areas(file_analyses)

        return CodeChangeAnalysis(
            commit_sha=f"{base_ref}..{head_ref}",
            commit_message=f"Diff analysis: {base_ref} to {head_ref}",
            author=diff_info.get('author', 'multiple'),
            timestamp=diff_info.get('timestamp', ''),
            files_changed=file_analyses,
            total_lines_added=total_added,
            total_lines_removed=total_removed,
            risk_score=risk_score,
            affected_modules=list(affected_modules),
            test_files_modified=test_files_modified,
            suggested_test_areas=suggested_test_areas
        )

    def _get_commit_info(self, commit_ref: str) -> Dict:
        """Get commit metadata"""
        cmd = [
            'git', '-C', str(self.repo_path), 'show', '--no-patch',
            '--format=%H%n%an%n%at%n%s', commit_ref
        ]
        output = subprocess.check_output(cmd, text=True).strip().split('\n')

        return {
            'sha': output[0],
            'author': output[1],
            'timestamp': output[2],
            'message': output[3] if len(output) > 3 else ''
        }

    def _get_diff_info(self, base_ref: str, head_ref: str) -> Dict:
        """Get diff metadata"""
        cmd = [
            'git', '-C', str(self.repo_path), 'log',
            '--format=%an%n%at', f"{base_ref}..{head_ref}", '-1'
        ]
        try:
            output = subprocess.check_output(cmd, text=True).strip().split('\n')
            return {
                'author': output[0] if output else 'unknown',
                'timestamp': output[1] if len(output) > 1 else ''
            }
        except:
            return {'author': 'unknown', 'timestamp': ''}

    def _get_changed_files(self, commit_ref: str) -> List[Tuple[str, str]]:
        """Get list of changed files in commit"""
        cmd = [
            'git', '-C', str(self.repo_path), 'diff-tree', '--no-commit-id',
            '--name-status', '-r', commit_ref
        ]
        output = subprocess.check_output(cmd, text=True).strip()

        files = []
        for line in output.split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            status = parts[0]
            file_path = parts[1]

            change_type = self._map_git_status(status)
            files.append((file_path, change_type))

        return files

    def _get_changed_files_range(self, base_ref: str, head_ref: str) -> List[Tuple[str, str]]:
        """Get changed files between two refs"""
        cmd = [
            'git', '-C', str(self.repo_path), 'diff',
            '--name-status', f"{base_ref}...{head_ref}"
        ]
        output = subprocess.check_output(cmd, text=True).strip()

        files = []
        for line in output.split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            status = parts[0]
            file_path = parts[1]

            change_type = self._map_git_status(status)
            files.append((file_path, change_type))

        return files

    def _map_git_status(self, status: str) -> str:
        """Map git status to change type"""
        if status.startswith('A'):
            return 'added'
        elif status.startswith('M'):
            return 'modified'
        elif status.startswith('D'):
            return 'deleted'
        elif status.startswith('R'):
            return 'renamed'
        return 'modified'

    def _analyze_file_change(self, file_path: str, change_type: str, commit_ref: str) -> Optional[FileChange]:
        """Analyze a single file change"""
        language = self._detect_language(file_path)

        # Get diff stats for this file
        stats = self._get_file_diff_stats(file_path, commit_ref)

        # Get changed functions/classes
        functions, classes = self._get_changed_symbols(file_path, commit_ref, language)

        # Calculate complexity delta
        complexity_delta = self._calculate_complexity_delta(file_path, commit_ref, language)

        # Generate concise diff summary
        diff_summary = self._generate_diff_summary(file_path, commit_ref, change_type)

        return FileChange(
            file_path=file_path,
            change_type=change_type,
            lines_added=stats['added'],
            lines_removed=stats['removed'],
            language=language,
            functions_changed=functions,
            classes_changed=classes,
            complexity_delta=complexity_delta,
            diff_summary=diff_summary
        )

    def _analyze_file_diff(self, file_path: str, change_type: str, base_ref: str, head_ref: str) -> Optional[FileChange]:
        """Analyze file diff between refs"""
        language = self._detect_language(file_path)

        stats = self._get_file_diff_stats_range(file_path, base_ref, head_ref)
        functions, classes = self._get_changed_symbols_range(file_path, base_ref, head_ref, language)
        complexity_delta = self._calculate_complexity_delta_range(file_path, base_ref, head_ref, language)
        diff_summary = self._generate_diff_summary_range(file_path, base_ref, head_ref, change_type)

        return FileChange(
            file_path=file_path,
            change_type=change_type,
            lines_added=stats['added'],
            lines_removed=stats['removed'],
            language=language,
            functions_changed=functions,
            classes_changed=classes,
            complexity_delta=complexity_delta,
            diff_summary=diff_summary
        )

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix
        for lang, extensions in self.LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                return lang
        return 'unknown'

    def _parse_numstat_line(self, output: str) -> Dict[str, int]:
        """Parse numstat output — find the data line (skips commit header lines)"""
        for line in output.split('\n'):
            parts = line.strip().split('\t')
            if len(parts) == 3 and parts[0] != '-' and parts[1] != '-':
                try:
                    return {'added': int(parts[0]), 'removed': int(parts[1])}
                except ValueError:
                    continue
        return {'added': 0, 'removed': 0}

    def _get_file_diff_stats(self, file_path: str, commit_ref: str) -> Dict[str, int]:
        """Get line addition/deletion stats for file"""
        cmd = [
            'git', '-C', str(self.repo_path), 'show',
            '--numstat', commit_ref, '--', file_path
        ]
        try:
            output = subprocess.check_output(cmd, text=True)
            return self._parse_numstat_line(output)
        except:
            pass
        return {'added': 0, 'removed': 0}

    def _get_file_diff_stats_range(self, file_path: str, base_ref: str, head_ref: str) -> Dict[str, int]:
        """Get diff stats between refs"""
        cmd = [
            'git', '-C', str(self.repo_path), 'diff',
            '--numstat', f"{base_ref}...{head_ref}", '--', file_path
        ]
        try:
            output = subprocess.check_output(cmd, text=True)
            return self._parse_numstat_line(output)
        except:
            pass
        return {'added': 0, 'removed': 0}

    # JS/TS function definition patterns
    JS_FUNCTION_PATTERNS = [
        r'function\s+(\w+)\s*\(',                        # function foo(
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function', # const foo = function
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(', # const foo = async (
        r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{',         # foo() {
        r'app\.(?:get|post|put|delete|patch)\s*\([\'\"](.*?)[\'\"]', # express routes
    ]

    JS_CLASS_PATTERNS = [
        r'class\s+(\w+)',                                # class Foo
    ]

    def _get_changed_symbols(self, file_path: str, commit_ref: str, language: str) -> Tuple[List[str], List[str]]:
        """Extract changed function and class names"""
        if language == 'python':
            return self._get_python_symbols_commit(file_path, commit_ref)
        elif language in ('javascript', 'typescript'):
            return self._get_js_symbols_commit(file_path, commit_ref)
        return [], []

    def _get_python_symbols_commit(self, file_path: str, commit_ref: str) -> Tuple[List[str], List[str]]:
        """Extract changed Python symbols from a commit"""
        try:
            cmd = [
                'git', '-C', str(self.repo_path), 'show',
                '-U0', '--function-context', commit_ref, '--', file_path
            ]
            diff_output = subprocess.check_output(cmd, text=True)
            return self._parse_python_symbols(diff_output)
        except:
            return [], []

    def _get_js_symbols_commit(self, file_path: str, commit_ref: str) -> Tuple[List[str], List[str]]:
        """Extract changed JS/TS symbols from a commit diff"""
        try:
            cmd = [
                'git', '-C', str(self.repo_path), 'show',
                commit_ref, '--', file_path
            ]
            diff_output = subprocess.check_output(cmd, text=True)
            return self._parse_js_symbols(diff_output)
        except:
            return [], []

    def _parse_python_symbols(self, diff_output: str) -> Tuple[List[str], List[str]]:
        """Parse Python function/class names from diff hunk headers"""
        functions = set()
        classes = set()
        for line in diff_output.split('\n'):
            if line.startswith('@@'):
                match = re.search(r'@@.*@@\s+(.*)', line)
                if match:
                    symbol = match.group(1).strip()
                    if symbol.startswith('def '):
                        functions.add(symbol.split('(')[0].replace('def ', '').strip())
                    elif symbol.startswith('class '):
                        classes.add(symbol.split('(')[0].split(':')[0].replace('class ', '').strip())
        return list(functions), list(classes)

    def _parse_js_symbols(self, diff_output: str) -> Tuple[List[str], List[str]]:
        """Parse JS/TS function/class names from added/modified diff lines"""
        functions = set()
        classes = set()
        for line in diff_output.split('\n'):
            if not line.startswith('+') or line.startswith('+++'):
                continue
            content = line[1:]
            for pattern in self.JS_FUNCTION_PATTERNS:
                match = re.search(pattern, content)
                if match:
                    functions.add(match.group(1))
                    break
            for pattern in self.JS_CLASS_PATTERNS:
                match = re.search(pattern, content)
                if match:
                    classes.add(match.group(1))
        return list(functions), list(classes)

    def _get_changed_symbols_range(self, file_path: str, base_ref: str, head_ref: str, language: str) -> Tuple[List[str], List[str]]:
        """Extract changed symbols in diff range"""
        if language == 'python':
            return self._get_python_symbols_range(file_path, base_ref, head_ref)
        elif language in ('javascript', 'typescript'):
            return self._get_js_symbols_range(file_path, base_ref, head_ref)
        return [], []

    def _get_python_symbols_range(self, file_path: str, base_ref: str, head_ref: str) -> Tuple[List[str], List[str]]:
        """Extract Python symbols from diff range"""
        try:
            cmd = [
                'git', '-C', str(self.repo_path), 'diff',
                '-U0', '--function-context', f"{base_ref}...{head_ref}", '--', file_path
            ]
            diff_output = subprocess.check_output(cmd, text=True)
            return self._parse_python_symbols(diff_output)
        except:
            return [], []

    def _get_js_symbols_range(self, file_path: str, base_ref: str, head_ref: str) -> Tuple[List[str], List[str]]:
        """Extract JS/TS symbols from diff range"""
        try:
            cmd = [
                'git', '-C', str(self.repo_path), 'diff',
                f"{base_ref}...{head_ref}", '--', file_path
            ]
            diff_output = subprocess.check_output(cmd, text=True)
            return self._parse_js_symbols(diff_output)
        except:
            return [], []

    def _calculate_complexity_delta(self, file_path: str, commit_ref: str, language: str) -> int:
        """Calculate change in cyclomatic complexity"""
        try:
            before_content = self._get_file_at_commit(file_path, f"{commit_ref}^")
            after_content = self._get_file_at_commit(file_path, commit_ref)
            return self._complexity(after_content, language) - self._complexity(before_content, language)
        except:
            return 0

    def _calculate_complexity_delta_range(self, file_path: str, base_ref: str, head_ref: str, language: str) -> int:
        """Calculate complexity delta for range"""
        try:
            before_content = self._get_file_at_commit(file_path, base_ref)
            after_content = self._get_file_at_commit(file_path, head_ref)
            return self._complexity(after_content, language) - self._complexity(before_content, language)
        except:
            return 0

    def _complexity(self, code: str, language: str) -> int:
        """Route complexity calculation by language"""
        if language == 'python':
            return self._calculate_python_complexity(code)
        elif language in ('javascript', 'typescript'):
            return self._calculate_js_complexity(code)
        return 0

    def _calculate_js_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity for JS/TS code.
        Counts every decision point: if, else if, for, while, case, catch, &&, ||, ternary ?
        """
        if not code:
            return 0
        complexity = 1  # base
        # Remove strings and comments to avoid false matches
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        code = re.sub(r'`[^`]*`', '``', code)

        decision_patterns = [
            r'\bif\b',
            r'\belse\s+if\b',
            r'\bfor\b',
            r'\bwhile\b',
            r'\bcase\b',
            r'\bcatch\b',
            r'\?\s*\w',   # ternary operator
            r'&&',
            r'\|\|',
        ]
        for pattern in decision_patterns:
            complexity += len(re.findall(pattern, code))
        return complexity

    def _get_file_at_commit(self, file_path: str, commit_ref: str) -> str:
        """Get file content at specific commit"""
        cmd = ['git', '-C', str(self.repo_path), 'show', f"{commit_ref}:{file_path}"]
        try:
            return subprocess.check_output(cmd, text=True)
        except:
            return ""

    def _calculate_python_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity for Python code"""
        try:
            tree = ast.parse(code)
            complexity = 1  # Base complexity

            for node in ast.walk(tree):
                # Each decision point adds 1 to complexity
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return complexity
        except:
            return 0

    def _generate_diff_summary(self, file_path: str, commit_ref: str, change_type: str) -> str:
        """Generate concise summary of changes"""
        if change_type == 'deleted':
            return f"File deleted"
        if change_type == 'added':
            return f"New file added"

        try:
            cmd = ['git', '-C', str(self.repo_path), 'show', '--stat', commit_ref, '--', file_path]
            output = subprocess.check_output(cmd, text=True).strip()
            # Extract just the stat line
            lines = output.split('\n')
            for line in lines:
                if file_path in line:
                    return line.split('|')[1].strip() if '|' in line else "Modified"
        except:
            pass
        return "Modified"

    def _generate_diff_summary_range(self, file_path: str, base_ref: str, head_ref: str, change_type: str) -> str:
        """Generate diff summary for range"""
        if change_type == 'deleted':
            return f"File deleted"
        if change_type == 'added':
            return f"New file added"

        try:
            cmd = ['git', '-C', str(self.repo_path), 'diff', '--stat', f"{base_ref}...{head_ref}", '--', file_path]
            output = subprocess.check_output(cmd, text=True).strip()
            lines = output.split('\n')
            for line in lines:
                if file_path in line:
                    return line.split('|')[1].strip() if '|' in line else "Modified"
        except:
            pass
        return "Modified"

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file"""
        for pattern in self.TEST_PATTERNS:
            if re.search(pattern, file_path):
                return True
        return False

    def _extract_module(self, file_path: str) -> Optional[str]:
        """Extract module name from file path"""
        parts = Path(file_path).parts
        if len(parts) > 0:
            return parts[0]
        return None

    def _calculate_risk_score(self, files: List[FileChange], total_added: int, total_removed: int) -> float:
        """Calculate risk score (0-100)"""
        risk = 0.0

        # Factor 1: Number of files (0-25 points)
        risk += min(len(files) * 2, 25)

        # Factor 2: Lines changed (0-25 points)
        total_lines = total_added + total_removed
        risk += min(total_lines / 10, 25)

        # Factor 3: Complexity increase (0-25 points)
        complexity_increase = sum(f.complexity_delta for f in files if f.complexity_delta > 0)
        risk += min(complexity_increase * 5, 25)

        # Factor 4: Core files modified (0-25 points)
        core_patterns = ['main', 'core', 'config', 'server', 'app']
        core_files = sum(1 for f in files if any(p in f.file_path.lower() for p in core_patterns))
        risk += min(core_files * 5, 25)

        return min(risk, 100)

    def _suggest_test_areas(self, files: List[FileChange]) -> List[str]:
        """Suggest test areas based on changes"""
        suggestions = set()

        for file in files:
            # Suggest unit tests for function changes
            if file.functions_changed:
                suggestions.add(f"Unit tests for {', '.join(file.functions_changed[:3])} in {file.file_path}")

            # Suggest integration tests for module changes
            if file.language in ['python', 'javascript', 'typescript']:
                module = self._extract_module(file.file_path)
                if module:
                    suggestions.add(f"Integration tests for {module} module")

            # Suggest E2E tests for high-risk changes
            if file.complexity_delta > 5:
                suggestions.add(f"E2E tests for {file.file_path} (high complexity change)")

        return list(suggestions)[:10]  # Limit to top 10


def main():
    """CLI for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <repo_path> [commit_ref]")
        sys.exit(1)

    repo_path = sys.argv[1]
    commit_ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD"

    analyzer = CodeAnalyzer(repo_path)
    analysis = analyzer.analyze_commit(commit_ref)

    # Convert to dict and print as JSON
    result = asdict(analysis)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
