# Day 17: Integration Contracts & API Design

## OpenAPI Contract Example

```yaml
# contracts/payment_api_v1.yaml
openapi: 3.0.0
info:
  title: Payment Service API
  version: 1.0.0
servers:
  - url: https://api.example.com/v1

paths:
  /payments:
    post:
      summary: Process payment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [amount_cents, currency, provider]
              properties:
                amount_cents: {type: integer, minimum: 1, example: 10000}
                currency: {type: string, enum: [USD, EUR, GBP]}
                provider: {type: string, enum: [stripe, paypal]}
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentResponse'
        '400': {$ref: '#/components/responses/BadRequest'}
        '503': {$ref: '#/components/responses/ServiceUnavailable'}

components:
  schemas:
    PaymentResponse:
      type: object
      properties:
        transaction_id: {type: string, format: uuid}
        status: {type: string, enum: [completed, pending]}
        amount_cents: {type: integer}
        currency: {type: string}
        
  responses:
    BadRequest:
      description: Invalid request
      content:
        application/json:
          schema:
            type: object
            properties:
              error: {type: string, example: "Invalid currency"}
              code: {type: string, example: "INVALID_CURRENCY"}
```

## Event Contract (Message Bus)

```json
{
  "event": "PaymentCompleted",
  "version": "1.0",
  "schema": {
    "transaction_id": "uuid",
    "user_id": "string",
    "amount_cents": "integer",
    "currency": "string",
    "provider": "string",
    "timestamp": "ISO-8601"
  },
  "example": {
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_123",
    "amount_cents": 10000,
    "currency": "USD",
    "provider": "stripe",
    "timestamp": "2025-11-15T14:30:00Z"
  }
}
```

**Contract Validation:** Run `make validate-contracts` in CI  
**Integration Tests:** Use contracts to generate test cases  
**Documentation:** Auto-generated from OpenAPI spec
