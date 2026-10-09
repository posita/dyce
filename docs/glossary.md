<!---
  Copyright and other protections apply.
  Please see the accompanying LICENSE file for rights and restrictions governing use of this software.
  All rights not expressly waived or licensed are reserved.
  If that file is missing or appears to be modified from its original, then please contact the author before viewing or using this software in any capacity.

  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Please keep each sentence on its own unwrapped line.
  It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
  Thank you!
  -->

# Glossary

## Outcome

A possible result represented in a calculation.

## Count

A nonnegative integer assigned to an outcome indicating its weight relative to other outcomes.
A count can represent the number of ways an outcome occurs.
Reducing counts to their lowest terms can change a count’s value without changing its probability or relative weight.

## Histogram (`H`)

A [`dyce.H`][dyce.H] object is an immutable map of outcomes to counts.

## Probability distribution

A probability distribution (sometimes shortened to “distribution”) assigns a probability to each possible outcome in a histogram.
[`H.probability_items`][dyce.H.probability_items] yields outcome and probability pairs, using fractions by default to represent exact probabilities.
For outcomes with positive counts, each specific outcome’s probability is its count divided by [`H.total`][dyce.H.total].
Outcomes with zero counts have probabilities of zero.

## Pool (`P`)

An immutable sorted sequence of [`H`][dyce.H] objects.

## Roll

A tuple of outcomes from a [`P`][dyce.P], sorted from least to greatest.
Outcomes that cannot be compared are sorted by the natural order of their string representations.
Roll order is independent of pool order.
An outcome’s position in a roll does not identify the histogram that produced that outcome.

## Outcome selection

The choice of outcomes by their positions in a sorted roll.
[`P.at`][dyce.P.at] sums selected outcomes into a histogram.
[`P.rolls_with_counts`][dyce.P.rolls_with_counts] yields selected rolls and their counts.

This is distinct from indexing or slicing a pool, which selects histograms from that pool, not outcomes from rolls.

## Sample

Outcomes selected at random based on their counts (relative weights).
[`H.sample`][dyce.H.sample] returns a single outcome.
[`P.sample`][dyce.P.sample] returns a roll.

## Lowest terms

Histogram counts with their greatest common divisor reduced to one.
[`H.lowest_terms`][dyce.H.lowest_terms] divides positive counts by their greatest common divisor, preserving probabilities exactly.
It removes outcomes with zero counts unless `preserve_zero_counts=True`.

## Quantization

A reduction of histogram counts to fit within a specified bit width, approximating their relative weights.
This reduction is lossy and can change probabilities or reduce positive counts to zero.
See the experimental [`H.quantize_counts` method][dyce.H.quantize_counts].

## Path probability

The probability of reaching a branch in (possibly recursive) [`expand`][dyce.expand] calls.
The `min_path_probability` parameter sets the threshold below which a branch is discarded.

## Truncation

The removal of branches from an [`expand`][dyce.expand] calculation because their path probability is below the threshold or they exceed Python’s recursion limit.
[`TruncationWarning`][dyce.TruncationWarning] reports this removal.
The resulting probabilities describe the remaining outcomes.
Returning an empty histogram from the callback intentionally excludes a branch and does not, by itself, cause a truncation warning.

## Experimental

An API whose interface may change or which may be removed in a future release.
Experimental APIs are marked in the API reference.

## Deprecated

An API retained for compatibility whose use is discouraged.
Consult its deprecation notice for replacement and removal guidance.
