# Glossary

## Outcome

A possible result represented in a calculation.

## Count

An integer assigned to an outcome indicating its weight relative to other outcomes.

## Histogram (`H`)

A [`dyce.H`][dyce.H] object is an immutable map of outcomes to counts.

## Probability distribution

A probability distribution (sometimes shortened to “distribution”) assigns a probability to each possible outcome.
[`H.probability_items()`][dyce.H.probability_items] yields outcome and probability pairs, using exact fractions by default to represent probabilities.
For outcomes with positive counts, each specific outcome’s probability is its count divided by [`H.total`][dyce.H.total].
(Outcomes with zero counts have probabilities of zero.)

## Pool (`P`)

An immutable sorted sequence of [`H`][dyce.H] objects.

## Roll

A tuple of outcomes from a [`P`][dyce.P], sorted from least to greatest.
Outcomes that cannot be compared are sorted by the natural order of their string representations.
Roll order is independent of pool order.

## Sample

Outcomes selected at random based on their counts (relative weights).
[`H.sample()`][dyce.H.sample] returns a single outcome.
[`P.sample()`][dyce.P.sample] returns a roll.

## Lowest terms

Histogram counts with their greatest common divisor reduced to one.
[`H.lowest_terms()`][dyce.H.lowest_terms] divides positive counts by their greatest common divisor, preserving probabilities exactly.
It removes outcomes with zero counts unless `preserve_zero_counts=True`.

## Quantize

Reduce histogram counts to fit within a specified bit width, approximating their relative weights.
[`H.quantize_counts()`][dyce.H.quantize_counts] can change probabilities and reduce positive counts to zero.
This method is experimental.

## Experimental

An API whose interface may change or which may be removed in a future release.
Experimental APIs are marked in the API reference.

## Deprecated

An API retained for compatibility whose use is discouraged.
Consult its deprecation notice for replacement and removal guidance.
