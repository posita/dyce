<!---
Design notes for the Expr / roll-tree system.
Captured from conversation 2026-04-17/18. Ephemeral — not intended for publication.
-->

# Expr / Roll Tree Design Notes

## Motivation

We want to represent arbitrary dice computations as an AST-like structure that
can be constructed using operators and other methods.
This is the design space that `r.py` occupies in dyce-fork, but we want to
think through the design from scratch rather than porting it directly.

## Requirements

1. **Trace how a roll was reached** — e.g. "you rolled 3 on the d6, 5 on the
   d8, summed to 8."
2. **Lazy evaluation** — build the expression, then enumerate or roll later.
3. **Serialize/inspect the computation** — e.g. for display in a VTT, or for
   translating from a proprietary dice grammar.

Requirements 1 and 2 are definitively in scope.
Requirement 3 is considered derivable from 1 and 2: the `Expr` tree itself is
the inspectable/serializable artifact, and rolling it gives a `RollResult` tree
for the trace.

## Core design question: separate type or integrated?

**Option A — Distinct `Expr` type wrapping `H`:**

```python
d6_expr = Expr(H(6))
result = (d6_expr + d6_expr).roll()  # returns (outcome, trace)
```

Clean separation: `H` stays as "computed distribution", `Expr` is "unevaluated
computation."
Users have to lift `H` into `Expr` explicitly, but shorthands can cover this
(see below).

**Option B — `H` itself is a node:**

`H.__add__` already returns a new `H` by enumerating eagerly.
Making `H` sometimes return a lazy node would require changing `H`'s semantics
or adding a "lazy mode" — both messy.

**Decision: Option A.**

## Node hierarchy (sketch)

```python
Expr                          # abstract base
├── Leaf(h: H)                # a die — roll it, or use h directly
├── Const(value)              # a fixed value (distinct from a one-sided die)
├── UnaryOp(op, operand)      # -expr, abs(expr), ~expr
├── BinaryOp(op, lhs, rhs)    # expr + expr, expr * expr, etc.
├── Repeat(n, expr)           # n @ expr — roll expr n times and sum
├── Pool(exprs)               # ordered collection, analogous to P
└── Apply(func, expr)         # arbitrary transform
```

Operators on `Expr` return new `Expr` nodes rather than evaluating.

## Terminal operations

```python
expr.h() -> H            # enumerate all outcomes (may be intractable for recursive mechanics)
expr.roll() -> RollResult  # random sample with trace
```

## RollResult

```python
@dataclass
class RollResult:
    outcome: object
    probability: Fraction   # probability of this specific outcome at this node
    expr: Expr              # which node produced this
    children: list[RollResult]
```

For `(d6 + d8).roll()` yielding 9:

```
RollResult(9, Fraction(1, 36), BinaryOp(+), [
    RollResult(3, Fraction(1, 6), Leaf(H(6)), []),
    RollResult(6, Fraction(1, 8), Leaf(H(8)), []),
])
```

### On probability representation

Initially considered using a sentinel histogram
`H({SENTINEL: n-1, outcome: count})` to represent the full local probability
landscape at each decision point.
Rejected because it is always exactly two entries — the sentinel absorbs all
non-rolled outcomes regardless of how many distinct values the die has.
(Example: `H({1: 2, 2: 3, 3: 1})` rolled a 2 → `{SENTINEL: 4, 2: 3}` — still
two entries.)
Since there is never more than one non-sentinel outcome, `H` is the wrong type;
`probability: Fraction` (rolled count / total count) captures the same
information more simply.

## Handling `expand` / recursive mechanics

`expand` is the hard case because the two use cases have fundamentally different
computational characters:

- **Enumeration**: branch over all outcomes, weight by probability, accumulate
  full `H` — this is what current `expand` does.
- **Rolling/tracing**: pick one outcome, recurse down that branch, record the
  path — no weighting or accumulation needed.

### Option 1: First-class `Expr` nodes for common mechanics

Built-in mechanics like `explode_n` become first-class `Expr` nodes with both
`.h()` (delegates to eager `expand`) and `.roll()` (simple recursive sampler):

```python
@dataclass
class ExplodeExpr(Expr):
    source: H
    n: int

    def h(self) -> H:
        return explode_n(self.source, n=self.n)

    def roll(self) -> RollResult:
        rolls = []
        h = self.source
        remaining = self.n
        while True:
            outcome = h.roll()
            rolls.append(RollResult(outcome, Fraction(h[outcome], h.total), Leaf(h), []))
            if remaining == 0 or outcome != max(h):
                break
            remaining -= 1
        return RollResult(sum(r.outcome for r in rolls), ..., self, rolls)
```

### Option 2: Context manager dispatch for custom `expand` callbacks

For custom `expand` callbacks (not covered by first-class nodes), a context
manager switches `expand` to sampling mode using `contextvars`:

```python
_SAMPLE_MODE: ContextVar[bool] = ContextVar("_SAMPLE_MODE", default=False)

def expand(callback, h, **kwargs):
    if _SAMPLE_MODE.get():
        return _expand_sample(callback, h, **kwargs)
    return _expand_enumerate(callback, h, **kwargs)

@contextmanager
def rolling():
    token = _SAMPLE_MODE.set(True)
    try:
        yield
    finally:
        _SAMPLE_MODE.reset(token)
```

`_expand_sample` rolls one outcome from `h`, calls
`callback(HResult(outcome=rolled, h=h))`, and returns a `RollResult`.
Because the callback's internal `expand(callback, result.h)` call also sees
`_SAMPLE_MODE=True`, the whole recursion stays in sampling mode without the
callback author doing anything differently.
One callback implementation serves both enumeration and tracing.

These two options are complementary: first-class nodes for built-in mechanics,
context manager for custom `expand` callbacks.

### Rejected: protocol unification

Considered defining `HishT` / `PishT` protocols that both `H`/`P` and `Expr`
wrappers implement, so `expand` callbacks could work with either.
The wrapper would present `H({rolled_value: 1})` to `expand`'s branch iterator
(so only one branch is explored) while exposing the original `H(6)` for `max()`
and recursion.
Rejected as a "square peg in a round hole": the dual-view wrapper is clever but
overloads a single object with two responsibilities, and `expand` can't tell the
difference between a real `H` and a tracing wrapper pretending to have one
outcome.
The cleaner boundary is: `HResult.h` always carries the original `H`
(for correct recursion), and the `RollResult` carries probability information
separately.

## Shorthands

Shorthands are not a concern.
`P(6)` is already a shorthand for `P(H(6))`.
Similarly, `Px(6)` (name TBD) could be shorthand for `Leaf(P(H(6)))`, etc.

## `.roll()` on `H` and `P`

Keeping `.roll()` on `H` and `P` blurs the boundary between mathematical
objects (distributions) and the sampling/tracing layer (`Expr`).
It could mislead users into thinking they get tracing behavior when they don't.

Options:
- Remove immediately (breaking change).
- Deprecate once `Expr` exists, pointing users toward `Leaf(H(6)).roll()`.
- Keep as convenience shorthands with clear documentation that they do not
  produce `RollResult` traces.

Not yet decided.

## Open questions / still thinking

- Exact naming: `Expr`, `Node`, `R`, something else?
- `Const` vs `Leaf(H({n: 1}))` — keep `Const` explicit so traces can
  distinguish "fixed modifier" from "one-sided die."
- Pool selection in traces — does rolling a `Pool` node show discarded dice
  alongside selected ones in the `RollResult` children?
- `Repeat(n, expr)` semantics vs. current `n @ H` — same distribution, but
  trace shows `n` separate rolls (probably the desired behavior).
- Whether `rolling()` context manager is the right API surface, or whether
  `.roll()` on `Expr` is sufficient and the context manager is an implementation
  detail.
- Fate of `.roll()` on `H` and `P` (see above).
