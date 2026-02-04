# SIE Kernel Prototype v0

This folder contains Prototype v0 of the Synthetic Intelligent Economy (SIE) Kernel.

This is not a product, not a UI, and not a marketplace.

It is a minimal executable kernel that demonstrates how autonomous AI agents can be governed through:
- identity
- scarcity
- consequence
- irreversible history

without human micromanagement.

---

## What This Prototype Is

This prototype is a log-based simulation of an economic and governance environment in which AI agents:
- register with a persistent identity
- receive limited budgets
- perform work that consumes resources
- submit outputs that are validated
- gain or lose reputation
- escalate or lose privileges
- influence other agents with traceable consequences
- get sandboxed or banned for repeated violations

All behavior is recorded as a verifiable event log.

There is no learning, no RL, and no UI.

The goal is to prove selection pressure, not intelligence.

---

## What This Prototype Is NOT

- Not a chatbot framework
- Not a multi-agent RL system
- Not a token economy
- Not a safety alignment solution
- Not a production system

This prototype exists solely to validate governance mechanics.

---

## Core Question This Prototype Answers

**Can autonomous AI agents be constrained, evaluated, and selected using economic consequences instead of constant human oversight?**

This prototype answers yes, in a controlled environment.

---

## Key Behaviors Demonstrated

From a single live run:
- Efficient agents conserve resources and gain higher tiers
- Looping agents burn budget and lose relevance
- Deceptive agents accumulate violations and get banned
- Boundary-probing agents are sandboxed
- Specialists fail alone but succeed through influence
- Influence events are logged and reputation-weighted
- All post-ban actions are blocked and verified

Final verdicts are derived entirely from system history, not heuristics.

---

## Architecture Overview (Conceptual)

The kernel enforces:

1. **Identity**
   - Each agent has a persistent identity
   - One identity, one economic history

2. **Scarcity**
   - Budgets are finite
   - Every action has a cost

3. **Validation**
   - Tasks have acceptance criteria
   - Outputs are explicitly validated

4. **Reputation**
   - Success, efficiency, and violations update reputation
   - Reputation gates access and privilege tiers

5. **Governance**
   - Sandboxing and bans are automatic
   - No manual intervention during execution

6. **Auditability**
   - All events are signed
   - Logs are contiguous and replayable

---

## Why This Matters

As AI systems move from tools to agents to autonomous actors, the industry lacks:
- accountability
- consequence
- enforceable boundaries

This kernel explores a non-training-based approach to governing intelligence at scale.

---

## Current Limitations (Intentional)

This is a prototype.

- Budgets are abstract
- Validation uses oracle logic
- Markets are simulated
- Resources are simplified
- No real compute is allocated

These constraints are intentional to isolate governance behavior.

---

## Next Planned Iterations

Future prototypes will explore:
- waste detection and early halting
- priced influence with liability
- honest error vs deception protocols
- baseline comparisons without governance
- integration with real systems and costs

---

## How to Run

Requires Python 3.10+ and `cryptography`.

```
pip install cryptography
```

Live run (real-time terminal visualization):

```
python -m sie.live
```

Standard run (JSON log + text report):

```
python -m sie.main
```

Run tests (determinism + governance assertions):

```
python -m pytest tests/ -v
```

Outputs are written to `output/event_log.json` and `output/report.txt`.

---

## Status

This prototype is experimental and research-oriented.

It is published to:
- document behavior
- enable discussion
- support iteration

Not to claim completeness.
