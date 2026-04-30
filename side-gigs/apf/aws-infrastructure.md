---
context: personal
tags: [apf, aws, ec2, alb, nat, s3, route53, costs, simplification, cloudformation, t2-micro, mariadb, rds-snapshots, phpmyadmin]
last_updated: 2026-02-25
---

# APF: AWS Infrastructure — Reference

**Last Updated:** 2026-02-25
**Summary:** Production AWS stack decommissioned Feb 9, 2026. Only phpMyAdmin/certificate-lookup t2.micro remains (~$72/mo). Proposed simplification (remove ALB + NAT) would cut to ~$18/mo — pending client approval.

---

## What Was Deleted (Feb 9, 2026)

| Resource | Details |
|----------|---------|
| 2× c7a.2xlarge web instances | ASG scaled to min/max/desired 0 |
| Aurora MySQL cluster | 2× db.r7g.xlarge — final snapshot: `apf-final-snapshot-20260209` |
| ElastiCache | 6× cache.t2.medium Memcached (`apf-el-1ongt94rf0fuq`) |
| Production ALB | `apf-p-Publi-AOBZCZS0J76W` |
| EFS | `fs-fe6dd1fb` (22 GB WordPress files) |
| NAT Gateway | `nat-09db93707d5f72438` (100.20.149.254) |
| 4 stopped EC2 instances | i-07930cd8d92e3cd1a, i-09530a83602c5bb52, i-0be995b797eafa65a, i-0c781a28ea29487b7 |
| 3 Elastic IPs | 2 orphaned + 1 from deleted NAT |

---

## What Remains Running (~$72/mo)

| Resource | ID / Details | Est. Cost |
|----------|-------------|-----------|
| EC2 t2.micro | `i-054376b6d8751b8cb` — certificate lookup + phpMyAdmin | ~$9/mo |
| ALB | `phpmyadmin-LB` (2 AZs) — fronts cert lookup at `myadmin.autismpartnershipfoundation.org` | ~$25/mo |
| NAT Gateway | `nat-0977bb158a2454e72` (54.70.83.214) — outbound internet for private instance | ~$35/mo |
| 3 Elastic IPs | All attached (LB ×2, NAT ×1) | $0 |
| RDS Snapshots | 284 GB total (`apf-final-snapshot-20260209` 171 GB + `pre-mysql-index-upgrade-tm` 113 GB) | ~$6/mo |
| S3 Buckets | 6 buckets (see below) | ~$1–2/mo |
| Route53 | 1 zone, 27 records | ~$0.50/mo |
| Bastion EC2 | `i-0bd90d7263a1dfaae` (t2.nano) — RUNNING; public IP `52.39.99.191` (changes on restart — use `apf-inst` alias to check) | ~$5/mo |

**AWS Account:** 998393575948 | **Region:** us-west-2 (Oregon) only — no multi-region resources

---

## Proposed Simplification (pending client approval)

**Problem:** The cert-lookup t2.micro sits in a private subnet behind an ALB + NAT Gateway — the full production multi-AZ architecture. Costs ~$60/mo overhead for one small instance.

**Plan:**
1. Move t2.micro to public subnet (PublicSubnet0, us-west-2a)
2. Assign Elastic IP directly to instance
3. Update DNS: `myadmin.autismpartnershipfoundation.org` → A record → EIP
4. Delete ALB (`phpmyadmin-LB`) — saves ~$25/mo
5. Delete NAT Gateway (`nat-0977bb158a2454e72`) — saves ~$35/mo
6. Release 2 freed Elastic IPs
7. Add SSL via Let's Encrypt/certbot on instance
8. Restrict security group to HTTPS (443) inbound only

**Result:** ~$18/mo total AWS (down from ~$72/mo), saving ~$54/mo (~$648/yr)

| Resource | After simplification |
|----------|---------------------|
| EC2 t2.micro | ~$9/mo |
| Elastic IP (1, attached) | $0 |
| RDS Snapshots | ~$6/mo |
| S3 Buckets | ~$1–2/mo |
| Route53 | ~$0.50/mo |
| **Total** | **~$18/mo** |

---

## S3 Buckets (keep indefinitely)

| Bucket | Contents | Keep? |
|--------|---------|-------|
| `apf-certs` | 64,451 certificate JPGs (literal TAB in filenames — see cert registry doc) | ✅ Permanent |
| `apf-migration-backups-2026` | DB backups, 290,566 certificate PDFs (48 GB) | ✅ Compliance |
| `apf-conf-2023` | Conference data | ✅ Keep |
| `2022-apf-billing-reports` | Billing reports | ✅ Keep |
| `autismpartnershipfoundation.com-logs` | Access logs | Review for deletion |
| `aws-cloudtrail-logs-998393575948-e5885d22` | CloudTrail audit logs (3.18 GB) | Review for deletion |

---

## CloudFormation Stacks (still exist — DO NOT delete yet)

Stacks are in drift (their resources have been deleted or scaled to 0). Deleting them may remove the VPC/security groups that the phpMyAdmin instance depends on. Clean up only after simplification is complete.

Stacks: `apf-prod-web`, `apf-prod-rds`, `apf-prod-elasticache`, `apf-prod-efsfilesystem`,
`apf-prod-bastion`, `apf-prod-publicalb`, `apf-prod-efsalarms`, `apf-prod-dashboardwithalarms`,
`apf-prod-securitygroups`, `apf-prod-newvpc`, `apf-prod` (parent)

---

## Historical AWS Resource IDs (for reference)

| Resource | ID |
|----------|----|
| AWS Account | 998393575948 |
| Region | us-west-2 (Oregon) |
| VPC | still active (contains phpMyAdmin instance) |
| RDS primary endpoint (deleted) | ad1vg6lup38wqbl.cvtv1w2tb1pk.us-west-2.rds.amazonaws.com |
| RDS reader endpoint (deleted) | adaj3d6wz5ai6z.cvtv1w2tb1pk.us-west-2.rds.amazonaws.com |
| CloudFront distribution (inactive) | ESAD4J9V0N5BJ |
| IAM Role (web instances) | apf-prod-web-M6ZIP7XVIN40-WebInstanceRole-1RE62KAK0CA99 |
| EFS (deleted) | fs-fe6dd1fb |
