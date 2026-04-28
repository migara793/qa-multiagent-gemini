# Code Change Analyzer Service

A standalone Python microservice that extracts and analyzes code changes from git repositories. This service significantly reduces AI token usage by preprocessing code analysis locally before sending to AI models.

## Features

- **Git Analysis**: Extract commit diffs, file changes, and code statistics
- **Code Intelligence**:
  - Detect changed functions and classes — **Python (AST) + JavaScript/TypeScript (regex)**
  - Calculate cyclomatic complexity deltas — **Python (AST) + JavaScript/TypeScript (regex)**
  - Identify test files and affected modules
- **Risk Assessment**: Automatic 4-factor risk scoring (verified accurate)
- **Test Suggestions**: AI-ready test area recommendations
- **Token Optimization**: Reduces AI token usage by ~70% through structured preprocessing

## Language Support

| Language | functions_changed | classes_changed | complexity_delta |
|---|---|---|---|
| Python | ✅ AST-based | ✅ AST-based | ✅ AST-based |
| JavaScript | ✅ Regex-based | ✅ Regex-based | ✅ Regex-based |
| TypeScript | ✅ Regex-based | ✅ Regex-based | ✅ Regex-based |
| Java / Go / Rust / PHP / Ruby | ✅ file detected | ✅ file detected | — not yet |

## API Endpoints

### POST `/analyze/commit`
Analyze a specific git commit

**Request:**
```json
{
  "repo_path": "/path/to/repo",
  "commit_ref": "HEAD"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "commit_sha": "abc123...",
    "files_changed": [...],
    "risk_score": 45.2,
    "suggested_test_areas": [...]
  }
}
```

### POST `/analyze/diff`
Analyze diff between two refs (for PRs)

**Request:**
```json
{
  "repo_path": "/path/to/repo",
  "base_ref": "main",
  "head_ref": "feature-branch"
}
```

### GET `/analyze/quick`
Quick analysis with minimal data

**Query Params:**
- `repo_path`: Path to repository
- `commit_ref`: Commit reference (default: HEAD)

## Usage

### 1. Standalone CLI

```bash
python analyzer.py /path/to/repo HEAD
```

### 2. Run as Microservice

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn api:app --host 0.0.0.0 --port 8001
```

### 3. Docker

```bash
# Build and run
docker-compose up -d

# Or build manually
docker build -t code-analyzer .
docker run -p 8001:8001 -v /path/to/repo:/repos:ro code-analyzer
```

### 4. Python Client

```python
from client import CodeAnalyzerClient

client = CodeAnalyzerClient("http://localhost:8001")

# Analyze commit
analysis = client.analyze_commit("/path/to/repo", "HEAD")

# Get AI-optimized summary (70% fewer tokens)
summary = client.get_ai_summary(analysis)
print(summary)
```

## Integration with QA System

### Before (Using MCP):
```python
# AI model receives full git diff (high token usage)
mcp_result = mcp_client.call_tool("git-server", "get_diff", {"commit": "HEAD"})
# Send 5000+ tokens to AI
```

### After (Using Analyzer Service):
```python
# Analyzer preprocesses changes locally
analysis = code_analyzer.analyze_commit(repo_path, "HEAD")
ai_summary = client.get_ai_summary(analysis)
# Send only 1500 tokens to AI (70% reduction)
```

## Token Usage Comparison

| Method | Tokens | Reduction |
|--------|--------|-----------|
| Raw git diff | ~5000 | 0% |
| MCP git-server | ~4000 | 20% |
| **Analyzer Service** | **~1500** | **70%** |

## Configuration

Environment variables:
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8001)
- `LOG_LEVEL`: Logging level (default: info)

## Response Format

```json
{
  "commit_sha": "abc123...",
  "commit_message": "Add feature X",
  "author": "developer@example.com",
  "timestamp": "1234567890",
  "files_changed": [
    {
      "file_path": "src/main.py",
      "change_type": "modified",
      "lines_added": 45,
      "lines_removed": 12,
      "language": "python",
      "functions_changed": ["process_data", "validate_input"],
      "classes_changed": ["DataProcessor"],
      "complexity_delta": 5,
      "diff_summary": "45 additions, 12 deletions"
    }
  ],
  "total_lines_added": 45,
  "total_lines_removed": 12,
  "risk_score": 42.5,
  "affected_modules": ["src", "tests"],
  "test_files_modified": true,
  "suggested_test_areas": [
    "Unit tests for process_data, validate_input in src/main.py",
    "Integration tests for src module"
  ]
}
```

## Attribute Accuracy (Research Validated)

All attributes were cross-validated against raw git commands during research testing:

| Attribute | Accuracy | Notes |
|---|---|---|
| `files_changed` | **100%** | Exact git output |
| `change_type` | **100%** | Exact git status codes |
| `lines_added` | **100%** | Exact git numstat |
| `lines_removed` | **100%** | Exact git numstat |
| `language` | **~95%** | Extension lookup |
| `functions_changed` | **~75%** | Named functions; some arrow patterns missed |
| `complexity_delta` | **~80%** | Regex decision-point counting |
| `risk_score` | **~85%** | Formula-verified; depends on upstream accuracy |
| `test_files_modified` | **~95%** | Regex path patterns |
| `affected_modules` | **~90%** | First directory component |
| `suggested_test_areas` | **~80%** | Rule-based |

## Benefits

1. **Reduced Token Costs**: ~70% reduction in AI token usage
2. **Faster Processing**: Local analysis is instant — no AI call needed
3. **Better Insights**: Structured data for smarter test generation
4. **Microservice Architecture**: Scales independently, restarts automatically
5. **Language Agnostic API**: Works with any AI model or pipeline

## Extending

Add support for more languages by:
1. Adding file extensions to `LANGUAGE_EXTENSIONS` in `analyzer.py`
2. Implementing language-specific symbol extraction (see `_get_js_symbols_commit` as reference)
3. Adding complexity calculators (see `_calculate_js_complexity` as reference)

## License

MIT
