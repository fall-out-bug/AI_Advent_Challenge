# MongoDB Warnings - Resolution Guide

## Overview

MongoDB logs show several warnings that are expected in development environments but should be addressed in production.

## Warnings and Solutions

### 1. Access Control Not Enabled

**Warning**: `Access control is not enabled for the database`

**Solution**: Enable authentication in production:

```yaml
environment:
  - MONGO_INITDB_ROOT_USERNAME=admin
  - MONGO_INITDB_ROOT_PASSWORD=your-secure-password
```

### 2. Transparent HugePages

**Warning**: `/sys/kernel/mm/transparent_hugepage/enabled is 'always'`

**Solution**: On the host system, run:

```bash
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag
```

Make it permanent by adding to `/etc/rc.local` or systemd service.

### 3. vm.max_map_count Too Low

**Warning**: `vm.max_map_count is too low`

**Solution**: On the host system, run:

```bash
sudo sysctl -w vm.max_map_count=1677720
```

Make it permanent by adding to `/etc/sysctl.conf`:

```
vm.max_map_count=1677720
```

### 4. Filesystem Recommendation

**Warning**: `Using the XFS filesystem is strongly recommended`

**Note**: This is informational. For production deployments, consider using XFS filesystem for MongoDB data directory.

## Current Status

These warnings are **not critical** for development and testing. The database functions correctly despite these warnings.

## Production Recommendations

For production deployments:

1. Enable MongoDB authentication
2. Configure system kernel parameters
3. Use XFS filesystem for data directory
4. Enable SSL/TLS encryption
5. Configure proper backup strategy
6. Set up monitoring and alerting

