# Open Training Jobs

TRAIN-20260514-001 | Deferred | 2026-05-14 | Candidate training from DTS pack; start only after Target Lab scene-aware diagnostics are trustworthy and accepted operator records are visually checked.

YOLO26-SMOKE-20260517 | Invalid/Stopped | 2026-05-17 | Manual smoke-train attempt stopped before training artifacts were produced. Directories contain args.yaml only and no results.csv, weights/best.pt, or weights/last.pt; do not use as model evidence.

TRAIN-20260517-002 | Ready | 2026-05-17 | YOLO26 weak4 smoke retry; use orchestrator/training/TRAIN-20260517-002-yolo26-weak4-smoke.md. Artifact-generation proof only: epochs=1, workers=0, save_period=1, tee log, external timeout 60 minutes, require results.csv, weights/last.pt, and train.log before any longer training.
