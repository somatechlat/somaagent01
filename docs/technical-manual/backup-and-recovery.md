# Backup and Recovery

## Overview
This document describes backup and recovery procedures for SomaAgent01.

## Backup Strategy

### Database Backups
```bash
# Backup PostgreSQL
docker exec postgres pg_dump -U postgres somaagent > backup_$(date +%Y%m%d).sql

# Backup with compression
docker exec postgres pg_dump -U postgres somaagent | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Redis Backups
```bash
# Trigger Redis save
docker exec redis redis-cli BGSAVE

# Copy RDB file
docker cp redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### Configuration Backups
```bash
# Backup environment configuration
cp .env .env.backup_$(date +%Y%m%d)

# Backup docker-compose
cp docker-compose.yaml docker-compose.backup_$(date +%Y%m%d).yaml
```

## Recovery Procedures

### Database Recovery
```bash
# Stop services
make dev-down

# Restore PostgreSQL
docker-compose up -d postgres
docker exec -i postgres psql -U postgres somaagent < backup_20250114.sql

# Restart services
make dev-up
```

### Redis Recovery
```bash
# Stop Redis
docker-compose stop redis

# Restore RDB file
docker cp redis_backup_20250114.rdb redis:/data/dump.rdb

# Start Redis
docker-compose start redis
```

### Full System Recovery
```bash
# 1. Stop all services
make dev-down-hard

# 2. Restore databases
docker-compose up -d postgres redis
sleep 10

# 3. Restore PostgreSQL
docker exec -i postgres psql -U postgres somaagent < backup.sql

# 4. Restore Redis
docker cp redis_backup.rdb redis:/data/dump.rdb
docker-compose restart redis

# 5. Start all services
make dev-up

# 6. Verify health
curl http://localhost:21016/v1/health
```

## Backup Schedule

### Recommended Schedule
- **Hourly**: Redis snapshots (retained for 24 hours)
- **Daily**: PostgreSQL full backup (retained for 7 days)
- **Weekly**: Full system backup (retained for 4 weeks)
- **Monthly**: Archive backup (retained for 1 year)

### Automated Backup Script
```bash
#!/bin/bash
# backup.sh - Automated backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL backup
docker exec postgres pg_dump -U postgres somaagent | \
  gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Redis backup
docker exec redis redis-cli BGSAVE
sleep 5
docker cp redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Configuration backup
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" .env docker-compose.yaml

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +7 -delete

echo "Backup completed: $DATE"
```

## Disaster Recovery

### Recovery Time Objective (RTO)
- Target: < 1 hour for full system recovery
- Critical services: < 15 minutes

### Recovery Point Objective (RPO)
- Database: < 1 hour (hourly backups)
- Configuration: < 24 hours (daily backups)

### DR Checklist
1. ☐ Identify failure scope
2. ☐ Stop affected services
3. ☐ Restore from latest backup
4. ☐ Verify data integrity
5. ☐ Restart services
6. ☐ Run health checks
7. ☐ Monitor for issues
8. ☐ Document incident

## Testing Recovery

### Monthly DR Test
```bash
# 1. Create test backup
./backup.sh

# 2. Simulate failure
make dev-down-hard

# 3. Perform recovery
# (follow Full System Recovery steps)

# 4. Verify functionality
curl http://localhost:21016/v1/health
# Test chat functionality
# Verify memory recall

# 5. Document results
```

## References
- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [Redis Persistence](https://redis.io/topics/persistence)
- [Docker Volume Backups](https://docs.docker.com/storage/volumes/#backup-restore-or-migrate-data-volumes)
