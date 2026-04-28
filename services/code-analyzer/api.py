"""
FastAPI REST API for Code Analyzer Service
Provides HTTP endpoints for code change analysis
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uvicorn
from pathlib import Path
import os
from dataclasses import asdict

from analyzer import CodeAnalyzer, CodeChangeAnalysis


app = FastAPI(
    title="Code Change Analyzer API",
    description="Microservice for analyzing code changes and reducing AI token usage",
    version="1.0.0"
)


class AnalyzeCommitRequest(BaseModel):
    """Request model for commit analysis"""
    repo_path: str = Field(..., description="Absolute path to git repository")
    commit_ref: str = Field(default="HEAD", description="Git commit reference")


class AnalyzeDiffRequest(BaseModel):
    """Request model for diff analysis"""
    repo_path: str = Field(..., description="Absolute path to git repository")
    base_ref: str = Field(default="main", description="Base git reference")
    head_ref: str = Field(default="HEAD", description="Head git reference")


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Code Change Analyzer",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/analyze/commit", response_model=AnalysisResponse)
async def analyze_commit(request: AnalyzeCommitRequest):
    """
    Analyze a specific git commit

    Returns structured code change analysis including:
    - Files changed with line stats
    - Functions/classes modified
    - Complexity deltas
    - Risk score
    - Suggested test areas
    """
    try:
        # Validate repo path
        if not Path(request.repo_path).exists():
            raise HTTPException(status_code=400, detail=f"Repository path not found: {request.repo_path}")

        # Check if it's a git repo
        git_dir = Path(request.repo_path) / ".git"
        if not git_dir.exists():
            raise HTTPException(status_code=400, detail=f"Not a git repository: {request.repo_path}")

        # Analyze commit
        analyzer = CodeAnalyzer(request.repo_path)
        analysis = analyzer.analyze_commit(request.commit_ref)

        # Convert to dict
        result = asdict(analysis)

        return AnalysisResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/analyze/diff", response_model=AnalysisResponse)
async def analyze_diff(request: AnalyzeDiffRequest):
    """
    Analyze diff between two git references (for PR analysis)

    Returns structured code change analysis including:
    - Files changed with line stats
    - Functions/classes modified
    - Complexity deltas
    - Risk score
    - Suggested test areas
    """
    try:
        # Validate repo path
        if not Path(request.repo_path).exists():
            raise HTTPException(status_code=400, detail=f"Repository path not found: {request.repo_path}")

        # Check if it's a git repo
        git_dir = Path(request.repo_path) / ".git"
        if not git_dir.exists():
            raise HTTPException(status_code=400, detail=f"Not a git repository: {request.repo_path}")

        # Analyze diff
        analyzer = CodeAnalyzer(request.repo_path)
        analysis = analyzer.analyze_diff(request.base_ref, request.head_ref)

        # Convert to dict
        result = asdict(analysis)

        return AnalysisResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=str(e)
        )


@app.get("/analyze/quick")
async def quick_analyze(
    repo_path: str = Query(..., description="Path to git repository"),
    commit_ref: str = Query(default="HEAD", description="Git commit reference")
):
    """
    Quick analysis endpoint (GET request for convenience)
    Returns minimal analysis for quick checks
    """
    try:
        # Validate repo path
        if not Path(repo_path).exists():
            raise HTTPException(status_code=400, detail=f"Repository path not found: {repo_path}")

        analyzer = CodeAnalyzer(repo_path)
        analysis = analyzer.analyze_commit(commit_ref)

        # Return simplified response
        return {
            "success": True,
            "summary": {
                "commit": analysis.commit_sha[:8],
                "files_changed": len(analysis.files_changed),
                "lines_added": analysis.total_lines_added,
                "lines_removed": analysis.total_lines_removed,
                "risk_score": round(analysis.risk_score, 1),
                "test_files_modified": analysis.test_files_modified,
                "affected_modules": analysis.affected_modules,
                "suggested_tests": len(analysis.suggested_test_areas)
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/analyze/batch")
async def batch_analyze(commits: list[str], repo_path: str):
    """
    Analyze multiple commits in batch
    Useful for analyzing entire PR or commit range
    """
    try:
        if not Path(repo_path).exists():
            raise HTTPException(status_code=400, detail=f"Repository path not found: {repo_path}")

        analyzer = CodeAnalyzer(repo_path)
        results = []

        for commit_ref in commits:
            try:
                analysis = analyzer.analyze_commit(commit_ref)
                results.append({
                    "commit": commit_ref,
                    "success": True,
                    "data": asdict(analysis)
                })
            except Exception as e:
                results.append({
                    "commit": commit_ref,
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": True,
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Run with: uvicorn api:app --host 0.0.0.0 --port 8001 --reload
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8001")),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
