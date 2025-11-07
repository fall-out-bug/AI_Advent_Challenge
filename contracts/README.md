# Integration Contracts

This directory contains integration contracts and specifications for the Code Review API.

## Contents

### API Specification

- **`review_api_v1.yaml`**: OpenAPI 3.0 specification for the Code Review API
  - Defines endpoints, request/response schemas, and error codes
  - Can be imported into Swagger UI, Postman, or other API tools

### Payload Schemas

- **`hw_check_payload_schema.json`**: JSON schema for external API payload
  - Defines the structure of data sent to external homework check API
  - Validates payloads when reviews are completed

### Format Specifications

- **`log_archive_format.md`**: Specification for log archive format
  - Describes structure, supported formats, and processing rules
  - Required for Pass 4 (Runtime Analysis) log processing

### Documentation

- **`INTEGRATION_GUIDE.md`**: Complete integration guide
  - Quick start, API endpoints, request/response formats
  - Error handling, best practices, examples
- **`../docs/day17/INTEGRATION_CONTRACTS.md`**: Day 17 summary (static analysis, Pass 4, MCP publishing)

### Examples

- **`examples/curl_example.sh`**: cURL command examples
- **`examples/python_example.py`**: Python client implementation

## Usage

### For API Consumers

1. Read `INTEGRATION_GUIDE.md` for overview
2. Import `review_api_v1.yaml` into your API client
3. Use examples in `examples/` as reference
4. Include a non-empty `new_commit` value in every review request
5. Capture `static_analysis_results` and `pass_4_logs` from the response for richer downstream insights
6. Validate payloads against `hw_check_payload_schema.json`

### For API Providers

1. Ensure implementation matches `review_api_v1.yaml`
2. Run contract tests: `pytest tests/contracts/`
3. Validate external API payloads against `hw_check_payload_schema.json`
4. Confirm `new_commit`, `static_analysis_results`, and `pass_4_logs` are persisted through to external API payloads
5. Follow log archive format from `log_archive_format.md`

## Contract Tests

Contract tests validate that the implementation matches the specifications:

```bash
# Run all contract tests
pytest tests/contracts/

# Run API spec compliance tests
pytest tests/contracts/test_api_spec.py

# Run payload schema compliance tests
pytest tests/contracts/test_payload_schema.py
```

## Versioning

- **Current version**: 1.0.0
- **Breaking changes**: Will increment major version
- **New features**: Will increment minor version
- **Bug fixes**: Will increment patch version

## Support

For questions or issues:
1. Check `INTEGRATION_GUIDE.md`
2. Review OpenAPI specification
3. Run contract tests
4. Contact support team

