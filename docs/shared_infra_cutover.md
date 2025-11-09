# Shared Infrastructure Cutover Checklist

> Manual actions required from the infrastructure team before enabling shared
> services inside `AI_Challenge`.

## MongoDB Migration (User Action Required)

1. Ensure the shared infrastructure stack is running under
   `/home/fall_out_bug/work/infra`.
2. Execute the prepared migration scripts:

   ```bash
   cd /home/fall_out_bug/work/infra
   ./scripts/backup-existing-mongodb.sh
   ./scripts/restore-mongodb.sh <backup_file_from_step_1>
   docker exec shared-mongo \
     mongosh --username admin --password <password> \
     --authenticationDatabase admin --eval 'use butler; db.getCollectionNames()'
   ```

3. Compare the output with `docs/mongo_inventory_before.json` to verify that all
   collections, indexes, and TTL policies were migrated successfully.
4. Reply in the project channel once the migration is complete so the shared
   services can be enabled in the compose file.


