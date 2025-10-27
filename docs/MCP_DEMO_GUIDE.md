# Day 09 MCP Demo Guide

## Quick Start

Run the comprehensive MCP integration demo with report generation:

```bash
make mcp-demo-report
```

This will:
1. Test all 8 MCP tools (calculator, models, agents, tokens)
2. Generate multiple report formats:
   - **Markdown** (`.md`) - Human-readable, GitHub-friendly
   - **Text** (`.txt`) - Console-friendly
   - **JSON** (`.json`) - Machine-readable
   - **Summary** (`.txt`) - Quick stats

## Report Output

Reports are saved to `reports/` directory with timestamps:

```
reports/
├── mcp_demo_report_20251027_230303.md    # Markdown report
├── mcp_demo_report_20251027_230303.txt   # Text report
├── mcp_demo_report_20251027_230303.json  # JSON report
└── mcp_demo_summary_20251027_230303.txt  # Summary
```

## Markdown Report Features

The generated markdown report includes:

- 📊 **Test Summary Table** - Quick overview with metrics
- 📝 **Detailed Results** - Category-organized test results
- ✅ **Status Icons** - Visual success/failure indicators
- 🔍 **Error Details** - Specific error messages for failures

### Example Markdown Output

```markdown
# 🔥 Day 09 MCP Integration - Test Report

**Generated:** 2025-10-27 23:03:07
**Duration:** 3.09s

## 📊 Test Summary

| Metric | Value |
|--------|-------|
| Total Tests | 6 |
| ✅ Passed | 4 |
| ❌ Failed | 2 |
| Success Rate | 66.7% |

## 📝 Detailed Results

### Calculator Tools

✅ **add**: success
  - **Result**: `42.0`

✅ **multiply**: success
  - **Result**: `56.0`
```

## Other Commands

### Basic Demo (Original)
```bash
make mcp-demo
```

### Tool Discovery
```bash
make mcp-discover
```

### Run Tests
```bash
make test-mcp
```

## Viewing Reports

### In Terminal
```bash
cat reports/mcp_demo_report_*.md
```

### In GitHub
Markdown reports are formatted to display beautifully in GitHub's markdown viewer.

### In VS Code
Markdown reports render perfectly in VS Code's built-in markdown preview.

## Report Structure

Each report contains:

1. **Header** - Title, generation time, duration
2. **Test Summary** - Aggregated statistics in table format
3. **Detailed Results** - Per-tool results organized by category:
   - Calculator Tools
   - Model SDK Tools  
   - Token Analysis
   - Agent Tools
4. **Footer** - Timestamp and generation info

## Customization

To add more tests to the demo, edit:
- `scripts/day_09_mcp_demo_report.py`

Add tests to the `run_demo_with_reports()` function.

## Integration

Reports can be integrated with:
- **CI/CD pipelines** - Parse JSON for automated checks
- **GitHub Actions** - Upload markdown reports as artifacts
- **Documentation** - Include reports in project docs
- **Monitoring** - Track test trends over time

## Tips

1. **Compare Reports**: Run multiple times to compare results
2. **Track Trends**: Review JSON reports for historical data
3. **Debugging**: Text reports are easiest for terminal viewing
4. **Sharing**: Markdown reports work great in documentation

## Troubleshooting

If reports show failures:

1. Check model availability: `make mcp-discover`
2. Review error messages in the markdown report
3. Run tests: `make test-mcp`
4. Check configuration: `config/mcp_config.yaml`
