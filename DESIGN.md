---
name: SignalRoom
description: The Review Request. A solution brief reviewed the way engineers review code, as a pull request against the transcript, in day and night renditions of one world.
colors:
  bg: "#f6f7f4"
  surface: "#ffffff"
  surface-2: "#eef1ec"
  gutter: "#f3f5f1"
  ink: "#172120"
  ink-2: "#48534f"
  ink-3: "#68746f"
  rule: "#d9dfd9"
  rule-2: "#bcc6c0"
  accent: "#0f6e6a"
  accent-hover: "#0b5955"
  accent-soft: "#dbeeeb"
  ok: "#2b7a3e"
  ok-soft: "#e3f3e6"
  warn: "#8f5400"
  warn-soft: "#fbeed6"
  bad: "#b3261e"
  bad-soft: "#fbe6e4"
  add: "#e7f5ea"
  add-ink: "#1f5f2e"
  del: "#fdeceb"
  del-ink: "#8f2119"
  focus: "#5fb3ac"
  night-bg: "#0f1413"
  night-surface: "#151b1a"
  night-surface-2: "#1a2321"
  night-ink: "#e6ebe8"
  night-ink-2: "#b3bfba"
  night-ink-3: "#8c9893"
  night-rule: "#26302d"
  night-accent: "#4fc1b8"
  night-accent-soft: "#143331"
  night-ok: "#6cc98a"
  night-warn: "#e3a94f"
  night-bad: "#ff8078"
  night-add: "#12281a"
  night-del: "#351b18"
typography:
  title:
    fontFamily: "Red Hat Text, Segoe UI, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.012em"
  body:
    fontFamily: "Red Hat Text, Segoe UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
  control:
    fontFamily: "Red Hat Text, Segoe UI, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 600
    lineHeight: 1
  label:
    fontFamily: "Red Hat Text, Segoe UI, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.06em"
  data:
    fontFamily: "Red Hat Mono, Cascadia Mono, Consolas, monospace"
    fontSize: "11.5px"
    fontWeight: 500
    lineHeight: 1.4
  gutter:
    fontFamily: "Red Hat Mono, Cascadia Mono, Consolas, monospace"
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  marker: "2px"
  focus: "3px"
  mark: "5px"
  control: "6px"
  container: "10px"
  pill: "999px"
spacing:
  tight: "6px"
  control: "12px"
  section: "18px"
  page: "20px"
  gutter: "88px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "6px 12px"
    height: "34px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "6px 12px"
    height: "34px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "8px 10px"
---

# Design System: SignalRoom

## Overview

**Creative North Star: "The Review Request"**

The brief is a pull request against the conversation. A solution engineer reviews it the way engineers already review code: a request header with checks, a list of changed claims, a document with a line-number gutter carrying transcript references, evidence as added lines, out-of-scope items as removed lines, findings as comment threads under the section they concern, and a submit-review group that approves, requests changes or answers open items. It refuses the AI-workbench arrangement of cards, KPI tiles and an assistant panel.

Two renditions of one world: day paper (cool grey-green paper, carbon ink) and night bench (green-black ground, chalk ink). Structure, type and spacing are identical; only the token values swap on `data-theme="night"`.

**Key characteristics**

- One teal review accent for the current selection, primary action and links. Green verifies, amber cautions, red blocks, and nothing else is coloured.
- An 88px monospaced gutter is the spine of the document: every quote, constraint, finding and answer hangs from a line reference.
- Ruled containers, not cards. One soft offset shadow exists, on the room menu and the composer sheet, and nothing else floats.
- Dense Operate typography on one family, with mono reserved for line numbers, ids and measurements.
- Motion explains state: a selection marker that travels, threads that arrive, one authored moment when a decision resolves.

## Colors

**The Provenance Rule.** Colour states where a thing came from or what state it is in, never decorates. Added tint marks a verified quote and a follow-up line, removed tint marks scope the participants declined, accent marks the current claim and the primary action.

- Day: page `#f6f7f4`, surface white, secondary surface `#eef1ec`, gutter `#f3f5f1`, ink `#172120` with two quieter steps, rules `#d9dfd9` and `#bcc6c0`.
- Night: page `#0f1413`, surface `#151b1a`, gutter `#131a19`, ink `#e6ebe8`, rules `#26302d` and `#37443f`. Accent lightens to `#4fc1b8` and its text inverts to the page colour.
- Semantic pairs (solid plus soft) for ok, warn and bad exist in both renditions; chips and notices mix the solid at 40 to 45 percent into their border.

## Typography

Red Hat Text carries every interface size; Red Hat Mono carries the gutter, ids, the eval line and measurements. Both are self-hosted (latin subset) under `apps/web/public/fonts`.

**The Measurement Rule.** Mono means a line number, an id, a count or a cost. It is never atmosphere.

Scale: 22px title (700, -0.012em), 13px body, 12.5px controls (600), 12px uppercase labels (700, 0.06em), 11.5px mono data, 11px mono gutter. Tabular numerals everywhere.

## Layout

Desktop: a sticky 52px top bar, a request header with status pill, title, lede, eval line and a six-cell checks strip, then three columns of 272px (changed claims), fluid (the document) and 320px (review) inside a 1560px maximum with 20px gutters. The changed list and the review panel are sticky under the top bar.

At 1100px the review panel moves first and spans the width so the decision stays reachable, with its panels in an auto-fit grid. At 820px the columns stack, the changed list becomes a horizontal strip, the checks strip scrolls and centres the active check, the gutter narrows to 64px, and the crumb label hides while the room switcher truncates.

## Elevation and depth

Flat by default: containers are one-pixel rules on the surface colour. The only shadow is `0 14px 34px -14px rgba(23,33,32,.32)` (darker at night), on the room menu and the composer sheet, which carry no border. Elevation is declared once.

## Shapes

Controls at 6px, containers at 10px, chips as pills, the selection marker at 2px, the brand mark at 5px. No nested containers.

## Components

- **Request header**: status pill (open, approved, failed, running), meta counts, title, lede, eval line, checks strip with complete, active, failed and pending states.
- **Changed list**: claims grouped as requirements and use cases, each with a mono id, a confidence dot and its line reference; the selected claim carries a shared-layout accent marker.
- **Document**: hunks with an `@@ id` header, rows on an 88px gutter, added and removed tints, chips for confidence, readiness, baseline and severity, tables that scroll inside their container.
- **Threads**: comment-style findings with a source chip (code check or critic), a severity word, the location and the lines; struck and marked resolved once the brief is approved.
- **Review panel**: submit group as a radio group with an inline note field, one primary submit, export, then checks, timeline and the graph trace.
- **Composer sheet**: right-hand sheet with a mono transcript field, fixture loader, reference-file target and the synthetic-only notice.

## Motion

One grammar in `motion.ts`: ease `cubic-bezier(0.16, 1, 0.3, 1)`, durations 120ms feedback, 200ms state, 320ms layout, 600ms focal. Selection continuity uses a shared layout marker; threads and the sheet arrive in place; a changed brief revision flashes its hunk headers once. The focal moment is a submitted approval: the status pill resolves, the Gate check completes, a single green rule sweeps under the checks and threads are marked resolved. Under reduced motion spatial movement and the sweep are removed while colour and state changes remain.

## Do and don't

- Do put a line reference on every claim, constraint and finding; the gutter is the design.
- Do keep the decision above the fold at every width.
- Do add rows and threads, never cards, when the brief grows a section.
- Don't colour anything that is not a state or a provenance.
- Don't introduce a second shadow, a hero metric, an assistant persona or a chat bubble.
- Don't present synthetic evidence or evaluation numbers as customer proof.
