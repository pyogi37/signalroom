---
version: 1
slug: "src-app-tsx"
primary_target: "src/App.tsx"
related_targets: []
---

# SignalRoom review workspace

## Mode

Operate

## Job

A solution engineer, alone at a laptop after a discovery call, reads what the workflow produced, sees exactly which transcript line supports each claim and which findings the critic and the code checks raised, then approves, sends it back with a note, or answers open items and re-runs.

## Direction contract

**THESIS.** The brief is a pull request against the conversation: reviewed the way engineers already review, with line-numbered evidence in a gutter, findings as comment threads under the section they concern, and approval as the merge. It refuses the AI-workbench arrangement of cards, KPI tiles and an assistant panel.

**OWN-WORLD.** Cool paper and ink with one teal review accent; verified green, caution amber, blocked red only as states; added and removed tints for evidence lines. Red Hat Text for interface, Red Hat Mono for gutters, ids and measurements. Rules, not cards. Two renditions: day paper and night bench, same structure.

**STORY.** Open a room, see the checks, pick a change, read its verified line, read the threads, decide.

**FIRST VIEWPORT.** Header with room switcher and theme. Request header: status, title, checks strip of the six stages. Three columns: changed claims (272px), the document with gutter and threads (fluid), the review panel (320px) with Approve, Request changes and Comment as one submit group above the fold.

**FORM.** The Review Request, position 1 on the ordered list, IMPECCABLE'S PICK; seed key 266a4f26; code-led.

**FINISH.** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Responsive behavior

Below 1100px the review panel moves under the document. Below 820px the changed list becomes a horizontal strip, checks scroll horizontally, columns stack, and the submit group stays reachable at the bottom.

## Unresolved

Streaming stage progress during a live run is not built; the running state is a single pulsing check.
