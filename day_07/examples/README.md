# Examples Directory

This directory contains practical examples demonstrating how to use the StarCoder Multi-Agent System.

## Examples Overview

### 01_simple_generation.py
**Basic code generation example**
- Demonstrates simple task processing
- Shows basic workflow with code generation and review
- Perfect for getting started

### 02_custom_requirements.py
**Custom requirements example**
- Shows how to use specific requirements to guide generation
- Demonstrates complex task with multiple constraints
- Illustrates metadata extraction and analysis

### 03_batch_processing.py
**Parallel task processing**
- Demonstrates processing multiple tasks in parallel
- Shows efficiency gains from concurrent processing
- Includes performance analysis

### 04_advanced_orchestration.py
**Advanced orchestration patterns**
- Demonstrates retry logic and error handling
- Shows result analysis and pattern recognition
- Includes comprehensive error recovery

### 05_error_handling.py
**Comprehensive error handling**
- Tests various error scenarios
- Demonstrates proper exception handling
- Shows graceful degradation patterns

### 06_monitoring_metrics.py
**System monitoring and metrics**
- Shows how to monitor system health
- Demonstrates performance testing
- Includes metrics collection and analysis

## Running Examples

### Prerequisites

1. **Start StarCoder Service:**
   ```bash
   cd ../local_models
   docker-compose up -d starcoder-chat
   ```

2. **Start Agent Services:**
   ```bash
   cd ../day_07
   docker-compose up -d
   ```

3. **Verify Services:**
   ```bash
   make health
   ```

### Running Individual Examples

```bash
# Basic example
python examples/01_simple_generation.py

# Custom requirements
python examples/02_custom_requirements.py

# Batch processing
python examples/03_batch_processing.py

# Advanced orchestration
python examples/04_advanced_orchestration.py

# Error handling
python examples/05_error_handling.py

# Monitoring
python examples/06_monitoring_metrics.py
```

### Running All Examples

```bash
# Run all examples sequentially
for example in examples/*.py; do
    echo "Running $example..."
    python "$example"
    echo "Completed $example"
    echo "---"
done
```

## Example Outputs

Each example generates:
- **Console output**: Real-time progress and results
- **JSON files**: Detailed results for analysis
- **Metrics**: Performance data and statistics

### Output Files

- `advanced_orchestration_results_YYYYMMDD_HHMMSS.json`
- `monitoring_metrics_YYYYMMDD_HHMMSS.json`
- Various result files in `results/` directory

## Customizing Examples

### Modifying Tasks

Edit the `task_description` and `requirements` in any example:

```python
task_description = "Your custom task here"
requirements = [
    "Your requirement 1",
    "Your requirement 2"
]
```

### Adjusting Parameters

Modify parameters like retry counts, timeouts, or batch sizes:

```python
# In advanced orchestration example
orchestrator = AdvancedOrchestrator(max_retries=5)

# In batch processing example
tasks = [
    {"description": "Task 1", "requirements": ["req1"]},
    {"description": "Task 2", "requirements": ["req2"]}
]
```

## Troubleshooting

### Common Issues

1. **Services not running:**
   ```bash
   # Check service status
   docker-compose ps
   
   # Restart services
   docker-compose restart
   ```

2. **Connection errors:**
   ```bash
   # Check if ports are available
   netstat -tulpn | grep :9001
   netstat -tulpn | grep :9002
   ```

3. **Out of memory:**
   ```bash
   # Check GPU memory
   nvidia-smi
   
   # Reduce batch size or max_tokens
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Learning Path

### Beginner
1. Start with `01_simple_generation.py`
2. Try `02_custom_requirements.py`
3. Experiment with different tasks

### Intermediate
1. Run `03_batch_processing.py`
2. Study `05_error_handling.py`
3. Implement your own error handling

### Advanced
1. Analyze `04_advanced_orchestration.py`
2. Use `06_monitoring_metrics.py` for production
3. Build custom orchestration patterns

## Contributing Examples

To add new examples:

1. Create a new Python file in this directory
2. Follow the naming convention: `XX_description.py`
3. Include comprehensive docstrings
4. Add error handling and logging
5. Update this README

### Example Template

```python
#!/usr/bin/env python3
"""Example XX: Your Description

Brief description of what this example demonstrates.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import process_simple_task


async def main():
    """Run your example."""
    print("🚀 Example XX: Your Description")
    print("=" * 50)
    
    try:
        # Your example code here
        pass
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Support

For questions about examples:
- Check the troubleshooting section
- Review the main README.md
- Open an issue in the project repository
