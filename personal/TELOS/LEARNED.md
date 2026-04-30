# LEARNED.md

**Last Updated:** 2026-03-29
**Summary:** A repository of lessons, insights, and "hard-won" wisdom.

---

## Infrastructure Lessons

- **[Nutanix/GCP]** Standardize on specific machine profiles early to avoid fragmentation in Ansible playbooks.
- **[Home Assistant]** Z-Wave and Zigbee stability depends heavily on the quality of the coordinator and the mesh density; don't cheap out on the stick.
- **[WordPress]** High-traffic site performance on WordPress.com is excellent, but custom PHP compatibility requires rigorous testing before migration.

## AI Session Lessons

- **[Context]** Large `ls -R` outputs are context killers. Prefer targeted `grep` and `find`.
- **[Prompting]** Giving an agent "Permission to Fail" (explicitly allowing them to say "I don't know") drastically reduces hallucinations.
- **[Memory]** `_runtime/` events are useful for session recovery, but only validated facts should be promoted to canonical files.
