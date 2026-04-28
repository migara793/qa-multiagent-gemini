"""
Production-Grade Code Change Analyzer Service
Version 2.0 - Refactored with pygit2, tree-sitter, and robust error handling

Architectural Improvements:
1. Multi-language AST parsing with tree-sitter (Python, JavaScript, TypeScript)
2. In-memory git operations via pygit2 (libgit2 bindings)
3. Production-grade error handling with specific exception types
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

# Git operations via pygit2 (libgit2 bindings)
import pygit2

# Tree-sitter for multi-language AST parsing
from tree_sitter import Language, Parser, Node, Tree

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models (Unchanged - API compatibility)
# ============================================================================

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


# ============================================================================
# Tree-sitter Language Support
# ============================================================================

class SupportedLanguage(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    UNKNOWN = "unknown"


class TreeSitterParser:
    """
    Multi-language AST parser using tree-sitter
    Supports Python, JavaScript, and TypeScript with extensible architecture
    """

    # Language file mappings
    LANGUAGE_EXTENSIONS = {
        SupportedLanguage.PYTHON: ['.py'],
        SupportedLanguage.JAVASCRIPT: ['.js', '.jsx', '.mjs', '.cjs'],
        SupportedLanguage.TYPESCRIPT: ['.ts', '.tsx'],
    }

    # Tree-sitter query patterns for extracting symbols
    QUERIES = {
        SupportedLanguage.PYTHON: {
            'functions': '(function_definition name: (identifier) @function.name)',
            'classes': '(class_definition name: (identifier) @class.name)',
            'complexity_nodes': [
                'if_statement',
                'while_statement',
                'for_statement',
                'except_clause',
                'boolean_operator',
                'conditional_expression',
            ]
        },
        SupportedLanguage.JAVASCRIPT: {
            'functions': '''
                [
                    (function_declaration name: (identifier) @function.name)
                    (method_definition name: (property_identifier) @function.name)
                    (arrow_function)
                ]
            ''',
            'classes': '(class_declaration name: (identifier) @class.name)',
            'complexity_nodes': [
                'if_statement',
                'while_statement',
                'for_statement',
                'switch_statement',
                'catch_clause',
                'conditional_expression',
                'binary_expression',
            ]
        },
        SupportedLanguage.TYPESCRIPT: {
            'functions': '''
                [
                    (function_declaration name: (identifier) @function.name)
                    (method_definition name: (property_identifier) @function.name)
                    (arrow_function)
                ]
            ''',
            'classes': '(class_declaration name: (identifier) @class.name)',
            'complexity_nodes': [
                'if_statement',
                'while_statement',
                'for_statement',
                'switch_statement',
                'catch_clause',
                'conditional_expression',
                'binary_expression',
            ]
        }
    }

    def __init__(self):
        """Initialize tree-sitter parsers for supported languages"""
        self.parsers: Dict[SupportedLanguage, Parser] = {}
        self.languages: Dict[SupportedLanguage, Language] = {}
        self._initialize_parsers()

    def _initialize_parsers(self) -> None:
        """
        Initialize tree-sitter language parsers
        Note: In production, you'd build language libraries first:

        Build instructions:
        ```bash
        git clone https://github.com/tree-sitter/tree-sitter-python
        git clone https://github.com/tree-sitter/tree-sitter-javascript
        git clone https://github.com/tree-sitter/tree-sitter-typescript

        # Build shared libraries
        python -c "from tree_sitter import Language; Language.build_library(
            'build/languages.so',
            ['tree-sitter-python', 'tree-sitter-javascript', 'tree-sitter-typescript/typescript']
        )"
        ```
        """
        try:
            # Load pre-built language library
            lib_path = Path(__file__).parent / 'build' / 'languages.so'

            if lib_path.exists():
                # Load languages from shared library
                for lang in [SupportedLanguage.PYTHON, SupportedLanguage.JAVASCRIPT, SupportedLanguage.TYPESCRIPT]:
                    try:
                        language = Language(str(lib_path), lang.value)
                        parser = Parser()
                        parser.set_language(language)

                        self.languages[lang] = language
                        self.parsers[lang] = parser
                        logger.info(f"Initialized tree-sitter parser for {lang.value}")
                    except (OSError, ValueError) as e:
                        logger.warning(f"Failed to load {lang.value} parser: {e}")
            else:
                logger.warning(f"Tree-sitter language library not found at {lib_path}. "
                             f"Symbol extraction will be limited. See build instructions in code.")

        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter parsers: {e}")

    def detect_language(self, file_path: str) -> SupportedLanguage:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()

        for lang, extensions in self.LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                return lang

        return SupportedLanguage.UNKNOWN

    def parse_code(self, code: str, language: SupportedLanguage) -> Optional[Tree]:
        """Parse source code and return AST"""
        if language not in self.parsers:
            return None

        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code, 'utf8'))
            return tree
        except Exception as e:
            logger.error(f"Failed to parse {language.value} code: {e}")
            return None

    def extract_functions(self, tree: Tree, language: SupportedLanguage) -> List[str]:
        """Extract function names from AST"""
        if not tree or language not in self.languages:
            return []

        functions = []

        try:
            query_text = self.QUERIES[language]['functions']
            query = self.languages[language].query(query_text)
            captures = query.captures(tree.root_node)

            for node, capture_name in captures:
                if 'function' in capture_name:
                    func_name = node.text.decode('utf8')
                    functions.append(func_name)

        except (KeyError, AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Error extracting functions: {e}")

        return functions

    def extract_classes(self, tree: Tree, language: SupportedLanguage) -> List[str]:
        """Extract class names from AST"""
        if not tree or language not in self.languages:
            return []

        classes = []

        try:
            query_text = self.QUERIES[language]['classes']
            query = self.languages[language].query(query_text)
            captures = query.captures(tree.root_node)

            for node, capture_name in captures:
                if 'class' in capture_name:
                    class_name = node.text.decode('utf8')
                    classes.append(class_name)

        except (KeyError, AttributeError, UnicodeDecodeError) as e:
            logger.debug(f"Error extracting classes: {e}")

        return classes

    def calculate_complexity(self, tree: Tree, language: SupportedLanguage) -> int:
        """
        Calculate cyclomatic complexity from AST
        Complexity = 1 + number of decision points
        """
        if not tree or language not in self.QUERIES:
            return 0

        complexity = 1  # Base complexity

        try:
            complexity_nodes = self.QUERIES[language]['complexity_nodes']

            def count_nodes(node: Node) -> int:
                count = 0
                if node.type in complexity_nodes:
                    count += 1

                for child in node.children:
                    count += count_nodes(child)

                return count

            complexity += count_nodes(tree.root_node)

        except (KeyError, AttributeError) as e:
            logger.debug(f"Error calculating complexity: {e}")

        return complexity


# ============================================================================
# Git Repository Interface (pygit2)
# ============================================================================

class GitRepository:
    """
    Git repository interface using pygit2 (libgit2 bindings)
    Replaces all subprocess git CLI calls with in-memory operations
    """

    def __init__(self, repo_path: str):
        """
        Initialize git repository

        Args:
            repo_path: Path to git repository

        Raises:
            pygit2.GitError: If repository cannot be opened
        """
        self.repo_path = Path(repo_path).resolve()

        try:
            self.repo = pygit2.Repository(str(self.repo_path))
            logger.info(f"Opened git repository: {self.repo_path}")
        except pygit2.GitError as e:
            logger.error(f"Failed to open repository at {repo_path}: {e}")
            raise

    def get_commit(self, ref: str = "HEAD") -> pygit2.Commit:
        """
        Get commit object by reference

        Args:
            ref: Git reference (commit SHA, branch name, or HEAD)

        Returns:
            Commit object

        Raises:
            pygit2.GitError: If reference not found
        """
        try:
            # Resolve reference to commit
            obj = self.repo.revparse_single(ref)

            # Peel to commit if necessary
            if isinstance(obj, pygit2.Tag):
                commit = obj.peel(pygit2.Commit)
            elif isinstance(obj, pygit2.Commit):
                commit = obj
            else:
                raise pygit2.GitError(f"Reference {ref} does not point to a commit")

            return commit

        except (KeyError, pygit2.GitError) as e:
            logger.error(f"Failed to resolve reference {ref}: {e}")
            raise pygit2.GitError(f"Invalid reference: {ref}") from e

    def get_commit_info(self, ref: str = "HEAD") -> Dict[str, str]:
        """
        Extract commit metadata

        Args:
            ref: Git reference

        Returns:
            Dict with sha, author, timestamp, message
        """
        try:
            commit = self.get_commit(ref)

            return {
                'sha': str(commit.id),
                'author': commit.author.name,
                'timestamp': str(commit.commit_time),
                'message': commit.message.strip()
            }

        except pygit2.GitError as e:
            logger.error(f"Failed to get commit info for {ref}: {e}")
            return {
                'sha': 'unknown',
                'author': 'unknown',
                'timestamp': '0',
                'message': ''
            }

    def get_changed_files(self, commit_ref: str = "HEAD") -> List[Tuple[str, str]]:
        """
        Get list of changed files in a commit

        Args:
            commit_ref: Commit reference

        Returns:
            List of (file_path, change_type) tuples
        """
        try:
            commit = self.get_commit(commit_ref)

            # Get parent commit for diff
            if len(commit.parents) == 0:
                # Initial commit - all files are added
                diff = commit.tree.diff_to_tree(swap=True)
            else:
                parent = commit.parents[0]
                diff = parent.tree.diff_to_tree(commit.tree)

            return self._parse_diff_deltas(diff)

        except pygit2.GitError as e:
            logger.error(f"Failed to get changed files for {commit_ref}: {e}")
            return []

    def get_changed_files_range(self, base_ref: str, head_ref: str) -> List[Tuple[str, str]]:
        """
        Get changed files between two references

        Args:
            base_ref: Base reference
            head_ref: Head reference

        Returns:
            List of (file_path, change_type) tuples
        """
        try:
            base_commit = self.get_commit(base_ref)
            head_commit = self.get_commit(head_ref)

            # Create diff between trees
            diff = base_commit.tree.diff_to_tree(head_commit.tree)

            return self._parse_diff_deltas(diff)

        except pygit2.GitError as e:
            logger.error(f"Failed to get changed files for {base_ref}..{head_ref}: {e}")
            return []

    def _parse_diff_deltas(self, diff: pygit2.Diff) -> List[Tuple[str, str]]:
        """Parse diff deltas into (file_path, change_type) tuples"""
        files = []

        for delta in diff.deltas:
            file_path = delta.new_file.path

            # Map pygit2 delta status to change type
            if delta.status == pygit2.GIT_DELTA_ADDED:
                change_type = 'added'
            elif delta.status == pygit2.GIT_DELTA_DELETED:
                change_type = 'deleted'
            elif delta.status == pygit2.GIT_DELTA_MODIFIED:
                change_type = 'modified'
            elif delta.status == pygit2.GIT_DELTA_RENAMED:
                change_type = 'renamed'
            else:
                change_type = 'modified'

            files.append((file_path, change_type))

        return files

    def get_diff_stats(self, commit_ref: str, file_path: str) -> Dict[str, int]:
        """
        Get line addition/deletion stats for a file in a commit

        Args:
            commit_ref: Commit reference
            file_path: Path to file

        Returns:
            Dict with 'added' and 'removed' counts
        """
        try:
            commit = self.get_commit(commit_ref)

            if len(commit.parents) == 0:
                # Initial commit
                diff = commit.tree.diff_to_tree(swap=True)
            else:
                parent = commit.parents[0]
                diff = parent.tree.diff_to_tree(commit.tree)

            # Find specific file in diff
            for patch in diff:
                if patch.delta.new_file.path == file_path:
                    return {
                        'added': patch.line_stats[1],  # insertions
                        'removed': patch.line_stats[2]  # deletions
                    }

            return {'added': 0, 'removed': 0}

        except (pygit2.GitError, IndexError, AttributeError) as e:
            logger.debug(f"Failed to get diff stats for {file_path} in {commit_ref}: {e}")
            return {'added': 0, 'removed': 0}

    def get_diff_stats_range(self, base_ref: str, head_ref: str, file_path: str) -> Dict[str, int]:
        """Get diff stats for file between two refs"""
        try:
            base_commit = self.get_commit(base_ref)
            head_commit = self.get_commit(head_ref)

            diff = base_commit.tree.diff_to_tree(head_commit.tree)

            for patch in diff:
                if patch.delta.new_file.path == file_path:
                    return {
                        'added': patch.line_stats[1],
                        'removed': patch.line_stats[2]
                    }

            return {'added': 0, 'removed': 0}

        except (pygit2.GitError, IndexError, AttributeError) as e:
            logger.debug(f"Failed to get diff stats for {file_path}: {e}")
            return {'added': 0, 'removed': 0}

    def get_file_content(self, ref: str, file_path: str) -> str:
        """
        Get file content at specific commit

        Args:
            ref: Git reference
            file_path: Path to file

        Returns:
            File content as string
        """
        try:
            commit = self.get_commit(ref)

            # Navigate tree to find file
            entry = commit.tree[file_path]

            # Get blob content
            blob = self.repo[entry.id]

            if blob.is_binary:
                return ""

            return blob.data.decode('utf-8', errors='ignore')

        except (pygit2.GitError, KeyError, UnicodeDecodeError, AttributeError) as e:
            logger.debug(f"Failed to get content for {file_path} at {ref}: {e}")
            return ""

    def get_diff_patch(self, commit_ref: str, file_path: str) -> str:
        """Get unified diff patch for a file"""
        try:
            commit = self.get_commit(commit_ref)

            if len(commit.parents) == 0:
                diff = commit.tree.diff_to_tree(swap=True)
            else:
                parent = commit.parents[0]
                diff = parent.tree.diff_to_tree(commit.tree)

            for patch in diff:
                if patch.delta.new_file.path == file_path:
                    return patch.text

            return ""

        except (pygit2.GitError, AttributeError) as e:
            logger.debug(f"Failed to get patch for {file_path}: {e}")
            return ""


# ============================================================================
# Production-Grade Code Analyzer
# ============================================================================

class CodeAnalyzer:
    """
    Production-grade code change analyzer
    Uses pygit2 for git operations and tree-sitter for AST parsing
    """

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
        """
        Initialize code analyzer

        Args:
            repo_path: Path to git repository

        Raises:
            pygit2.GitError: If repository cannot be opened
        """
        self.git = GitRepository(repo_path)
        self.parser = TreeSitterParser()
        logger.info(f"Initialized CodeAnalyzer for {repo_path}")

    def analyze_commit(self, commit_ref: str = "HEAD") -> CodeChangeAnalysis:
        """
        Analyze a specific commit

        Args:
            commit_ref: Git commit reference

        Returns:
            CodeChangeAnalysis with complete analysis data
        """
        # Get commit metadata
        commit_info = self.git.get_commit_info(commit_ref)

        # Get changed files
        changed_files = self.git.get_changed_files(commit_ref)

        # Analyze each file
        file_analyses: List[FileChange] = []
        total_added = 0
        total_removed = 0
        test_files_modified = False
        affected_modules: Set[str] = set()

        for file_path, change_type in changed_files:
            try:
                analysis = self._analyze_file_change(file_path, change_type, commit_ref)

                if analysis:
                    file_analyses.append(analysis)
                    total_added += analysis.lines_added
                    total_removed += analysis.lines_removed

                    if self._is_test_file(file_path):
                        test_files_modified = True

                    module = self._extract_module(file_path)
                    if module:
                        affected_modules.add(module)

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
                continue

        # Calculate risk and suggestions
        risk_score = self._calculate_risk_score(file_analyses, total_added, total_removed)
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
        """
        Analyze diff between two references (for PR analysis)

        Args:
            base_ref: Base git reference
            head_ref: Head git reference

        Returns:
            CodeChangeAnalysis with diff analysis
        """
        # Get diff metadata
        head_info = self.git.get_commit_info(head_ref)

        # Get changed files
        changed_files = self.git.get_changed_files_range(base_ref, head_ref)

        # Analyze each file
        file_analyses: List[FileChange] = []
        total_added = 0
        total_removed = 0
        test_files_modified = False
        affected_modules: Set[str] = set()

        for file_path, change_type in changed_files:
            try:
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

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
                continue

        risk_score = self._calculate_risk_score(file_analyses, total_added, total_removed)
        suggested_test_areas = self._suggest_test_areas(file_analyses)

        return CodeChangeAnalysis(
            commit_sha=f"{base_ref}..{head_ref}",
            commit_message=f"Diff analysis: {base_ref} to {head_ref}",
            author=head_info['author'],
            timestamp=head_info['timestamp'],
            files_changed=file_analyses,
            total_lines_added=total_added,
            total_lines_removed=total_removed,
            risk_score=risk_score,
            affected_modules=list(affected_modules),
            test_files_modified=test_files_modified,
            suggested_test_areas=suggested_test_areas
        )

    def _analyze_file_change(self, file_path: str, change_type: str, commit_ref: str) -> Optional[FileChange]:
        """Analyze a single file change in a commit"""
        # Detect language
        language = self.parser.detect_language(file_path)

        # Get diff stats
        stats = self.git.get_diff_stats(commit_ref, file_path)

        # Get symbols and complexity
        functions: List[str] = []
        classes: List[str] = []
        complexity_delta = 0

        if change_type != 'deleted' and language != SupportedLanguage.UNKNOWN:
            try:
                # Get file content before and after
                before_content = self._get_file_before_commit(file_path, commit_ref)
                after_content = self.git.get_file_content(commit_ref, file_path)

                # Parse and extract symbols from after version
                if after_content:
                    tree = self.parser.parse_code(after_content, language)
                    if tree:
                        functions = self.parser.extract_functions(tree, language)
                        classes = self.parser.extract_classes(tree, language)

                # Calculate complexity delta
                complexity_delta = self._calculate_complexity_delta(
                    before_content, after_content, language
                )

            except Exception as e:
                logger.debug(f"Failed to extract symbols from {file_path}: {e}")

        # Generate diff summary
        diff_summary = self._generate_diff_summary(stats, change_type)

        return FileChange(
            file_path=file_path,
            change_type=change_type,
            lines_added=stats['added'],
            lines_removed=stats['removed'],
            language=language.value,
            functions_changed=functions,
            classes_changed=classes,
            complexity_delta=complexity_delta,
            diff_summary=diff_summary
        )

    def _analyze_file_diff(self, file_path: str, change_type: str,
                          base_ref: str, head_ref: str) -> Optional[FileChange]:
        """Analyze file diff between two refs"""
        language = self.parser.detect_language(file_path)
        stats = self.git.get_diff_stats_range(base_ref, head_ref, file_path)

        functions: List[str] = []
        classes: List[str] = []
        complexity_delta = 0

        if change_type != 'deleted' and language != SupportedLanguage.UNKNOWN:
            try:
                before_content = self.git.get_file_content(base_ref, file_path)
                after_content = self.git.get_file_content(head_ref, file_path)

                if after_content:
                    tree = self.parser.parse_code(after_content, language)
                    if tree:
                        functions = self.parser.extract_functions(tree, language)
                        classes = self.parser.extract_classes(tree, language)

                complexity_delta = self._calculate_complexity_delta(
                    before_content, after_content, language
                )

            except Exception as e:
                logger.debug(f"Failed to extract symbols from {file_path}: {e}")

        diff_summary = self._generate_diff_summary(stats, change_type)

        return FileChange(
            file_path=file_path,
            change_type=change_type,
            lines_added=stats['added'],
            lines_removed=stats['removed'],
            language=language.value,
            functions_changed=functions,
            classes_changed=classes,
            complexity_delta=complexity_delta,
            diff_summary=diff_summary
        )

    def _get_file_before_commit(self, file_path: str, commit_ref: str) -> str:
        """Get file content before a commit (parent commit)"""
        try:
            commit = self.git.get_commit(commit_ref)

            if len(commit.parents) == 0:
                return ""  # Initial commit, no parent

            parent_sha = str(commit.parents[0].id)
            return self.git.get_file_content(parent_sha, file_path)

        except (pygit2.GitError, IndexError) as e:
            logger.debug(f"Failed to get file before commit: {e}")
            return ""

    def _calculate_complexity_delta(self, before_content: str, after_content: str,
                                   language: SupportedLanguage) -> int:
        """Calculate change in cyclomatic complexity"""
        try:
            before_complexity = 0
            after_complexity = 0

            if before_content:
                before_tree = self.parser.parse_code(before_content, language)
                if before_tree:
                    before_complexity = self.parser.calculate_complexity(before_tree, language)

            if after_content:
                after_tree = self.parser.parse_code(after_content, language)
                if after_tree:
                    after_complexity = self.parser.calculate_complexity(after_tree, language)

            return after_complexity - before_complexity

        except Exception as e:
            logger.debug(f"Failed to calculate complexity delta: {e}")
            return 0

    def _generate_diff_summary(self, stats: Dict[str, int], change_type: str) -> str:
        """Generate concise diff summary"""
        if change_type == 'deleted':
            return "File deleted"
        if change_type == 'added':
            return "New file added"

        added = stats['added']
        removed = stats['removed']

        if added == 0 and removed == 0:
            return "No changes"

        return f"{added} insertions(+), {removed} deletions(-)"

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

    def _calculate_risk_score(self, files: List[FileChange],
                             total_added: int, total_removed: int) -> float:
        """
        Calculate risk score (0-100) based on change metrics

        Factors:
        - Number of files changed (0-25 points)
        - Total lines changed (0-25 points)
        - Complexity increase (0-25 points)
        - Core files modified (0-25 points)
        """
        risk = 0.0

        # Factor 1: Number of files
        risk += min(len(files) * 2, 25)

        # Factor 2: Lines changed
        total_lines = total_added + total_removed
        risk += min(total_lines / 10, 25)

        # Factor 3: Complexity increase
        complexity_increase = sum(f.complexity_delta for f in files if f.complexity_delta > 0)
        risk += min(complexity_increase * 5, 25)

        # Factor 4: Core files modified
        core_patterns = ['main', 'core', 'config', 'server', 'app', 'api']
        core_files = sum(1 for f in files if any(p in f.file_path.lower() for p in core_patterns))
        risk += min(core_files * 5, 25)

        return min(risk, 100.0)

    def _suggest_test_areas(self, files: List[FileChange]) -> List[str]:
        """Generate test suggestions based on changes"""
        suggestions: Set[str] = set()

        for file in files:
            # Unit tests for function changes
            if file.functions_changed:
                func_list = ', '.join(file.functions_changed[:3])
                suggestions.add(f"Unit tests for {func_list} in {file.file_path}")

            # Integration tests for modules
            if file.language in ['python', 'javascript', 'typescript']:
                module = self._extract_module(file.file_path)
                if module:
                    suggestions.add(f"Integration tests for {module} module")

            # E2E tests for high-risk changes
            if file.complexity_delta > 5:
                suggestions.add(f"E2E tests for {file.file_path} (high complexity change)")

        return list(suggestions)[:10]


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Command-line interface for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyzer_v2.py <repo_path> [commit_ref]")
        print("\nProduction-grade code analyzer with:")
        print("  - pygit2 for git operations")
        print("  - tree-sitter for multi-language AST parsing")
        print("  - Robust error handling")
        sys.exit(1)

    repo_path = sys.argv[1]
    commit_ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD"

    try:
        analyzer = CodeAnalyzer(repo_path)
        analysis = analyzer.analyze_commit(commit_ref)

        # Output as JSON
        result = asdict(analysis)
        print(json.dumps(result, indent=2))

    except pygit2.GitError as e:
        logger.error(f"Git error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
