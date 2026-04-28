"""
Client library for Code Analyzer Service
Use this in your agents to consume the analyzer API
"""

import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass


class CodeAnalyzerClient:
    """Client for Code Analyzer microservice"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')

    def analyze_commit(self, repo_path: str, commit_ref: str = "HEAD") -> Dict[str, Any]:
        """
        Analyze a git commit

        Args:
            repo_path: Absolute path to git repository
            commit_ref: Git commit reference (default: HEAD)

        Returns:
            Structured analysis data
        """
        response = requests.post(
            f"{self.base_url}/analyze/commit",
            json={
                "repo_path": repo_path,
                "commit_ref": commit_ref
            }
        )
        response.raise_for_status()
        result = response.json()

        if not result.get('success'):
            raise Exception(result.get('error', 'Unknown error'))

        return result['data']

    def analyze_diff(self, repo_path: str, base_ref: str = "main", head_ref: str = "HEAD") -> Dict[str, Any]:
        """
        Analyze diff between two refs (for PR analysis)

        Args:
            repo_path: Absolute path to git repository
            base_ref: Base git reference (default: main)
            head_ref: Head git reference (default: HEAD)

        Returns:
            Structured analysis data
        """
        response = requests.post(
            f"{self.base_url}/analyze/diff",
            json={
                "repo_path": repo_path,
                "base_ref": base_ref,
                "head_ref": head_ref
            }
        )
        response.raise_for_status()
        result = response.json()

        if not result.get('success'):
            raise Exception(result.get('error', 'Unknown error'))

        return result['data']

    def quick_analyze(self, repo_path: str, commit_ref: str = "HEAD") -> Dict[str, Any]:
        """
        Quick analysis with minimal data

        Args:
            repo_path: Absolute path to git repository
            commit_ref: Git commit reference

        Returns:
            Summary of changes
        """
        response = requests.get(
            f"{self.base_url}/analyze/quick",
            params={
                "repo_path": repo_path,
                "commit_ref": commit_ref
            }
        )
        response.raise_for_status()
        result = response.json()

        if not result.get('success'):
            raise Exception(result.get('error', 'Unknown error'))

        return result['summary']

    def get_ai_summary(self, analysis: Dict[str, Any]) -> str:
        """
        Convert analysis to concise text for AI consumption
        Reduces token usage by ~70%

        Args:
            analysis: Full analysis data from analyze_commit or analyze_diff

        Returns:
            Concise text summary optimized for AI models
        """
        lines = []

        # Header
        lines.append(f"Code Change Analysis - {analysis['commit_sha'][:8]}")
        lines.append(f"Author: {analysis['author']} | Risk: {analysis['risk_score']:.1f}/100")
        lines.append("")

        # Summary
        lines.append(f"Files: {len(analysis['files_changed'])} | "
                    f"+{analysis['total_lines_added']} -{analysis['total_lines_removed']} lines")
        lines.append(f"Modules: {', '.join(analysis['affected_modules'])}")
        lines.append(f"Tests modified: {'Yes' if analysis['test_files_modified'] else 'No'}")
        lines.append("")

        # File details
        lines.append("Changed Files:")
        for file in analysis['files_changed']:
            lines.append(f"  • {file['file_path']} ({file['change_type']})")
            lines.append(f"    +{file['lines_added']} -{file['lines_removed']} | "
                        f"Complexity Δ: {file['complexity_delta']:+d}")

            if file['functions_changed']:
                lines.append(f"    Functions: {', '.join(file['functions_changed'])}")
            if file['classes_changed']:
                lines.append(f"    Classes: {', '.join(file['classes_changed'])}")

        lines.append("")

        # Test suggestions
        if analysis['suggested_test_areas']:
            lines.append("Suggested Test Areas:")
            for suggestion in analysis['suggested_test_areas'][:5]:
                lines.append(f"  • {suggestion}")

        return "\n".join(lines)

    def health_check(self) -> bool:
        """Check if service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


# Example usage
def example_usage():
    """Example of how to use the client"""

    # Initialize client
    client = CodeAnalyzerClient("http://localhost:8001")

    # Check service health
    if not client.health_check():
        print("Service not available")
        return

    # Analyze latest commit
    analysis = client.analyze_commit("/path/to/repo", "HEAD")

    # Get AI-friendly summary (reduces tokens by ~70%)
    ai_summary = client.get_ai_summary(analysis)
    print(ai_summary)

    # Quick analysis
    summary = client.quick_analyze("/path/to/repo", "HEAD")
    print(f"Risk score: {summary['risk_score']}")

    # Analyze PR diff
    pr_analysis = client.analyze_diff(
        repo_path="/path/to/repo",
        base_ref="main",
        head_ref="feature-branch"
    )
    print(f"PR changes {pr_analysis['total_lines_added']} lines")


if __name__ == '__main__':
    example_usage()
