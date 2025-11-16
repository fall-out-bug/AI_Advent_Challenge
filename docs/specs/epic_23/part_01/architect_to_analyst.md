# Architect → Analyst Alignment · Epic 23

## Purpose
Capture clarified assumptions and outstanding needs from the Architect so the
Analyst can update requirement packs without ambiguity.

## Confirmed Decisions
1. **Data sources:** Product owner provides **exactly five RU Telegram channels**.
2. **Time window:** Collect posts for the **latest 30 calendar days** for each
   provided channel.
3. **Storage format:** Keep the existing **MongoDB JSON documents**; no schema
   migration to other stores is needed for Epic 23.
4. **Disaster recovery scope:** **Removed** from Epic 23. We only run the stack
   on the single Ryzen 5800 + 128 GB RAM + RTX 3070 Ti host; no DR drill or
   failover automation is required.
5. **Performance limits:** Benchmarks and exporters must assume the hardware
   above. There are no additional throughput ceilings beyond “runs must complete
   on that box”.
6. **RAG++ access:** Feature flag remains **owner-only**; other contributors are
   expected to provision their own stacks. Document this constraint in the
   Analyst materials.
7. **Legacy payment examples:** All payment-related references were removed; the
   epic now focuses solely on observability and benchmark enablement.

## Needs from Analyst
- Please state the **minimum sample count** per channel (e.g., ≥100 posts or 30
  daily digests) so engineering can set exporter validation thresholds.
- Confirm whether the Analyst pack should include **schema snippets** for the
  Mongo collections or if linking to existing exporter outputs is sufficient.
- Provide any **acceptance tests** the product owner will run on the seeded
  datasets (format, field presence, localization checks) to keep the success
  metrics measurable.

## Next Steps
1. Analyst updates `docs/specs/epic_23/backlog.md` (or append addendum) with the
   confirmed decisions above.
2. Analyst answers the open questions in “Needs from Analyst”.
3. Architect will refresh the Epic 23 architecture vision once the Analyst pack
   reflects the new scope.

_Generated 2025-11-15 based on stakeholder sync._
