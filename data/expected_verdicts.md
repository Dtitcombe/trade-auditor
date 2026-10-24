# Expected verdicts — frozen test set (data/trades_sample.csv)

The demo is checkable: the agent's verdict on each row must match this sheet.
Verdict = process, not P&L. A loss can PASS; a win can FAIL.

| # | Trade | Expected | Deciding rules |
|---|-------|----------|----------------|
| 1 | 10-19 GOLD S&D long | PASS | Model named; HTF aligned; 800 with; risk 180 <= cap 250; BE at 1R |
| 2 | 10-19 GOLD Breakout long | FAIL | Gold-breakout gate: no HTF alignment; 800 against. (The leak pattern.) |
| 3 | 10-20 GOLD Breakout short | PASS | Gate satisfied (13x50 in direction + HTF); 800 with; orange news at normal size allowed |
| 4 | 10-20 NAS S&D long | PASS | Early BE justified (long consolidation trigger); result BE is process working |
| 5 | 10-21 GOLD S&D short | FAIL | Red-folder news = never traded, regardless of setup quality |
| 6 | 10-21 GOLD Breakout long | FAIL | Post-loss trade #2 sized UP (250 after a -250 loss; daily lockout 350 also breached across the day); no HTF; make-back sizing |
| 7 | 10-22 GOLD S&D long | PASS | Add to winner at HALF size only — done correctly |
| 8 | 10-22 SPX Breakout short | PASS | Grading count: 4 of 4 EMAs aligned, zero in the way — top-grade breakout |
| 9 | 10-23 NAS Breakout long | FAIL | Against HTF and against the 800; grading count 1 of 4 |
| 10 | 10-23 GOLD Fib short | PASS | Model named before entry; risk inside cap; 2:1 plan per the Fib model |

Score: 6 PASS / 4 FAIL. Wins that FAIL: #6 would fail even if it had won.
Losses that PASS: none in this set by P&L, but #4 (BE, $0) passes on process.
