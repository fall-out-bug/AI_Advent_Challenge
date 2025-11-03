# Cross-Compose Integration Guide

This guide explains how to connect MCP servers and Prometheus exporters from different docker-compose files to Butler Agent infrastructure.

## Table of Contents

- [Overview](#overview)
- [Network Setup](#network-setup)
- [Connecting MCP Servers](#connecting-mcp-servers)
- [Connecting Prometheus Exporters](#connecting-prometheus-exporters)
- [Adding Data Sources to Grafana](#adding-data-sources-to-grafana)
- [Practical Examples](#practical-examples)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Overview

Butler Agent's docker-compose setup supports integration with services running in other compose files. This enables:

- **Shared MCP Servers**: Butler Agent can connect to MCP servers from `docker-compose.day12.yml` or other compose files
- **Multi-Compose Monitoring**: Prometheus can scrape metrics from exporters across multiple compose files
- **Centralized Visualization**: Grafana can aggregate data from all compose files

### Architecture Diagram

```
┌─────────────────────────┐      ┌─────────────────────────┐
│ docker-compose.day12   │      │ docker-compose.butler   │
│                         │      │                         │
│ ┌─────────────────┐   │      │ ┌─────────────────┐   │
│ │ mcp-server      │───┼──────┼→│ butler-bot      │   │
│ │ (port 8004)     │   │      │ │                 │   │
│ └─────────────────┘   │      │ └─────────────────┘   │
│                         │      │                         │
│ ┌─────────────────┐   │      │ ┌─────────────────┐   │
│ │ exporter        │───┼──────┼→│ prometheus      │   │
│ │ (port 9091)     │   │      │ │                 │   │
│ └─────────────────┘   │      │ └─────────────────┘   │
└─────────────────────────┘      └─────────────────────────┘
         │                                    │
         └────────────┬───────────────────────┘
                      │
           ┌──────────────────┐
           │ External Network │
           │ ai-challenge-    │
           │ network          │
           └──────────────────┘
```

## Network Setup

### Option 1: External Docker Network (Recommended for Production)

**Step 1: Create the shared network**

```bash
docker network create ai-challenge-network
```

**Step 2: Update compose files to join the network**

In `docker-compose.day12.yml`, add:

```yaml
networks:
  butler-network:
    driver: bridge
  butler-network-external:
    external: true
    name: ai-challenge-network
```

Then update services that need cross-compose access:

```yaml
services:
  mcp-server:
    # ... other config ...
    networks:
      - butler-network
      - butler-network-external  # Add this
```

In `docker-compose.butler.yml`, the external network is already configured.

**Step 3: Verify network connectivity**

```bash
# Check network exists
docker network ls | grep ai-challenge-network

# Inspect network
docker network inspect ai-challenge-network

# Test connectivity (from butler-bot container)
docker exec butler-bot-day13 ping mcp-server-day12
docker exec butler-bot-day13 curl http://mcp-server-day12:8004/health
```

### Option 2: host.docker.internal (Simple, Development Only)

Works on Docker Desktop (Mac/Windows) and Docker Engine 20.10+.

**Configuration:**

Set environment variable in `docker-compose.butler.yml`:

```yaml
environment:
  - MCP_SERVER_URL=http://host.docker.internal:8004
```

**Limitations:**

- Not available on all platforms (Linux native Docker requires Docker Engine 20.10+)
- Requires port mapping on host
- Less secure (direct host access)

**Example:**

If MCP server is running on host port 8004:

```yaml
# In other compose file
services:
  mcp-server:
    ports:
      - "8004:8004"  # Must expose port to host
```

Then Butler Agent can access it via `http://host.docker.internal:8004`.

## Connecting MCP Servers

### From Butler Agent to External MCP Server

**Prerequisites:**

- MCP server running in another compose file (e.g., `docker-compose.day12.yml`)
- Network connectivity (via external network or host.docker.internal)
- MCP server exposes HTTP endpoint on port 8004

**Configuration:**

1. **Using External Network (Recommended):**

```yaml
# docker-compose.butler.yml
services:
  butler-bot:
    environment:
      - MCP_SERVER_URL=http://mcp-server-day12:8004  # Service name from other compose
```

2. **Using host.docker.internal:**

```yaml
services:
  butler-bot:
    environment:
      - MCP_SERVER_URL=http://host.docker.internal:8004
```

**Verification:**

```bash
# Check MCP server is accessible
docker exec butler-bot-day13 curl http://mcp-server-day12:8004/health

# Or if using host.docker.internal
docker exec butler-bot-day13 curl http://host.docker.internal:8004/health
```

**Environment Variable:**

Set in `.env` file:

```bash
MCP_SERVER_URL=http://mcp-server-day12:8004
```

### Connecting Multiple MCP Servers

If you need to connect to multiple MCP servers:

1. **Use a Load Balancer**: Route requests to multiple MCP servers
2. **Service Discovery**: Use DNS or service discovery to find available MCP servers
3. **Client-Side Selection**: Implement logic in Butler Agent to select appropriate MCP server

**Example with Multiple MCP Servers:**

```yaml
# docker-compose.butler.yml
services:
  mcp-proxy:
    image: nginx:alpine
    ports:
      - "8004:80"
    volumes:
      - ./nginx-mcp.conf:/etc/nginx/nginx.conf
    networks:
      - butler-network-external

  butler-bot:
    environment:
      - MCP_SERVER_URL=http://mcp-proxy:80  # Proxy to multiple MCP servers
```

## Connecting Prometheus Exporters

### Adding External Exporters to Prometheus

**Step 1: Update `prometheus/prometheus.yml`**

Add a new scrape job:

```yaml
scrape_configs:
  # External exporter from another compose file
  - job_name: 'external-service'
    static_configs:
      - targets: ['service-name:9091']  # Use container name or host
        labels:
          service: 'external-service'
          compose_file: 'other-compose'
          layer: 'application'
    metrics_path: '/metrics'
    scrape_interval: 15s
    honor_labels: true
```

**Using External Network:**

If both Prometheus and exporter are on the same external network:

```yaml
- job_name: 'external-service'
  static_configs:
    - targets: ['external-service-container:9091']  # Container name
```

**Using host.docker.internal:**

If exporter is on host:

```yaml
- job_name: 'external-service'
  static_configs:
    - targets: ['host.docker.internal:9091']  # Host port
```

**Step 2: Reload Prometheus Configuration**

```bash
# Option 1: Reload via API (recommended)
curl -X POST http://localhost:9090/-/reload

# Option 2: Restart Prometheus container
docker-compose -f docker-compose.butler.yml restart prometheus
```

**Step 3: Verify Scraping**

Check Prometheus targets:

1. Open `http://localhost:9090/targets`
2. Look for your new job
3. Verify status is "UP"

### Service Discovery

For dynamic service discovery, use Prometheus service discovery:

```yaml
scrape_configs:
  - job_name: 'docker-services'
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        port: 2375
    relabel_configs:
      - source_labels: [__meta_docker_container_label_service]
        target_label: service
```

**Note:** This requires Docker socket access, which has security implications.

## Adding Data Sources to Grafana

### Prometheus Data Source

**Default Configuration:**

Grafana is pre-configured to use Prometheus from the same compose file:

- URL: `http://prometheus:9090` (service name)

**External Prometheus:**

To connect to Prometheus from another compose file:

1. **Using External Network:**

Update `grafana/provisioning/datasources/datasources.yml`:

```yaml
datasources:
  - name: Prometheus-External
    type: prometheus
    access: proxy
    url: http://prometheus-other-compose:9090  # Container name
    isDefault: false
```

2. **Using Host Access:**

```yaml
datasources:
  - name: Prometheus-Host
    type: prometheus
    access: proxy
    url: http://host.docker.internal:9090  # Host port
    isDefault: false
```

### Other Data Sources

**MySQL Exporter:**

```yaml
datasources:
  - name: MySQL
    type: mysql
    url: mysql-exporter:9104  # Container name:port
    database: your_database
    user: grafana
    secureJsonData:
      password: your_password
```

**PostgreSQL Exporter:**

```yaml
datasources:
  - name: PostgreSQL
    type: postgres
    url: postgres-exporter:5432
    database: your_database
    user: grafana
    secureJsonData:
      password: your_password
```

**Provisioning Location:**

Place datasource configs in `grafana/provisioning/datasources/` directory.

## Practical Examples

### Example 1: Connect Butler Agent to Day12 MCP

**Prerequisites:**

- `docker-compose.day12.yml` running with `mcp-server` service
- External network created: `docker network create ai-challenge-network`

**Steps:**

1. **Update day12 compose to join external network:**

```yaml
# docker-compose.day12.yml
services:
  mcp-server:
    networks:
      - butler-network
      - butler-network-external  # Add this

networks:
  butler-network-external:
    external: true
    name: ai-challenge-network
```

2. **Start day12 services:**

```bash
docker-compose -f docker-compose.day12.yml up -d
```

3. **Update butler compose (already configured):**

```bash
# docker-compose.butler.yml already has external network configured
docker-compose -f docker-compose.butler.yml up -d
```

4. **Set MCP URL in .env:**

```bash
MCP_SERVER_URL=http://mcp-server-day12:8004
```

5. **Verify connection:**

```bash
docker exec butler-bot-day13 curl http://mcp-server-day12:8004/health
```

### Example 2: Add MongoDB Exporter to Prometheus

**Step 1: Deploy MongoDB Exporter**

Add to a compose file:

```yaml
services:
  mongodb-exporter:
    image: percona/mongodb_exporter:latest
    environment:
      - MONGODB_URI=mongodb://mongodb:27017
    ports:
      - "9216:9216"
    networks:
      - butler-network-external
```

**Step 2: Configure Prometheus**

```yaml
# prometheus/prometheus.yml
scrape_configs:
  - job_name: 'mongodb-exporter'
    static_configs:
      - targets: ['mongodb-exporter:9216']
        labels:
          service: 'mongodb'
          exporter: 'mongodb'
    scrape_interval: 15s
```

**Step 3: Reload Prometheus**

```bash
curl -X POST http://localhost:9090/-/reload
```

### Example 3: Multi-Compose Monitoring Setup

**Scenario:** Monitor 3 different compose files with exporters

**Architecture:**

```
docker-compose.app.yml    → app-exporter:9091
docker-compose.worker.yml → worker-exporter:9091  
docker-compose.butler.yml → butler-bot:9091, prometheus, grafana
```

**Steps:**

1. **Create external network:**

```bash
docker network create ai-challenge-network
```

2. **Update all compose files to join network:**

```yaml
# In each compose file
networks:
  external:
    external: true
    name: ai-challenge-network
```

3. **Configure Prometheus to scrape all:**

```yaml
scrape_configs:
  - job_name: 'app-services'
    static_configs:
      - targets:
          - 'app-exporter:9091'
          - 'worker-exporter:9091'
          - 'butler-bot:9091'
        labels:
          environment: 'production'
```

## Troubleshooting

### Network Connectivity Issues

**Problem: Cannot connect to service in other compose file**

**Debug Steps:**

```bash
# 1. Verify network exists
docker network ls | grep ai-challenge-network

# 2. Inspect network
docker network inspect ai-challenge-network

# 3. Check containers are on network
docker network inspect ai-challenge-network | grep -A 5 "Containers"

# 4. Test DNS resolution
docker exec butler-bot-day13 nslookup mcp-server-day12

# 5. Test connectivity
docker exec butler-bot-day13 ping mcp-server-day12
docker exec butler-bot-day13 curl -v http://mcp-server-day12:8004/health
```

**Common Issues:**

- **Network not created**: Run `docker network create ai-challenge-network`
- **Container not on network**: Add network to service configuration
- **Wrong service name**: Use exact container name or service name
- **Firewall blocking**: Check Docker firewall rules

### MCP Connection Problems

**Problem: Butler Agent cannot connect to MCP server**

**Debug Steps:**

```bash
# 1. Verify MCP server is running
docker ps | grep mcp-server

# 2. Check MCP server health
curl http://localhost:8004/health  # From host
# Or
docker exec butler-bot-day13 curl http://mcp-server-day12:8004/health

# 3. Check environment variable
docker exec butler-bot-day13 env | grep MCP_SERVER_URL

# 4. Check logs
docker logs butler-bot-day13 | grep -i mcp
```

**Common Issues:**

- **Wrong URL format**: Must be `http://service-name:port`
- **Port not exposed**: Ensure MCP server exposes port in compose file
- **Network isolation**: Verify both services on same network

### Prometheus Scraping Issues

**Problem: Prometheus cannot scrape external exporter**

**Debug Steps:**

```bash
# 1. Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# 2. Test exporter endpoint
docker exec prometheus-day13 curl http://external-exporter:9091/metrics

# 3. Check Prometheus configuration
docker exec prometheus-day13 cat /etc/prometheus/prometheus.yml

# 4. Reload Prometheus
curl -X POST http://localhost:9090/-/reload
```

**Common Issues:**

- **Target shows as DOWN**: Check exporter is accessible from Prometheus container
- **No metrics**: Verify exporter exposes `/metrics` endpoint
- **Wrong port**: Ensure target port matches exporter port

## Security Considerations

### Network Isolation vs. Shared Network

**Isolated Networks (Default):**

- ✅ Better security (services cannot access each other)
- ❌ Requires explicit configuration for cross-compose access

**Shared External Network:**

- ✅ Easy cross-compose communication
- ❌ All services can potentially access each other
- ⚠️ Use firewall rules if needed

### Best Practices

1. **Use External Network Only for Required Services**: Don't add all services to external network
2. **Limit Port Exposure**: Only expose ports that need external access
3. **Use Secrets Management**: Never hardcode credentials in compose files
4. **Monitor Network Traffic**: Use tools to monitor cross-compose communication
5. **Regular Security Audits**: Review network configurations periodically

### Access Control

For production, consider:

- **Network Policies**: Use Docker network policies to restrict traffic
- **TLS/SSL**: Use encrypted connections for sensitive data
- **Authentication**: Implement authentication for MCP servers
- **Rate Limiting**: Protect against abuse

## Quick Reference

### Common Network Commands

```bash
# Create external network
docker network create ai-challenge-network

# List networks
docker network ls

# Inspect network
docker network inspect ai-challenge-network

# Remove network (when empty)
docker network rm ai-challenge-network
```

### Environment Variable Reference

```bash
# MCP Server URL
MCP_SERVER_URL=http://mcp-server-day12:8004  # External network
MCP_SERVER_URL=http://host.docker.internal:8004  # Host access
```

### Prometheus Scrape Config Template

```yaml
- job_name: 'service-name'
  static_configs:
    - targets: ['service-container:port']
      labels:
        service: 'service-name'
        compose_file: 'compose-filename'
  metrics_path: '/metrics'
  scrape_interval: 15s
```

### Grafana Datasource Template

```yaml
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

---

**Next Steps:**

- See [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment instructions
- See [MONITORING.md](./MONITORING.md) for monitoring setup
- See [ARCHITECTURE.md](./ARCHITECTURE.md) for architecture details

