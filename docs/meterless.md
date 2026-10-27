# Meterless mapping — what this project uses, honestly

Meterless publishes four engines as prompt-based specs with a Context
Packet structure, no SDK, and directs builders to recreate the patterns
in their own stack. This project is a Python recreation of those
patterns. It does not run Meterless's TypeScript reference
implementations and does not claim conformance-suite results (the
suites are TypeScript-only).

## Component → engine

- **World Model** (event-sourced entity/context graph) → the packet's
  `world_state`: the day's declared frame (risk cap, daily lockout,
  news calendar) plus the day's running state (trades so far, P&L so
  far, lockout room left), built in `src/auditor/context_packet.py`.
- **H-MEM** (hierarchical memory, provenance, trust ledger) → the
  packet's `memory`: the raw journal row + the day's full history —
  the only evidence any step may cite. The Evaluator re-checks every
  citation against the raw row (the provenance check); an unverified
  citation VOIDS the verdict.
- **Markovian** (long runs in bounded chunks) → audit discipline: one
  trade per bounded audit unit. Nothing reaches a step except through
  the packet, so a long journal stays a sequence of small, checkable
  units instead of one unbounded run.
- **Scout Intent** (Sense → Interpret → Guard → Route → Recommend
  signed execution contract; spec only) → the packet's `intent`: the
  one question plus its guardrails (grade process, never P&L; never
  predict price; never issue a trade signal). The Planner emits the
  applicable rule set as the contract; the Executor follows it; the
  Evaluator checks it.

## What is NOT claimed

- **Swarm is not a Meterless engine.** Swarm-orchestration is a future
  engine. Our Planner / Executor / Evaluator are roles working one
  packet in sequence — described as roles, not as an engine.
- **No conformance-suite results.** The H-MEM, World Model, and
  Markovian reference implementations and their suites are TypeScript;
  this is a Python pattern implementation, so "implemented following
  the spec" is the claim, nothing stronger.
- **No live Meterless service.** There is no Meterless SDK, API call,
  or hosted engine in the path; the packet is built in-process by
  `src/auditor/context_packet.py`.

## Why this mapping is the honest one

The packet is the product's spine: frame + running state, cited memory,
bounded units, and a guarded question. Each of those four pieces traces
to exactly one published engine, and nothing in the build needs a
fifth. The earlier draft named "Swarm" as the fifth piece; that was
wrong and is corrected here and in the README and metadata.
