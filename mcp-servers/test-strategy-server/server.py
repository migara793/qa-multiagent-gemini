"""
MCP Server: Test Strategy Generation
MCP Specification: https://modelcontextprotocol.io/specification/
FastAPI: https://fastapi.tiangolo.com/
Gemini API: https://ai.google.dev/gemini-api/docs
"""
import os
import json
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"))

# Create FastAPI app
app = FastAPI(
    title="Test Strategy MCP Server",
    description="MCP server for generating test strategies using Gemini AI",
    version="1.0.0"
)


class ToolCallRequest(BaseModel):
    """MCP tool call request"""
    name: str
    parameters: Dict[str, Any]


class ToolResponse(BaseModel):
    """MCP tool response"""
    result: Dict[str, Any]


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "server": "test-strategy-mcp-server",
        "version": "1.0.0",
        "protocol": "MCP",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "test-strategy"}


@app.post("/mcp/call-tool")
async def call_tool(request: ToolCallRequest) -> Dict[str, Any]:
    """
    Handle MCP tool calls

    MCP Specification: Tool Calling
    Reference: https://modelcontextprotocol.io/specification/
    """
    if request.name == "generate_strategy":
        return await generate_test_strategy(request.parameters)

    elif request.name == "impact_analysis":
        return await analyze_impact(request.parameters)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown tool: {request.name}"
        )


async def generate_test_strategy(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate test strategy based on code analysis using Gemini AI

    Args:
        params: Dictionary containing code_analysis and trigger_type

    Returns:
        Test strategy with recommended test types and priorities
    """
    try:
        code_analysis = params.get("code_analysis", {})
        trigger_type = params.get("trigger_type", "pull_request")

        # Create prompt for Gemini
        prompt = f"""
Analyze this code change and generate a comprehensive test strategy.

Changed Files: {code_analysis.get('changed_files', [])}
Lines Changed: +{code_analysis.get('lines_added', 0)} -{code_analysis.get('lines_removed', 0)}
Complexity: {code_analysis.get('complexity', {})}
Risk Level: {code_analysis.get('risk_level', 'medium')}
Trigger Type: {trigger_type}

Based on this analysis, determine:
1. Which test types should run (choose from: unit, integration, e2e, performance, security)
2. Priority level (choose one: critical, high, medium, low)
3. Estimated test duration in seconds
4. Whether parallel execution is recommended (true/false)

Return ONLY a valid JSON object with these exact keys:
- test_types: array of strings
- priority: string
- estimated_duration: integer
- parallel_execution: boolean

Example response:
{{"test_types": ["unit", "integration", "security"], "priority": "high", "estimated_duration": 300, "parallel_execution": true}}
"""

        # Call Gemini API
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Parse JSON from response (remove markdown code blocks if present)
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()

        try:
            strategy = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback strategy if Gemini returns invalid JSON
            strategy = {
                "test_types": ["unit", "integration"],
                "priority": "medium",
                "estimated_duration": 180,
                "parallel_execution": True
            }

        # Add metadata
        strategy["affected_components"] = code_analysis.get("changed_files", [])
        strategy["regression_required"] = len(code_analysis.get("changed_files", [])) > 5

        return strategy

    except Exception as e:
        # Return fallback strategy on error
        return {
            "test_types": ["unit"],
            "priority": "medium",
            "estimated_duration": 120,
            "parallel_execution": False,
            "error": str(e)
        }


async def analyze_impact(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze impact of code changes

    Args:
        params: Dictionary containing changed_files and commit_sha

    Returns:
        Impact analysis with risk assessment
    """
    changed_files = params.get("changed_files", [])

    # Simple heuristic-based impact analysis
    risk_level = "low"

    if len(changed_files) > 10:
        risk_level = "high"
    elif len(changed_files) > 5:
        risk_level = "medium"

    # Check for critical files
    critical_patterns = ["auth", "security", "payment", "database", "migration"]
    for file in changed_files:
        if any(pattern in file.lower() for pattern in critical_patterns):
            risk_level = "high"
            break

    affected_modules = list(set([
        file.split("/")[0] if "/" in file else "root"
        for file in changed_files
    ]))

    return {
        "risk_level": risk_level,
        "affected_modules": affected_modules,
        "requires_full_regression": risk_level == "high" or len(changed_files) > 10,
        "changed_file_count": len(changed_files)
    }


@app.get("/mcp/list-tools")
async def list_tools() -> List[Dict[str, Any]]:
    """
    List available MCP tools

    MCP Specification: Tool Discovery
    """
    return [
        {
            "name": "generate_strategy",
            "description": "Generate comprehensive test strategy using Gemini AI",
            "parameters": {
                "code_analysis": "dict - Code analysis results",
                "trigger_type": "str - Type of trigger (push, pull_request, etc.)"
            }
        },
        {
            "name": "impact_analysis",
            "description": "Analyze impact of code changes",
            "parameters": {
                "changed_files": "list - List of changed file paths",
                "commit_sha": "str - Git commit SHA"
            }
        }
    ]


@app.get("/mcp/list-resources")
async def list_resources() -> List[Dict[str, Any]]:
    """List available MCP resources"""
    return []


@app.get("/mcp/list-prompts")
async def list_prompts() -> List[Dict[str, Any]]:
    """List available MCP prompts"""
    return []


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", 3005))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
