---
tags: [pysudoers, python, sudoers, linux, feynman, permissions, sysadmin]
hosts: [feynman, any-linux]
last_updated: 2026-02-19
---

# pySudoers
**Last Updated:** 2026-02-19
**Summary:** Python utility to refactor `/etc/sudoers` into individual files in `/etc/sudoers.d/`. Linux only.

## Environment Requirements
- **Platform:** Linux only — sudoers/visudo is not applicable on macOS
- **Tools:** `python3`, `visudo`
- Works on any Linux machine (not feynman-specific)

## Overview
Automates the modularization of sudoers configuration by creating separate files for each user/group rule.

## Features
- Validates syntax using `visudo -cf` before committing changes.
- Supports test mode (`--test`) to preview changes.
- Optional backup and removal of original entries.

## Location
- Source: `/home/mcglothi/code/pySudoers`
