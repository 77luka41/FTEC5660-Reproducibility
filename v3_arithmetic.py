"""Exact arithmetic tools for the declared v3 hybrid-system experiment.

The reachability tool exhaustively solves a remaining arithmetic subproblem. It
returns a boolean, never an expression or a replacement model proposal. This is
an oracle evaluator for a tiny domain, not evidence of better LLM reasoning.
"""
from collections import Counter
from fractions import Fraction
from functools import lru_cache
import re
import time

NUMBER = r'(?:-?\d+/[1-9]\d*|-?\d+(?:\.\d+)?)'
OPERATION = re.compile(rf'({NUMBER}) ([+*/-]) ({NUMBER}) = ({NUMBER}) \(left: ({NUMBER}(?: {NUMBER})*)\)')


def advance(numbers, line):
    """Validate a proposed action and its remaining multiset without repairing it."""
    match = OPERATION.fullmatch(line)
    if not match:
        raise ValueError('Not a canonical arithmetic operation')
    a, operator, b, c, tail = match.groups()
    a, b, c = map(Fraction, (a, b, c))
    remaining = list(numbers)
    # Removing twice also checks multiplicity when both operands are equal.
    remaining.remove(a)
    remaining.remove(b)
    if operator == '+': expected = a + b
    elif operator == '-': expected = a - b
    elif operator == '*': expected = a * b
    else: expected = a / b
    if expected != c:
        raise ValueError('Incorrect operation result (use exact fractions)')
    remaining.append(c)
    declared = list(map(Fraction, tail.split()))
    if Counter(remaining) != Counter(declared):
        raise ValueError('Remaining numbers do not match the operation')
    return declared


def state_after(puzzle, trace):
    numbers = list(map(Fraction, puzzle.split()))
    lines = trace.strip().splitlines() if trace.strip() else []
    if len(lines) > 3:
        raise ValueError('Expected at most three operation lines')
    for line in lines:
        numbers = advance(numbers, line)
    return numbers


class ReachabilityTool:
    """One instance per puzzle; cache work and CPU time are logged explicitly."""
    def __init__(self):
        self.calls = self.nodes = self.cache_hits = 0
        self.seconds = 0.0

        @lru_cache(maxsize=None)
        def reachable(state):
            self.nodes += 1
            if len(state) == 1:
                return state[0] == 24
            for i in range(len(state)):
                for j in range(i + 1, len(state)):
                    a, b = state[i], state[j]
                    rest = [v for k, v in enumerate(state) if k not in (i, j)]
                    outcomes = {a+b, a-b, b-a, a*b}
                    if b: outcomes.add(a/b)
                    if a: outcomes.add(b/a)
                    for outcome in sorted(outcomes):
                        if reachable(tuple(sorted(rest + [outcome]))):
                            return True
            return False
        self._reachable = reachable

    def can_reach_24(self, numbers):
        """Only scores post-action states; it never solves the original four inputs."""
        if not 1 <= len(numbers) <= 3:
            raise ValueError('The evaluator accepts only one to three remaining numbers')
        self.calls += 1
        start = time.perf_counter()
        result = self._reachable(tuple(sorted(numbers)))
        self.seconds += time.perf_counter() - start
        self.cache_hits = self._reachable.cache_info().hits
        return result

    def usage(self):
        return dict(tool_calls=self.calls, tool_nodes=self.nodes,
                    tool_cache_hits=self.cache_hits, tool_seconds=self.seconds)
