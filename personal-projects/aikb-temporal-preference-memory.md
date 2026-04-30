---
tags: [aikb, memory, temporal, preferences, retrieval, ranking, user-model, design]
status: planning
last_updated: 2026-04-17
---

# AIKB Temporal Preference Memory
**Last Updated:** 2026-04-17
**Summary:** Design for upgrading AIKB from recency-aware retrieval to a versioned temporal memory system that lets agents track, resolve, and explain how user preferences and decisions change over time.

---

## Goal

Make AIKB capable of answering four questions reliably:

1. What does the user want right now?
2. What did the user want at a previous point in time?
3. What changed, and why does the system believe it changed?
4. Which preferences are durable versus one-off or provisional?

The desired end state is not just better search. It is a memory system that can maintain an evolving model of the user's preferences, workflow habits, tolerances, and decisions without collapsing old and new guidance into one flat relevance ranking.

---

## Why Current Search Is Not Enough

Current `aikb_search` already has useful temporal behavior:
- recency boost
- explicit `before` / `after` / `as_of` filters
- event indexing with `ts_utc`
- early temporal graph support

That is enough to prefer newer text and answer some historical queries, but it is not enough to model changing truth.

Current limitations:
- timestamps exist, but most memories are still treated as plain chunks
- no stable memory identity beyond file/chunk position
- old and new preferences compete in ranking instead of having explicit supersession
- little distinction between enduring preferences, temporary instructions, and inferred habits
- no resolver layer that turns evidence into a "current preference view"
- no first-class explanation for why one preference won over another

---

## Design Principles

1. Prefer explicit state transitions over implicit recency.
2. Separate evidence from resolved current truth.
3. Preserve history instead of overwriting it.
4. Track confidence and source reliability.
5. Make retrieval explainable enough for debugging and evals.
6. Allow soft inference from repeated behavior, but keep it lower confidence than direct user instruction.
7. Keep rollout incremental and compatible with the current AIKB markdown + runtime pipeline.

---

## Core Idea

Introduce a versioned preference and decision layer above raw notes/events.

Instead of storing only "the user said X on date Y", AIKB should store memory records that can remain active, expire, be narrowed, or be superseded by later records.

This creates two distinct layers:

1. Evidence layer
- runtime events
- captured decisions
- canonical docs
- review-approved candidates

2. Resolved memory layer
- current active preferences
- past preferences with validity windows
- conflicts awaiting resolution
- synthesized "current truth" views

Search still matters, but it becomes one input into resolution rather than the final source of truth.

---

## Memory Types

AIKB should add typed memory records for:

- `workflow_preference`
- `communication_preference`
- `tool_preference`
- `coding_preference`
- `risk_preference`
- `operational_preference`
- `project_decision`
- `standing_instruction`
- `temporary_instruction`
- `inferred_habit`
- `open_question`
- `conflict_record`

These types are important because ranking and lifecycle rules differ by type. A direct standing instruction should out-rank an inferred habit even if the inferred habit is more frequently observed.

---

## Proposed Memory Record Schema

Each resolved memory record should have:

```yaml
id: mem_pref_01
memory_type: communication_preference
subject: user
scope: global
topic: answer-length
statement: Prefer concise final answers unless extra detail is requested.
status: active
confidence: 0.98
source_reliability: direct_user_instruction
evidence:
  - kind: runtime_event
    ref: event:2026-04-17T15:04:00Z
  - kind: canonical_doc
    ref: AGENTS.md#final-answer-instructions
valid_from: 2026-04-17T15:04:00Z
valid_to: null
supersedes:
  - mem_pref_00
superseded_by: []
volatility: low
durability: standing
review_state: approved
explanation: Reaffirmed in current session and aligned with existing instruction set.
```

Key fields to add beyond today's search index:
- `id`: stable identifier
- `subject`: who/what the memory is about
- `scope`: global, repo, project, toolchain, session
- `topic`: normalized preference topic
- `status`: active, superseded, expired, tentative, conflicted
- `source_reliability`: direct user statement, explicit doc, inferred behavior, agent assumption
- `valid_from` / `valid_to`: temporal window of applicability
- `supersedes` / `superseded_by`: explicit state transition edges
- `volatility`: expected change rate
- `durability`: standing vs temporary

---

## Evidence Model

Each resolved memory should point back to evidence rather than duplicating unsupported conclusions.

Evidence items can come from:
- direct user chat or terminal instruction
- AIKB canonical docs
- runtime capture entries
- repeated user corrections
- repeated accepted patterns in edits or workflow

Evidence should also be typed:
- `explicit_instruction`
- `explicit_preference`
- `explicit_decision`
- `behavioral_signal`
- `agent_inference`
- `promotion_review`

This allows the resolver to treat "user explicitly said this" as stronger than "agents inferred this from three similar sessions."

---

## Resolution Lifecycle

### 1. Capture

New evidence is captured from runtime events, explicit `capture`, promotion work, or future behavioral inference jobs.

### 2. Normalize

The system extracts:
- subject
- scope
- topic
- candidate statement
- confidence
- evidence type
- whether the evidence looks durable or temporary

### 3. Match Existing Memory

Candidate memory is matched against existing active and historical records by:
- exact topic and scope
- semantic similarity
- stable IDs if already linked
- contradiction markers

### 4. Decide Action

Possible actions:
- reinforce an existing active memory
- create a new memory
- narrow an existing memory's scope
- mark an old memory superseded
- open a conflict for review

### 5. Publish Resolved View

The system updates the active memory set and keeps old records queryable historically.

---

## Conflict Model

Conflicts should become first-class instead of merely noisy competing results.

Conflict triggers:
- same topic/scope with opposite polarity
- same topic/scope with materially different recommendation
- temporary instruction overlapping a standing preference
- old active record not explicitly retired when newer contradictory evidence appears

Conflict record example:

```yaml
id: conflict_answer_length_2026_04_17
topic: answer-length
scope: global
status: open
records:
  - mem_pref_00
  - mem_pref_01
reason: newer direct instruction contradicts earlier broader preference
recommended_resolution: supersede mem_pref_00 with mem_pref_01
```

The important change is that conflicts should feed the preference resolver, not only a separate review queue.

---

## Retrieval Architecture

Best-in-class temporal memory needs a resolver on top of search.

### Retrieval flow

1. Evidence recall
- lexical, vector, graph, and temporal recall over raw evidence

2. Memory record recall
- fetch candidate resolved memories by topic, subject, and scope

3. Temporal resolution
- choose active record for "current" queries
- choose nearest valid record for historical queries
- surface changes for "what changed?" queries

4. Explanation emission
- include why the record was selected
- include supersession chain where relevant
- include evidence references

### Query classes

The system should explicitly support:
- current truth: "what does the user prefer for X?"
- historical truth: "what was the preference as of 2026-03-01?"
- change queries: "what changed about X recently?"
- stability queries: "is this a standing preference or a recent session quirk?"
- ambiguity queries: "what is uncertain or conflicted right now?"

---

## Ranking Changes

Current ranking heavily rewards freshness. That is useful, but not sufficient.

Ranking for memory resolution should consider:
- semantic relevance
- exact topic match
- scope match
- source reliability
- confidence
- durability
- reinforcement count
- contradiction penalty
- temporal validity
- canonicality

Illustrative scoring:

```text
resolved_score =
  relevance
  + scope_match
  + source_reliability
  + confidence
  + reinforcement
  + active_validity
  - contradiction_penalty
```

Recency should remain a tie-breaker for volatile topics, but not override a stable high-confidence standing instruction without a real contradiction or supersession.

---

## Behavioral Learning

To evolve understanding over time, AIKB should learn from repeated operator behavior, not only explicit capture.

Candidate inferred habits:
- prefers concise closeouts
- prefers action over planning for code tasks
- tolerates direct pushes to `main` for tiny doc fixes
- prefers specific tools or command styles

Rules:
- inferred habits start low-confidence
- they never silently override direct instructions
- repeated confirmation increases confidence
- explicit contradiction rapidly decays or retires them

This is the path from "search over notes" to "adaptive collaborator memory."

---

## Temporal Graph Expansion

The current temporal graph is a useful seed, but it should evolve from document/entity links into a memory-state graph.

Nodes should include:
- evidence items
- resolved memory records
- topics
- scopes
- projects
- agents

Edges should include:
- `supports`
- `contradicts`
- `supersedes`
- `narrows`
- `applies_to_scope`
- `reaffirmed_by`
- `derived_from`

This would make temporal graph queries useful for:
- preference change timelines
- unresolved conflicts
- chain-of-reasoning explanations
- "why do we believe this is the current truth?"

---

## Evaluation

A best-in-class system needs temporal correctness evals, not just retrieval relevance evals.

Add benchmark sets for:
- current preference recall
- historical snapshot correctness
- stale memory suppression
- conflict detection accuracy
- supersession correctness
- inferred-habit calibration

Core metrics:
- current_truth_hit@k
- historical_truth_hit@k
- stale_preference_error_rate
- conflict_precision / recall
- supersession_accuracy
- explanation_support_rate

The important shift is that an answer can be relevant but still wrong if it returns a stale preference as if it were current.

---

## Incremental Rollout

### Phase 1: Typed records + stable IDs

- add memory-record schema for resolved preferences/decisions
- add stable IDs and validity fields
- build a minimal preference resolver for explicit user instructions
- keep search index compatible with existing chunks

### Phase 2: Supersession + conflicts

- add conflict and supersession detection
- generate review candidates automatically
- allow historical queries over resolved records

### Phase 3: Behavioral inference

- infer low-confidence habits from repeated patterns
- add reinforcement and decay rules
- surface inferred vs explicit provenance clearly

### Phase 4: Resolver-first retrieval

- answer preference queries from resolved memory first
- fall back to evidence search when unresolved
- emit explanations and trace objects by default for debugging

### Phase 5: Graph-backed temporal reasoning

- upgrade the temporal graph to represent memory states and transitions
- support change timelines, dependency reasoning, and contradiction traversal

---

## Minimum Viable Implementation

If we want the smallest useful slice, build this first:

1. Schema for resolved memory records
2. Stable memory IDs
3. Explicit `supersedes` handling
4. A resolver for direct user instructions
5. Query API:
   - `current_preference(topic, scope)`
   - `preference_as_of(topic, date, scope)`
   - `what_changed(topic, since, scope)`
6. Eval set with known preference transitions

This would already move AIKB from "recency-aware search" to "versioned preference memory."

---

## Open Questions

- Should resolved memories live as markdown, YAML, SQLite rows, or a hybrid model?
- How much automatic supersession is safe without human review?
- Which preference topics deserve strict schemas versus free-text statements?
- How should repo-local preferences inherit from or override global user preferences?
- When should inferred habits be surfaced to the user for confirmation?
- How much explanation should agents see by default versus on demand?

---

## Recommendation

The highest-leverage next step is not a better embedding model. It is a typed, versioned preference-memory layer with explicit supersession and conflict handling.

Once AIKB can represent "old preference retired, new preference active, confidence high, evidence here," the existing search stack becomes much more powerful because it can retrieve evidence in service of state resolution rather than forcing ranking alone to approximate evolving truth.

---

## Next Actions

- Define `memory-record` schema extensions for temporal preference records.
- Choose storage model for resolved records and transition edges.
- Extend capture/review pipeline to classify direct user instructions into typed memory candidates.
- Build a minimal resolver for current-truth and as-of queries.
- Add eval fixtures that include real preference changes over time.
