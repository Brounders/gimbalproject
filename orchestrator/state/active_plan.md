# Active Plan

## Plan ID
- AP-20260312-012

## Source Direction
- Human direction: build the next implementation cycle from audit findings, but prioritize the local desktop product over temporary RTX/GitHub/web infrastructure.
- Scope: local product integrity only — theme source of truth, stable local baseline model path, and root/entrypoint cleanup.

## Status
- Completed

## Brief In Focus
- BRIEF-20260312-015-local-product-integrity-v1

## Active Claude Tasks (execution allowed now)
- (none)

## Active RTX Tasks (execution allowed now)
- (none)

## Backlog Policy
- Любые задачи вне списков выше считаются backlog и не исполняются.

## Exit Criteria
- [x] UI theme has one explicit maintained source of truth. (`app/ui/theme.py`)
- [x] Canonical local presets no longer depend on `runs/.../best.pt` as production model paths. (`models/baseline.pt`)
- [x] Repository root exposes only clear local launch paths for the desktop product. (`legacy/` created)
