# Trade Auditor — "Why did this trade pass or fail my system?"

Open Agent Hackathon 2026 · Track 02 (The Agent That Can Explain Why) · Question 1
Solo build by David Titcombe.

## The problem

A trading journal tells you WHAT happened. It never tells you whether the trade
deserved to be taken. This agent audits every journal entry against the trader's
own written system — a fixed set of rules ruled in advance — and answers, per trade:

**PASS or FAIL — and why, citing the exact journal fields each claim rests on.**

A second agent then verifies every citation against the entry before the verdict
is shown. No claim survives that the data doesn't support.

## How it works

1. **Planner** — reads the day's declared frame (risk cap, daily lockout, news
   calendar) and the trade under audit; decides which rules apply.
2. **Executor** — pulls the trade + journal history through the data layer and
   evaluates each applicable rule, attaching the cited field values.
3. **Evaluator** — re-checks every citation against the raw entry, grades the
   trade's process (not its P&L), and writes one fix for the next session.

Every audit travels as a single **Context Packet** (see
`src/auditor/context_packet.py`): the day's frame and running state (world
state), the raw journal row and day history (memory), the one question and its
guardrails (intent) — assembled by the Planner, reasoned over by the Executor,
verified by the Evaluator. Nothing reaches a step except through the packet.

A trade can lose money and PASS. A trade can make money and FAIL. That is the point.

## Where the sponsor tech sits (for judges)

- **Zetaris (data layer):** the agent never reads journal files directly. All
  trade + notes lookups go through Zetaris as the data harness — one governed
  endpoint over the journal CSV and the trader's notes, joined at query time.
  (Two-mode pipe: a local CSV reader with the identical contract runs until the
  Zetaris instance is provisioned; the swap is one function — see
  `src/auditor/data_pipe.py`.)
- **Meterless (engine patterns, implemented in Python from their published
  specs — see `docs/meterless.md`):** Meterless publishes four engines as
  prompt-based specs with a Context Packet structure, no SDK, and directs
  builders to recreate the patterns in their own stack. This project is that
  recreation: **World Model** = the day's declared frame + running state;
  **H-MEM** = the journal row + day history every claim must cite, verified
  by the Evaluator (provenance); **Markovian** = one bounded audit unit per
  trade, nothing reaching a step except through the packet; **Scout Intent**
  = the one question plus its guardrails (grade process, never P&L; never
  predict; never signal), emitted by the Planner as the contract the Executor
  follows and the Evaluator checks. Planner / Executor / Evaluator are roles
  in sequence, not a Meterless engine. (Meterless's own use-case list names
  this build: "Trading Journal Intelligence.")
- **Cursor (build layer):** the project is built in Cursor; the repo history is
  the build log.

## Data

`data/trades_sample.csv` — a frozen 10-trade test set in the journal's own
per-trade log format (date, time, instrument, model, grade, direction, HTF
alignment, 800 EMA position, news, risk $, result, P&L $, notes), with expected
verdicts in `data/expected_verdicts.md` so every demo run is checkable.

## Status

Build week Oct 22–27, 2026. Night 1: scaffold + frozen test set. Night 2
(Oct 23): rule engine fully wired; audit verified 10/10 against the frozen
answer key (`docs/sample-audit-output.txt`); Context Packet integration
landed. Night 3 (Oct 26): strict room ruling applied — trade #10 flips to
FAIL (5 PASS / 5 FAIL); Meterless mapping rewritten to the four published
engines (`docs/meterless.md`). Run it: `python3 run_audit.py`.
