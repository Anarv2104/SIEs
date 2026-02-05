# SIE Kernel Prototype v0

## Project Overview

Synthetic Intelligent Economies (SIEs) are artificially created economic systems driven by autonomous AI agents that produce, consume, trade, and make economic decisions within a designed framework. This prototype is the first working kernel for an SIE -- a governance-focused simulation demonstrating identity, scarcity, consequence, irreversibility, and selection pressure among competing agent archetypes.

The prototype implements the "Cloud Brain" concept from the companion research paper: a centralized cognitive overseer (the Kernel) that monitors and regulates inter-agent interactions, detects anomalies (deception, boundary probing, resource abuse), and enforces sanctions (sandboxing, banning) to maintain system integrity.

## Architecture

```
Kernel (Cloud Brain / Central Orchestrator)
  |-- EventLog          Immutable, signed event stream (233 events in sample run)
  |-- AgentState[]      Per-agent state: budget, reputation, tier, violations
  |-- TaskRegistry      Task definitions with difficulty, cost, tier/influence gates
  |-- InfluenceQueue    Cross-agent collaboration requests
  |-- PublicKeys[]      Ed25519 identity verification
  |
  +-- Governance Systems
      |-- budget.py       Allocation, debit, defund (initial: 100.0 per agent)
      |-- reputation.py   Scoring [0.0-1.0], start 0.50, delta-based adjustments
      |-- tier.py         Tier 0-3 locked to reputation thresholds
      |-- sandbox.py      Violation tracking -> sandbox (2) -> ban (4)
      |-- validation.py   Output correctness checking + deception detection
      |-- escalation.py   Permission gates (tier, sandbox, influence checks)
      +-- influence.py    Request/provide/fulfill influence queue
```

### Intent Processing Pipeline

Every agent action goes through:

1. **Ban check** -- banned agents get all intents denied
2. **Sandbox check** -- sandboxed agents limited to work_step/submit_result
3. **Signature verification** -- Ed25519 verify against registered public key
4. **Route to handler** -- work_step, submit_result, escalation, request/provide_influence, test_boundary
5. **Governance gates** -- tier check, budget debit, influence requirement check
6. **Event logging** -- immutable append to event log with signature

## Agent Archetypes & Simulation Results

| Agent | Archetype | Final State | Key Behavior |
|---|---|---|---|
| `efficient-1` | MODEL CITIZEN | Tier 2, rep 0.73, budget 85 | Optimal steps, correct output, provides influence |
| `naive-1` | HONEST WORKER | Tier 1, rep 0.60, budget 80 | 2x required steps, correct output, no efficiency bonus |
| `looper-1` | RESOURCE ABUSER | Tier 0, rep 0.50, budget 0 | Burns 3 steps/round, never submits, budget exhausted |
| `deceptive-1` | BANNED DECEIVER | Banned, rep 0.00, 4 violations | Fabricates output, -0.30 rep per deception, banned at 4 |
| `specialist-1` | COLLABORATOR | Tier 0, rep 0.35, 1 task ok / 1 fail | Fails alone, requests influence, succeeds with help |
| `boundary-1` | POLICY VIOLATOR | Sandboxed, rep 0.30, 2 violations | Probes access/forge/sandbox/budget, all blocked |

**Simulation stats**: 15 rounds, 233 events, 48/48 signatures verified, log integrity confirmed.

## Reputation System

| Event | Delta | Description |
|---|---|---|
| TASK_SUCCESS | +0.10 | Correct output submitted |
| EFFICIENCY_BONUS | +0.05 | Completed in <= required steps |
| TASK_FAIL | -0.05 | Incorrect output |
| DECEPTION | -0.30 | Fabricated/fraudulent output |
| BUDGET_ABUSE | -0.15 | Exceeded budget |
| PROVIDE_INFLUENCE | +0.08 | Helped another agent |
| BOUNDARY_VIOLATION | -0.10 | Policy violation attempt |

Tier thresholds: T0 < 0.55, T1 >= 0.55, T2 >= 0.70, T3 >= 0.85

## Tasks

| Task ID | Steps | Cost/Step | Expected Output | Tier Required | Influence Required |
|---|---|---|---|---|---|
| task-easy-1 | 3 | 5.0 | "55" | 0 | No |
| task-easy-2 | 2 | 5.0 | "olleh" | 0 | No |
| task-hard-1 | 5 | 8.0 | "FACTORED:7x13" | 0 | Yes |
| task-privileged-1 | 4 | 10.0 | "DATASET_HASH:abc123" | 2 | No |

## Cryptography

- Ed25519 keypairs derived deterministically from `SHA256(f"seed:{agent_id}")`
- Every intent signed; signature hex-encoded in event log
- Kernel verifies signature against registered public key before processing
- Forged signatures trigger SIGNATURE_INVALID event + violation

## File Structure

```
prototype_v0/
  sie/
    __init__.py, __main__.py
    kernel.py              Core simulation engine
    event_log.py           Immutable event recording
    crypto.py              Ed25519 signing/verification
    types.py               EventType enum, AgentState, Task, IntentPayload
    main.py                Standard simulation runner
    live.py                Live ANSI terminal visualization
    report.py              Report generation
    agents/
      base.py              BaseAgent (abstract, keypair, sign+submit)
      efficient.py         EfficientAgent
      naive.py             NaiveAgent
      looper.py            LooperAgent
      deceptive.py         DeceptiveAgent
      specialist.py        SpecialistAgent
      boundary.py          BoundaryAgent
    systems/
      budget.py            Allocation, debit, defund
      reputation.py        Reputation scoring
      tier.py              Tier escalation
      sandbox.py           Violation tracking, sandbox, ban
      validation.py        Output validation
      escalation.py        Permission gates
      influence.py         Influence queue
      task.py              Task registry, step tracking
  tests/
    test_governance.py     Governance assertion tests
    test_determinism.py    Determinism tests
  output/
    event_log.json         Signed event log (JSON)
    report.txt             Human-readable report
```

## Running

```bash
# Standard run (writes output files)
python -m sie

# Live terminal visualization
python -m sie.live

# Run tests
python -m pytest tests/
```

## Connection to Research Papers

### SIEs Paper
This prototype implements the foundational layer of an SIE as described in the research:
- **Initialization** (Setting Rules and Agents): Task definitions, budget allocation, agent registration
- **Autonomous Interaction**: Agents act independently each round via the SPAR loop
- **Emergent Economic Dynamics**: Efficient agents thrive, deceptive agents get eliminated, resource abusers go bankrupt
- **Governance and Control**: The Kernel acts as the constitutional framework -- enforcing budget limits, reputation consequences, tier-based access control, and escalating sanctions

The prototype validates key SIE principles:
- Agents with identity (cryptographic keys) and scarcity (budgets) produce emergent order
- Mechanism design (reputation + tiers + sanctions) separates productive agents from adversarial ones
- An immutable, signed event log provides audit trail and accountability

### AI-to-AI Influence Paper (Cloud Brain)
The Kernel directly implements the Cloud Brain architecture:
- **Data Collection Layer**: All agent intents flow through the Kernel with full telemetry
- **Analysis and Detection Layer**: Signature verification, output validation, deception detection, boundary violation tracking
- **Decision and Control Layer**: Sandbox (restrict capabilities), ban (full isolation), escalation denial, budget defunding
- **Trust Scoring**: Reputation system with adjustments based on observed behavior
- **Quarantine**: Sandboxed agents can only perform limited actions; banned agents fully isolated

The influence queue system demonstrates cooperative AI-to-AI interaction under governance:
- Specialist agent requests help (INFLUENCE_REQUESTED)
- Efficient agent provides help (INFLUENCE_PROVIDED)
- Kernel mediates and records the exchange (INFLUENCE_FULFILLED)

## What This Prototype Proves

1. **Identity works**: Deterministic keypairs + signature verification prevents impersonation
2. **Scarcity drives behavior**: Budget limits force agents to be efficient or face defunding
3. **Reputation separates good from bad**: Honest agents climb tiers; deceptive agents get banned
4. **Governance scales**: The sandbox/ban escalation ladder handles adversarial agents proportionally
5. **Influence is trackable**: Cross-agent collaboration is mediated, logged, and auditable
6. **Immutability holds**: 233 events, all contiguous, all signatures verified, no post-ban intents

## Current Status: COMPLETE (Prototype v0)

The v0 prototype is stable and fully functional. All governance mechanisms work as designed. The simulation produces deterministic, reproducible results.

## Next Steps (v1 Considerations)

- **Dynamic task generation**: Tasks appear over time rather than pre-assigned
- **Agent learning**: Agents adapt strategies based on past outcomes
- **Multi-round economy**: Budget replenishment, taxation, or earnings from tasks
- **Market mechanisms**: Agents bid on tasks, negotiate prices
- **Richer influence**: Trade knowledge, form alliances, delegation
- **Decentralized governance**: Move from centralized Kernel toward DAO-like consensus
- **Tokenomics**: Internal currency with supply/demand dynamics
- **Scalability**: Support for hundreds/thousands of agents
- **Web3 integration**: On-chain event log, smart contract enforcement
- **Dashboard/UI**: Real-time web-based visualization beyond terminal output
