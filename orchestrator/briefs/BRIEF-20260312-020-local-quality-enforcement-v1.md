# BRIEF: BRIEF-20260312-020-local-quality-enforcement-v1

## Context
После циклов локальной целостности, воспроизводимости, baseline governance и stage-1/0 refactor ключевой риск сместился из структуры кода в принятие решений по качеству. Candidate-модели и preset changes все еще оцениваются слишком вручную, а общий агрегат может скрывать regressions в `day`, `night` и `ir` режимах.

## Objective
Сделать локальный quality loop жестким и однозначным: разделить gate по preset/scenario, стандартизировать decision artifacts и зафиксировать baseline/candidate decision flow так, чтобы следующий training cycle не порождал двусмысленных model decisions.

## Success Metrics
- Local quality-gate differentiates `day`, `night`, and `ir` decisions explicitly.
- Baseline/candidate decisions are traceable through one canonical local artifact contract.
- Manual interpretation effort for `promote / hold_and_tune / reject` is reduced.

## Boundaries
- Must do:
  - работать только в локальном desktop-контуре проекта;
  - укреплять local quality enforcement и local decision flow;
  - использовать уже существующие regression packs и baseline contracts.
- Must not do:
  - не запускать новый training cycle;
  - не рефакторить `pipeline.py` или `main_gui.py` в этом цикле;
  - не развивать RTX/GitHub/automation как продуктовую архитектуру.

## Trigger Vocabulary
- If Claude plugin routing matters, prefer exact trigger words over synonyms.
- Context7 triggers:
  - `как использовать`, `документация`, `пример кода`, `API`, `версия`
  - `how to use`, `docs`, `latest API`, `library reference`, `sdk`
  - scope words: `library`, `dependency`, `docs`, `api`, `integration`
- Frontend-design triggers:
  - `ui`, `design`, `theme`, `stylesheet`, `overlay`, `card`, `layout`, `color`, `visual`, `hud`

## Deliverables
- Three focused implementation tasks for local quality enforcement
- Canonical per-preset quality-gate contract
- Canonical local decision artifact format
- Clear baseline/candidate promotion path tied to preset-specific evidence
