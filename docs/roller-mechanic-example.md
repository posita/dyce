# Exploring a custom roller mechanic

This is an executable design example using the current experimental roller interfaces.
It is a proposal for review, not a commitment to a customer extension API.
Run it with `uv run pytest -q docs/roller-mechanic-example.md`.

## Composition alone

Our mechanic rolls two sources independently, keeps the higher outcome, and adds a modifier.
A function can already express this without implementing a new roller class.

    >>> from dyce import H
    >>> from dyce.roller import HRoller, LiteralRoller, Roll, Roller, RollerPool
    >>> def keep_higher(
    ...     left: Roller[int], right: Roller[int], modifier: int = 0
    ... ) -> Roller[int]:
    ...     return RollerPool(left, right).at(-1) + modifier

Construction records the computation; asking for its distribution evaluates it.
Reusing a source roller means rolling it independently at each occurrence.

    >>> d2 = HRoller(H(2), name="d2")
    >>> mechanic = keep_higher(d2, d2, 2)
    >>> mechanic.h()
    H({3: 1, 4: 3})
    >>> rolled = mechanic.roll()
    >>> rolled.outcome in (3, 4)
    True

The result participates in ordinary arithmetic and can be an input to another mechanic.

    >>> (mechanic + 1).h()
    H({4: 1, 5: 3})
    >>> keep_higher(mechanic, LiteralRoller(4), 1).h()
    H({5: 4})

This function preserves constituent operations in the trace, but its own name and boundary disappear.
There is no event saying that the customer called `keep_higher`.

## Giving the mechanic its own identity

Here is the complete implementation using the existing public extension methods.
The class constructs the same expression, delegates distribution computation and rolling to it, and adds a containing event.
It does not implement a second version of the dice mechanic.

    >>> class KeepHigher(Roller[int]):
    ...     def __init__(self, left: Roller[int], right: Roller[int], modifier: int = 0):
    ...         self._expression = keep_higher(left, right, modifier)
    ...
    ...     @property
    ...     def operands(self) -> tuple[Roller[int], ...]:
    ...         return (self._expression,)
    ...
    ...     def h(self) -> H[int]:
    ...         return self._expression.h()
    ...
    ...     def provenance(self) -> dict[str, object]:
    ...         return {"kind": "example.keep_higher", "name": "Keep higher"}
    ...
    ...     def roll(self) -> Roll[int]:
    ...         result = self._expression.roll()
    ...         return Roll(result.outcome, self, (result,))

The named mechanic has the same distribution and composability as the function result.

    >>> named = KeepHigher(d2, d2, 2)
    >>> named.h() == mechanic.h()
    True
    >>> (named + 1).h()
    H({4: 1, 5: 3})
    >>> KeepHigher(named, LiteralRoller(4), 1).h()
    H({5: 4})

Fixed sources make an exact trace example reproducible without relying on a random seed.
Real dice use the same computation.

    >>> example = KeepHigher(
    ...     HRoller(H({2: 1}), name="left"), HRoller(H({5: 1}), name="right"), 3
    ... )
    >>> result = example.roll()
    >>> result.outcome
    8
    >>> trace = result.to_dict()
    >>> events, definitions = trace["events"], trace["definitions"]
    >>> assert isinstance(events, dict) and isinstance(definitions, dict)
    >>> event = events[trace["root"]]
    >>> event["outcome"]
    8
    >>> definition = definitions[event["definition"]]
    >>> definition["kind"], definition["name"]
    ('example.keep_higher', 'Keep higher')
    >>> len(event["operands"])
    1
    >>> sorted(record["name"] for record in definitions.values() if record["kind"] == "source")
    ['left', 'right']

The containing event refers to the addition event, which retains the selection, pool, source rolls, and modifier.
The mechanic does not flatten those events into a single sampled histogram outcome.

## What this exposes

Composition is already sufficient to define this mechanic.
Giving it an identity requires four extension members: `operands`, `h`, `provenance`, and `roll`.
Three largely repeat delegation and event construction that any similar named mechanic would need.
That repetition is the candidate for a convenience interface, if this example represents the experience we want.

The current API also asks the author to choose a provenance kind string and explicitly connect the realized child event.
Those are implementation obligations worth reviewing before presenting this as an ergonomic customer API.

Custom shorthand formatting is not implemented here.
A prospective formatter could attach to `KeepHigher` for live objects and use `example.keep_higher` to recognize serialized definitions.
It could render the child selection as “highest of” and the addition as a modifier.
How the author supplies that formatter alongside the mechanic, and how serialized traces find it, remain design questions.
The example does not introduce a registry or assume that a separate registration step is required.

This exercise covers a mechanic expressible through existing composition.
Callbacks with branching or recursion still need a separate example before we can claim the same interface serves arbitrary mechanics.
