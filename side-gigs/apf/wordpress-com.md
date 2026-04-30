---
context: personal
tags: [apf, wordpress-com, plugins, woocommerce, learndash, php, dns, route53, ssh, wp-cli, uncanny-toolkit, kleo, page-optimize, users, database]
last_updated: 2026-04-16
---

# APF: WordPress.com — Live Site Reference

**Last Updated:** 2026-04-16
**Summary:** autismpartnershipfoundation.org is live on WordPress.com (Atomic). 7,626 users, 35 active plugins, PHP 8.3.30, TTFB 55ms via CDN.

---

## Access

```bash
# SSH (must use wpcom staging hostname — production domain does NOT work for SSH)
ssh ecom-time72d10928191-fznxc.wordpress.com@ssh.wp.com
cd /srv/htdocs

# Quick health check
wp option get home        # → https://autismpartnershipfoundation.org
wp core version           # → 6.9.1
wp plugin list --status=active --fields=name --format=count  # → 35
curl -sI https://autismpartnershipfoundation.org | grep HTTP  # → HTTP/2 200
```

- **WP Root:** `/srv/htdocs`
- **WordPress version:** 6.9.1 (PHP 8.3.30)
- **No `--allow-root` needed** on WordPress.com

---

## April 2026 Security Vulnerabilities

High-priority vulnerabilities disclosed in early April 2026 affecting active plugins on this site.

| Plugin | Current Version | Risk | Mitigation |
|--------|-----------------|------|------------|
| **Slider Revolution** | 6.1.2 | **Critical** — CVE-2025-9217: Unauthenticated Arbitrary File Read (can read `wp-config.php`) | Update to **v7.0.8+** |
| **ACF Pro** | 5.8.7 | **High** — CVE-2026-4812: Unauthenticated Missing Authorization (data disclosure) | Update to **v6.7.1+** |
| **WPBakery (js_composer)** | 6.0.5 | **High** — Legacy version targeted by automated scans for dashboard takeover | Update to **v7.6+** |

**Notes:**
- Site does **not** use the "Essential Plugin" portfolio (the source of the April 2026 supply chain attack).
- These plugins are bundled with the KLEO theme. Updating them manually may be required if the theme is not updated.
- Verify dropdown functionality after any WPBakery update due to custom PHP 8.3 patches.

---

## Site Health (as of Feb 9, 2026)

- 7,626 users (5,831 customers, 1,779 subscribers, 16 admins) — 109 new since migration
- 35 active plugins (down from 43 after cleanup)
- TTFB: 55ms (CDN-cached); object cache active; HSTS enabled
- Disk: 12 GB uploads, 2.9 TB available
- Database: all tables pass `wp db check`

## Verified Content Counts (AWS ↔ WordPress.com — IDENTICAL)

| Post Type | Count |
|-----------|-------|
| sfwd-lessons | 521 |
| sfwd-quiz | 326 |
| sfwd-question | 293 |
| sfwd-certificates | 164 |
| sfwd-topics | 123 |
| sfwd-courses | 117 |
| products | 112 |
| pages (published) | 72 |
| posts (published) | 18 |

---

## PHP Compatibility Fixes (PHP 7.4 → 8.3)

All backups saved as `.backup` alongside original files.

| File | Fix |
|------|-----|
| `themes/kleo/kleo-framework/lib/function-core.php` | `isset()` checks on lines 448, 452; nested ternary parenthesized on line 573 |
| `plugins/js_composer/…/class-vc-manager.php` | `__wakeup()` visibility: `private` → `public` (line 202) |
| `plugins/js_composer/…/class-vc-frontend-editor.php` | Nested ternary parenthesized (line 673) |
| `plugins/brandastic-landing/brandastic-landing.php` | `defined('WP_ENV')` guard added (line 214) |

---

## Critical Plugin Notes

| Plugin | Status | Note |
|--------|--------|------|
| **Page Optimize** | DEACTIVATED — keep it this way | WordPress.com auto-installs this; it breaks Bootstrap/Magnific Popup JS loading order on KLEO/Brandastic. Edge caching already active. |
| **Uncanny LearnDash Toolkit** | Active | Was deactivated during migration troubleshooting. License key: [Stored in Vaultwarden: APF Uncanny Toolkit] — activate in WP Admin → Uncanny Toolkit → License Activation |
| **KLEO Theme** | DO NOT UPDATE (4.9.110) | Update to 5.5.0 would undo all PHP compatibility fixes. Test on staging first. |
| **Wordfence** | DEACTIVATED | Incompatible with managed hosting — self-deactivated; not needed |
| **wp-staging** | Cannot fully deactivate | Locked by mu-plugin; harmless |
| **wordpress-importer, wp-migrate-db-pro-***, wp-staging-pro, wpbenchmark, gutenberg, import-users-from-csv-with-meta** | All DEACTIVATED | One-time migration tools; Gutenberg redundant on WordPress.com |

### Active Plugins (35)
```
advanced-custom-fields-pro 5.8.7, akismet 5.6, auto-login-new-user-after-registration 1.9.3,
brandastic-landing 2.5, elc-ctid-tracker 1.02.03, elc-ctid-verifier 1.01.09,
classic-editor 1.6.7, cms-tree-page-view 1.6.8, custom-content-shortcode 3.8.6,
envato-market 2.0.5, extended-user-search-in-wp-admin 3, gravityforms 2.7.14,
gravity-forms-iframe 2.0.1, gravityformsmailchimp 4.8, index-wp-mysql-for-speed 1.4.18,
jetpack 15.5-beta, k-elements 4.9.100, sfwd-lms 5.0.0, learndash-woocommerce 1.9.0,
wpcom-migration 5.88, minimum-periods-for-woocommerce-subscriptions 1.2.0,
profile-builder 3.15.3, revslider 6.1.2, sq-sidebar-generator 1.2.2,
welcome-email-editor 6.3, the-events-calendar 6.15.15, uncanny-learndash-toolkit 3.8.0.2,
uncanny-toolkit-pro 3.5.8, woocommerce 10.5.0, woocommerce-custom-thank-you-pages 1.0.2,
woocommerce-subscriptions 3.0.13, js_composer 6.0.5, wp-mail-smtp 4.7.1,
wp-staging 3.8.0, wordpress-seo 26.9
```

---

## DNS State

- **Route53 Zone ID:** `Z01249502BI1HFSPUUYK4`
- **WordPress.com A records:** `192.0.78.171`, `192.0.78.240` (TTL 300)
- **27 total records** (down from 40; 13 dead records removed Feb 9)

Key preserved records:
- Google Workspace: 5× MX, SPF, DMARC, DKIM
- Active services: `courses.` (Kajabi), `myadmin.` (phpMyAdmin/cert-lookup ALB), `calendar.`
- Email CNAMEs: imap, pop, smtp, email (secureserver.net)
- Can clean later: 5× SES DKIM CNAMEs, 1× ACM validation CNAME, `_domainconnect`

### DNS Cutover Notes (for future reference)
- Must explicitly set custom domain as **primary** in WordPress.com dashboard — DNS alone won't trigger switchover
- Initial cutover caused 762,696 DB URL replacements: `wp search-replace --all-tables` (staging → production)
- Page Optimize plugin broke JS loading immediately after cutover — deactivate it

---

## Authentication Notes

- `wp user update --user_pass` unreliable — use `wp eval "wp_set_password('pass', ID);"` instead
- Uncanny LearnDash Toolkit's Frontend Login Plus intercepts WP auth — deactivate if debugging login
- WordPress.com flags weak/MD5 password hashes as "compromised" — triggers email verification flow
- WordPress.com dashboard auth is separate from wp_users table

---

## WordPress.com Constraints

- WP-CLI memory hard-limited to **512MB** (cannot increase)
- `wp user list` with 7,500+ users → OOM; use `wp db query` instead
- GD image processing crashes on very large images at 512MB limit
- `**/*.gif` glob patterns don't expand in WordPress.com shell
- MySQL `BINLOG ADMIN` / `GTID_PURGED` not available (harmless import warnings)
- Custom post types only import if the plugin is already installed

---

## Incidents & Post-Mortems

### Feb 6, 2026 — Page Optimize Broke Navigation Dropdowns
- **What happened:** Immediately after DNS cutover, navigation dropdown menus stopped working. Browser console showed `TypeError: $(...).popover is not a function` and `TypeError: $(...).magnificPopup is not a function`.
- **Root cause:** WordPress.com had auto-installed the Page Optimize plugin, which minifies and defers JavaScript. This broke Bootstrap and Magnific Popup loading order that KLEO/Brandastic depends on.
- **Fix:** `wp plugin deactivate page-optimize` — dropdowns immediately functional.
- **Prevention:** Page Optimize must stay deactivated permanently on this site. WordPress.com edge caching makes it redundant anyway.

### Feb 6, 2026 — Staging URLs Baked Into Database
- **What happened:** After DNS cutover, graphics were missing and internal links pointed to the staging domain.
- **Root cause:** WordPress stores the site URL throughout the database. Initial `wp search-replace` only targeted certain tables.
- **Fix:** `wp search-replace 'ecom-time72d10928191-fznxc.wpcomstaging.com' 'autismpartnershipfoundation.org' --all-tables` — 762,696 replacements.
- **Prevention:** Always use `--all-tables` for domain search-replace. Run it before announcing cutover complete.

### Feb 6, 2026 — Login Failures After User Import
- **What happened:** Imported users (PHP 7.4 hashes) couldn't log in under PHP 8.3. No error shown — form just bounced back to login prompt.
- **Root cause:** Multiple compounding issues: Uncanny LearnDash Toolkit's Frontend Login Plus intercepting auth before WP could complete it; WordPress.com flagging MD5-hashed passwords as "compromised" and requiring email verification; test account had a stale email address.
- **Fix:** Temporarily deactivated Uncanny LearnDash Toolkit; updated email; used `wp eval "wp_set_password('pass', ID);"` for proper native hashing.
- **Prevention:** Use `wp eval "wp_set_password()"` — never `wp user update --user_pass`. After any user table import across PHP major versions, reset admin passwords immediately.

---

## Deferred Cleanup (needs client sign-off)

| Item | Size | Action |
|------|------|--------|
| Post revisions | 45,284 in wp_posts | Limit to 5, prune old |
| `wp_wp_pro_quiz_statistic_ref` | 26.3M rows, 2 GB | Student data — requires client approval before pruning |
| `wp_postmeta` | 25.3M rows, 5.2 GB | Will shrink significantly after revision cleanup |

Also: `wp_aryo_activity_log` was already truncated (2.9M rows, 304 MB freed — orphaned table).

---

## Useful Commands

```bash
# Content counts
wp db query "SELECT post_type, COUNT(*) AS c FROM wp_posts WHERE post_status='publish' GROUP BY post_type ORDER BY c DESC;"

# User counts by role
wp db query "SELECT meta_value, COUNT(*) FROM wp_usermeta WHERE meta_key='wp_capabilities' GROUP BY meta_value;"

# Password reset
wp eval "wp_set_password('NewPassword', <USER_ID>);"
wp user reset-password username1 username2

# Plugin management
wp plugin activate <name>
wp plugin deactivate <name>

# Search-replace (always use --all-tables for domain changes)
wp search-replace 'old-domain.com' 'new-domain.com' --all-tables
```
