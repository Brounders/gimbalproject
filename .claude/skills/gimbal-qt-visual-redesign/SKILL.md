---
name: gimbal-qt-visual-redesign
description: Use for GimbalProject PySide6 visual redesign, modern UI, layout, theme, HUD, DTS windows, HTML/Figma/reference-to-Qt work. Requires token extraction, screenshots, visual comparison, and iterative zone-by-zone implementation.
---

# Gimbal Qt Visual Redesign

## Purpose

Use this skill when the task mentions:

- UI, design, visual, theme, stylesheet, layout, HUD, panel, card, window;
- PySide6 visual polish;
- HTML/Figma/screenshot reference;
- DTS or Operator UI redesign.

## Required Workflow

1. Treat references as visual references, not application architecture.
2. Extract real tokens where possible:
   - colors;
   - font sizes;
   - radius;
   - borders;
   - spacing;
   - shadows;
   - component dimensions.
3. Work one zone at a time:
   - topbar;
   - video stage;
   - left/source controls;
   - right target/telemetry cards;
   - bottom dock/drawer;
   - DTS header/table/preview/card/footer.
4. Run the app or an offscreen screenshot harness.
5. Save screenshots for current state.
6. Compare against reference.
7. Iterate before claiming completion.

## Qt Reality Rules

Qt is not a browser.

Acceptable approximations:

- rgba panel fill instead of true `backdrop-filter`;
- QGraphicsDropShadowEffect where practical, not universal CSS shadows;
- 1px borders instead of CSS hairlines;
- simple SVG/local icons, no new icon dependency.

Not acceptable:

- claiming pixel-perfect without screenshots;
- using WebView/QML for a QWidget task;
- copying HTML architecture into the Python app;
- hiding required operator controls just to match reference.

## Visual Completion Gate

Before final answer, provide one of:

- screenshots and a visual gap report;
- or a clear reason screenshots could not be produced.

Do not claim “matches reference” without evidence.
