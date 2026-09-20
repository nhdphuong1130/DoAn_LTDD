<!--
SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
SPDX-License-Identifier: Apache-2.0
-->

# Frontend Design & Flutter Review

Use this checklist when evaluating or building Flutter mobile UI features.

## Visual Fidelity & Pedagogical Tone

- [ ] **Authentic Design**: Typography, colors, and badge elements reflect Grade 7 textbook conventions.
- [ ] **No Deprecated APIs**: Avoid deprecated members (e.g. use `.withValues(alpha: ...)` instead of `.withOpacity(...)`).
- [ ] **Responsive Spacing**: Layouts use flexible columns, cards, and list views that scroll cleanly on various screen sizes.
- [ ] **Visual Feedback**: Interactive cards, audio players, and quiz choices provide clear tactile or visual selection states.

## Audio & Media Quality

- [ ] **Player Controls**: Audio player clearly shows play/pause state, progress slider, and duration timing.
- [ ] **Graceful Degradation**: Missing or offline audio assets show an informative placeholder rather than crashing.
- [ ] **Cache Friendly**: Media URLs reuse cached assets when possible.
