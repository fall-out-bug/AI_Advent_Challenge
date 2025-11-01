# Детали Grafana Dashboard для AI Agent

## Dashboard: Agent Health (`grafana/dashboards/agent_health.json`)

### Полная структура JSON

```json
{
  "dashboard": {
    "title": "AI Agent Health Dashboard",
    "tags": ["agent", "mcp", "ai-challenge"],
    "timezone": "browser",
    "schemaVersion": 38,
    "version": 1,
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "Total Requests (24h)",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(mcp_tool_calls_total[24h]))",
            "legendFormat": "Total",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
        "fieldConfig": {
          "defaults": {
            "unit": "short"
          }
        }
      },
      {
        "id": 2,
        "title": "Success Rate (%)",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(mcp_tool_calls_total{status=\"success\"}[5m])) / sum(rate(mcp_tool_calls_total[5m])) * 100",
            "legendFormat": "Success Rate",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100
          }
        },
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {"value": null, "color": "red"},
            {"value": 80, "color": "yellow"},
            {"value": 95, "color": "green"}
          ]
        }
      },
      {
        "id": 3,
        "title": "Active Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "count(agent_dialog_tokens > 0)",
            "legendFormat": "Sessions",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
        "fieldConfig": {
          "defaults": {
            "unit": "short"
          }
        }
      },
      {
        "id": 4,
        "title": "Avg Latency (P95)",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(agent_tool_call_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95 Latency",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      },
      {
        "id": 5,
        "title": "Requests per Minute",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(mcp_tool_calls_total[1m])) by (tool_name)",
            "legendFormat": "{{tool_name}}",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        },
        "options": {
          "legend": {
            "displayMode": "table",
            "placement": "right"
          }
        }
      },
      {
        "id": 6,
        "title": "Success vs Error Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(mcp_tool_calls_total{status=\"success\"}[1m]))",
            "legendFormat": "Success",
            "refId": "A"
          },
          {
            "expr": "sum(rate(mcp_tool_calls_total{status=\"error\"}[1m]))",
            "legendFormat": "Error",
            "refId": "B"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
        "options": {
          "stacking": {
            "mode": "normal"
          }
        }
      },
      {
        "id": 7,
        "title": "Latency Percentiles",
        "type": "timeseries",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(agent_tool_call_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P50",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(agent_tool_call_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95",
            "refId": "B"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(agent_tool_call_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P99",
            "refId": "C"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12},
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      },
      {
        "id": 8,
        "title": "Latency by Tool",
        "type": "table",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(agent_tool_call_duration_seconds_bucket[5m])) by (tool_name, le)) by (tool_name)",
            "format": "table",
            "instant": true,
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 12},
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {},
              "indexByName": {
                "tool_name": 0,
                "Value": 1
              },
              "renameByName": {
                "tool_name": "Tool Name",
                "Value": "P95 Latency (s)"
              }
            }
          }
        ]
      },
      {
        "id": 9,
        "title": "Errors by Type",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(agent_errors_total[5m])) by (error_type)",
            "legendFormat": "{{error_type}}",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 20}
      },
      {
        "id": 10,
        "title": "Top 10 Errors",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, sum(rate(agent_errors_total[5m])) by (error_type))",
            "format": "table",
            "instant": true,
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 20},
        "transformations": [
          {
            "id": "organize",
            "options": {
              "renameByName": {
                "error_type": "Error Type",
                "Value": "Rate (errors/sec)"
              }
            }
          }
        ]
      },
      {
        "id": 11,
        "title": "Tool Calls Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(rate(mcp_tool_calls_total[5m])) by (tool_name)",
            "legendFormat": "{{tool_name}}",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 28}
      },
      {
        "id": 12,
        "title": "Tool Usage Stats",
        "type": "table",
        "targets": [
          {
            "expr": "sum(rate(mcp_tool_calls_total[1m])) by (tool_name)",
            "format": "table",
            "instant": true,
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 28},
        "transformations": [
          {
            "id": "organize",
            "options": {
              "renameByName": {
                "tool_name": "Tool Name",
                "Value": "Calls/min"
              }
            }
          }
        ]
      }
    ],
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "timepicker": {
      "refresh_intervals": ["10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]
    }
  }
}
```

## Prometheus Queries Reference

### Основные метрики агента

```promql
# Total tool calls за последние 24 часа
sum(increase(mcp_tool_calls_total[24h]))

# Success rate в процентах
sum(rate(mcp_tool_calls_total{status="success"}[5m])) / sum(rate(mcp_tool_calls_total[5m])) * 100

# Активные сессии (диалоги с токенами > 0)
count(agent_dialog_tokens > 0)

# Latency percentiles
histogram_quantile(0.50, sum(rate(agent_tool_call_duration_seconds_bucket[5m])) by (le))  # P50
histogram_quantile(0.95, sum(rate(agent_tool_call_duration_seconds_bucket[5m])) by (le))  # P95
histogram_quantile(0.99, sum(rate(agent_tool_call_duration_seconds_bucket[5m])) by (le))  # P99

# Latency по инструментам
histogram_quantile(0.95, sum(rate(agent_tool_call_duration_seconds_bucket[5m])) by (tool_name, le)) by (tool_name)

# Requests per minute по инструментам
sum(rate(mcp_tool_calls_total[1m])) by (tool_name)

# Errors by type
sum(rate(agent_errors_total[5m])) by (error_type)

# Top 10 errors
topk(10, sum(rate(agent_errors_total[5m])) by (error_type))

# Tool calls distribution
sum(rate(mcp_tool_calls_total[5m])) by (tool_name)
```

### ML метрики

```promql
# LLM latency для агента
histogram_quantile(0.95, rate(llm_inference_latency_seconds_bucket{operation="agent"}[5m])) by (model_name)

# Token usage для агента
sum(rate(llm_token_usage_total{operation="agent"}[1m])) by (type, model_name)

# LLM requests для агента
sum(rate(llm_requests_total{operation="agent"}[1m])) by (model_name, status)
```

### Диалог метрики

```promql
# Compression rate
rate(dialog_compressions_total[5m])

# Token distribution
agent_dialog_tokens

# Compression ratio
rate(dialog_compressions_total[5m]) / rate(agent_dialog_tokens > 8000[5m])
```

## Дополнительные панели для ML Service Metrics Dashboard

Добавить в существующий `grafana/dashboards/ml_service_metrics.json`:

```json
{
  "title": "Agent LLM Latency",
  "type": "timeseries",
  "targets": [
    {
      "expr": "histogram_quantile(0.95, rate(llm_inference_latency_seconds_bucket{operation=\"agent\"}[5m])) by (model_name)",
      "legendFormat": "{{model_name}} P95"
    }
  ],
  "unit": "s",
  "gridPos": {"h": 8, "w": 12, "x": 0, "y": 60}
},
{
  "title": "Agent Token Usage",
  "type": "timeseries",
  "targets": [
    {
      "expr": "sum(rate(llm_token_usage_total{operation=\"agent\"}[1m])) by (type, model_name)",
      "legendFormat": "{{model_name}} - {{type}}"
    }
  ],
  "unit": "tokens/sec",
  "gridPos": {"h": 8, "w": 12, "x": 12, "y": 60}
},
{
  "title": "Dialog Compression Rate",
  "type": "timeseries",
  "targets": [
    {
      "expr": "rate(dialog_compressions_total[5m])",
      "legendFormat": "Compressions/sec"
    }
  ],
  "gridPos": {"h": 8, "w": 12, "x": 0, "y": 68}
},
{
  "title": "Dialog Token Distribution",
  "type": "histogram",
  "targets": [
    {
      "expr": "agent_dialog_tokens",
      "legendFormat": "{{session_id}}"
    }
  ],
  "gridPos": {"h": 8, "w": 12, "x": 12, "y": 68},
  "fieldConfig": {
    "defaults": {
      "custom": {
        "buckets": [0, 1000, 2000, 4000, 6000, 8000, 10000]
      }
    }
  }
}
```

## Инструкции по импорту

1. Скопировать JSON в файл `grafana/dashboards/agent_health.json`
2. В Grafana: Configuration → Data Sources → проверить Prometheus
3. Dashboards → Import → загрузить JSON файл
4. Или использовать provisioning: `grafana/provisioning/dashboards/dashboards.yml`

