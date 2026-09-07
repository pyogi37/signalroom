---
name: SignalRoom
description: An evidence docket for human review of AI-generated solution briefs.
colors:
  decision-cobalt: "#2457d6"
  decision-cobalt-hover: "#1948bd"
  decision-cobalt-pressed: "#123b9f"
  decision-cobalt-soft: "#dce7ff"
  dossier-ink: "#172033"
  dossier-ink-soft: "#3f4a5f"
  annotation: "#657188"
  canvas: "#eef1f5"
  paper: "#ffffff"
  paper-subtle: "#f7f8fa"
  paper-selected: "#e9f0ff"
  rule: "#d8dee8"
  rule-strong: "#aab4c4"
  verified: "#167553"
  verified-soft: "#e0f3eb"
  caution: "#a34b00"
  caution-soft: "#fff0df"
  blocked: "#a92f3a"
  blocked-soft: "#fee9eb"
  focus: "#7aa2ff"
typography:
  display:
    fontFamily: "Spline Sans, sans-serif"
    fontSize: "30px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Spline Sans, sans-serif"
    fontSize: "25px"
    fontWeight: 700
    lineHeight: 1.18
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Spline Sans, sans-serif"
    fontSize: "21px"
    fontWeight: 700
    lineHeight: 1.2
  body-large:
    fontFamily: "Spline Sans, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.6
  body-default:
    fontFamily: "Spline Sans, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "Spline Sans, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Spline Sans, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.35
  data:
    fontFamily: "IBM Plex Mono, monospace"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  control: "4px"
  container: "8px"
  overlay: "12px"
spacing:
  compact: "8px"
  control: "12px"
  section: "16px"
  panel: "24px"
  canvas: "28px"
  document: "38px"
components:
  button-primary:
    backgroundColor: "{colors.decision-cobalt}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "8px 13px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.decision-cobalt-hover}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.dossier-ink}"
    rounded: "{rounded.control}"
    padding: "8px 13px"
    height: "38px"
  input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.dossier-ink}"
    rounded: "{rounded.control}"
    padding: "9px 10px"
---

# Design System: SignalRoom

## Overview

**Creative North Star: "The Evidence Docket"**

SignalRoom is a calm technical review surface, shaped by architecture decision records, incident handovers, and audit workpapers. Its structure is explicit and ruled: provenance, uncertainty, proposal, critique, and human decision occupy stable regions instead of floating cards. It should feel made for someone evaluating consequences, not admiring an AI demo.

The system is dense enough to keep the reasoning chain in view, but never compressed below comfortable reading. Brand expression comes from precise cobalt state, tabular evidence details, and the disciplined three-region workspace.

**Key Characteristics:**

- Stable information columns with one-pixel rules.
- Cobalt reserved for the current decision or selection.
- Visible evidence provenance, confidence, and uncertainty.
- Compact sans typography with mono only for identifiers and measurements.
- Functional motion limited to state change and focused overlays.

## Colors

The palette combines cool document neutrals with a single decision cobalt; green verifies, amber cautions, and red blocks.

### Primary

- **Decision Cobalt:** Drives primary actions, current selections, and the active workflow state.
- **Soft Decision Cobalt:** Holds selected rows and evidence regions without competing with text.

### Secondary

- **Verified Green:** Marks completed stages, grounded confidence, and trusted audit behavior.
- **Caution Amber:** Marks medium uncertainty and correctable risk.
- **Blocked Red:** Marks high severity and destructive or failed state.

### Neutral

- **Dossier Ink:** Primary copy and the dark application bar.
- **Annotation:** Secondary copy, metadata, and descriptive labels.
- **Canvas:** The cool page field outside the working dossier.
- **Paper / Paper Subtle:** Main evidence surface and secondary work regions.
- **Rule / Rule Strong:** Structural separation and interactive control boundaries.

**The Evidence Color Rule.** Accent color always communicates state; it is never ambient decoration.

## Typography

**Display Font:** Spline Sans (with sans-serif fallback)  
**Body Font:** Spline Sans (with sans-serif fallback)  
**Label/Mono Font:** IBM Plex Mono (with monospace fallback)

**Character:** A practical, slightly technical sans carries all interface copy. The mono face is restricted to requirement IDs, timestamps, counts, and other evidence that benefits from stable character width.

### Hierarchy

- **Display** (700, 30px, 1.15): Page-level review task.
- **Headline** (700, 25px, 1.18): Selected requirement or primary document title.
- **Title** (700, 21px, 1.2): Decision and overlay headings.
- **Body Large** (400, 15px, 1.6): Requirement summaries and evidence descriptions, capped near 70 characters.
- **Body Default** (400, 14px, 1.5): Application chrome and default document text.
- **Body** (400, 13px, 1.55): Operational prose and helper copy.
- **Label** (600, 12px, 1.35): Section and control labels.
- **Data** (500, 11px, 1.4): IDs, times, percentages, and ordered architecture steps.

**The Measurement Rule.** Mono means evidence or measurement, never generic technical atmosphere.

## Layout

The desktop workspace uses three stable regions: a 270px requirements index, a fluid evidence docket, and a 310px decision panel. A compact task header and six-stage workflow sit directly above it. Content is capped at 1600px with 28px outer breathing room.

At 1180px, the decision panel moves beneath the evidence in a two-column summary. At 820px, the workspace becomes a single column and requirements become a horizontal selector. At 620px, analysis sections stack and outer gutters reduce to 18px. Typography stays fixed; the structure adapts.

## Elevation & Depth

The workspace is flat by default. One-pixel rules and subtle tonal layers establish hierarchy. The only raised surface is the new-discovery sheet, where a soft downward shadow communicates that it sits above the current task.

**The Flat Dossier Rule.** Persistent work surfaces use either a boundary or a tonal change, never decorative shadow.

## Shapes

Controls use gently squared 4px corners. Larger containers may use 8px or 12px only when the object is a true overlay or bounded region. Circles are reserved for workflow markers and status dots.

## Components

### Buttons

- **Shape:** Compact and squared (4px), at least 38px high.
- **Primary:** Decision cobalt with white text; used once in a decision group.
- **Hover / Focus:** A darker cobalt hover and a clearly offset focus ring.
- **Secondary:** White or transparent with a strong neutral rule.

### Inputs / Fields

- **Style:** White field, strong one-pixel boundary, 4px corners, and 13px text.
- **Focus:** Cobalt border plus a visible external focus ring.
- **Disabled:** Reduced opacity and a non-interactive cursor.

### Navigation

Requirements are full-width rows, not cards. The selected row uses a soft cobalt field and a 3px inset state marker. On small screens the same rows form a horizontally scrollable selector.

### Workflow

Workflow stages remain fixed in sequence. Completed steps use verified green; only the active stage receives the cobalt field and bottom rule. Detail copy may collapse at narrower widths, but stage names remain visible.

### Evidence Docket

The selected requirement begins with ID, kind, and confidence, followed by its source quotation, recommendation, critic pass, unresolved questions, and retrieved passages. Every region uses shared rules and section spacing rather than nested cards.

## Do's and Don'ts

### Do:

- **Do** make the current human decision visible without scrolling on desktop.
- **Do** keep source, timestamp, confidence, and evaluation details close to the claim they qualify.
- **Do** reserve cobalt for action and current state, green for verified state, and amber/red for risk.
- **Do** keep interactive copy at 12px or larger and operational prose at 13px or larger.
- **Do** preserve the same control vocabulary across intake, follow-up, approval, and export.

### Don't:

- **Don't** introduce marketing heroes, editorial kickers, glass effects, gradients, or decorative status chips into product surfaces.
- **Don't** place cards inside cards; use rules, spacing, and stable regions to express hierarchy.
- **Don't** hide unknowns or turn synthetic evaluation data into customer proof.
- **Don't** use color without a state meaning or mono type without evidence meaning.
