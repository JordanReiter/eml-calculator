"""The single complex-number evaluation pass and its result types.

Children are evaluated before parents, exactly once.  Evaluation returns a new
``EMLTree`` carrying a side table of results; it never mutates its input.
Failures are data (``overflow`` / ``undefined``), never exceptions or silent
``nan`` / ``inf``.

The compiler's construction chain uses the extended-real identities
``log(0) = -inf``, ``log(-inf) = +inf + i*pi`` and ``exp(-inf) = 0``.  Python's
``cmath`` traps these, so the evaluator carries an explicit internal value that
is either finite or an infinity with a phase.  These are *intermediate* states
only: a root that is still non-finite is reported as an ``overflow`` failure.
A domain check on source-derived logarithms still reports a zero right child as
``undefined``.  Log construction nodes carry provenance so the single pass can
apply the extended-log identity where the ordinary ``eml`` composition cannot
express it.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from fractions import Fraction

from .constants import (
    IMAG_ABS_FLOOR,
    MAX_FINITE_MAGNITUDE,
    MAX_NODE_EVAL_DEPTH,
    REL_TOL_EPSILON,
)
from .parser import SourceNode

__all__ = [
    "EvaluationResult",
    "FailureSummary",
    "evaluate_source",
    "evaluate_tree",
    "format_complex",
    "build_failure_summary",
    "root_value",
]

POSITIVE_INFINITY = complex(math.inf, 0)
NEGATIVE_INFINITY = complex(-math.inf, 0)


@dataclass(frozen=True)
class _Extended:
    """A finite complex value or an infinity with a direction/phase.

    ``complex_infinity.phase`` is the angle of an infinite magnitude; the
    evaluator serializes it in the imaginary component of a non-finite complex
    value.  This lets ``log(-inf) = +inf + i*pi`` and ``exp(+inf + i*pi)`` behave
    consistently inside the nested construction chain.
    """

    kind: str  # finite | positive_infinity | negative_infinity | complex_infinity
    value: complex = 0j
    phase: float = 0.0


_POS_INF = _Extended("positive_infinity")
_NEG_INF = _Extended("negative_infinity")


def _normalize_phase(phase: float) -> float:
    """Normalize an angle to ``(-pi, pi]`` so infinity directions compare stably."""
    normalized = math.remainder(phase, 2 * math.pi)
    if normalized <= -math.pi:
        normalized += 2 * math.pi
    return normalized


def _infinity(phase: float) -> _Extended:
    normalized = _normalize_phase(phase)
    if normalized == 0.0:
        return _POS_INF
    if abs(abs(normalized) - math.pi) <= REL_TOL_EPSILON:
        return _NEG_INF
    return _Extended("complex_infinity", 0j, normalized)


def _finite(value: complex) -> _Extended:
    return _Extended("finite", value)


@dataclass(frozen=True)
class EvaluationResult:
    """Outcome for one tree node (or for the source expression)."""

    status: str  # "ok" | "failed"
    value: complex | None = None
    display_value: str = ""
    value_display: str = ""
    display_as_real: bool = False
    failure_reason: str | None = None  # "overflow" | "undefined" | None
    attributed_node: int | None = None
    message: str = ""
    visible_failure_marker: str | None = None


@dataclass(frozen=True)
class FailureSummary:
    """Complete, node-attributed list of failures in an evaluated tree."""

    entries: tuple[tuple[int, str, str], ...] = ()
    source_value_available: bool = True


def format_complex(value: complex) -> str:
    """Display as real exactly under the shared ``IMAG_ABS_FLOOR``/ε rule."""
    if abs(value.imag) <= max(IMAG_ABS_FLOOR, REL_TOL_EPSILON * max(1.0, abs(value.real))):
        return _format_number(value.real)
    sign = "+" if value.imag >= 0 else "-"
    return f"{_format_number(value.real)}{sign}{_format_number(abs(value.imag))}i"


def _format_number(number: float) -> str:
    return format(number, ".12g")


def _is_finite(value: complex) -> bool:
    return math.isfinite(value.real) and math.isfinite(value.imag)


def _within_guard(value: complex) -> bool:
    return abs(value.real) <= MAX_FINITE_MAGNITUDE and abs(value.imag) <= MAX_FINITE_MAGNITUDE


def _as_extended(value: complex | None) -> _Extended:
    if value is None:
        return _NEG_INF  # never reached: failures are checked before this call
    if not math.isfinite(value.real):
        if math.isinf(value.imag) or math.isnan(value.imag):
            return _POS_INF
        if value.real > 0:
            # A non-zero imaginary component is an infinite magnitude's phase;
            # do not collapse +inf + i*pi back to the negative real infinity.
            return (
                _POS_INF
                if value.imag == 0
                else _Extended("complex_infinity", 0j, _normalize_phase(value.imag))
            )
        if value.imag == 0:
            return _NEG_INF
        return _Extended("complex_infinity", 0j, _normalize_phase(value.imag + math.pi))
    return _finite(value)


def _from_extended(value: _Extended) -> complex:
    if value.kind == "positive_infinity":
        return POSITIVE_INFINITY
    if value.kind == "negative_infinity":
        return NEGATIVE_INFINITY
    if value.kind == "complex_infinity":
        return complex(math.inf, value.phase)
    return value.value


def _infinity_phase(value: _Extended) -> float:
    if value.kind == "positive_infinity":
        return 0.0
    if value.kind == "negative_infinity":
        return math.pi
    return value.phase


def _negate_infinity(value: _Extended) -> _Extended:
    return _infinity(_infinity_phase(value) + math.pi)


def _extended_exp(value: _Extended) -> _Extended:
    if value.kind == "negative_infinity":
        return _finite(0j)
    if value.kind in {"positive_infinity", "complex_infinity"}:
        return _infinity(_infinity_phase(value))
    try:
        return _finite(cmath.exp(value.value))
    except OverflowError:
        return _infinity(value.value.imag)


def _extended_log(value: _Extended) -> _Extended | None:
    if value.kind == "negative_infinity":
        # log(-inf) is +inf + i*pi, which exp() must turn back into -inf.
        return _Extended("complex_infinity", 0j, math.pi)
    if value.kind == "positive_infinity":
        return _POS_INF
    if value.kind == "complex_infinity":
        return _POS_INF
    if value.value == 0:
        return _NEG_INF
    try:
        return _finite(cmath.log(value.value))
    except ValueError:
        return None


def _extended_subtract(left: _Extended, right: _Extended) -> _Extended | None:
    if left.kind == "finite" and right.kind == "finite":
        return _finite(left.value - right.value)
    if left.kind == "finite":
        return _negate_infinity(right)
    if right.kind == "finite":
        return left
    return None  # infinity - infinity is indeterminate here


def _intermediate_display(value: complex) -> str:
    if value.real > 0:
        if value.imag == 0:
            return "(+∞ intermediate)"
        return f"(∞ at phase {_format_number(value.imag)} intermediate)"
    if value.imag == 0:
        return "(−∞ intermediate)"
    return f"(∞ at phase {_format_number(value.imag)} intermediate)"


def _ok_result(value: complex, node_id: int | None = None) -> EvaluationResult:
    if not _is_finite(value):
        display = _intermediate_display(value)
        return EvaluationResult(
            status="ok",
            value=value,
            display_value=display,
            value_display=display,
            attributed_node=node_id,
        )
    display = format_complex(value)
    return EvaluationResult(
        status="ok",
        value=value,
        display_value=display,
        value_display=display,
        display_as_real=abs(value.imag)
        <= max(IMAG_ABS_FLOOR, REL_TOL_EPSILON * max(1.0, abs(value.real))),
        attributed_node=node_id,
    )


def _failed_result(reason: str, message: str, node_id: int) -> EvaluationResult:
    return EvaluationResult(
        status="failed",
        display_value=message,
        value_display=message,
        failure_reason=reason,
        attributed_node=node_id,
        message=message,
        visible_failure_marker=reason,
    )


def evaluate_source(source: SourceNode) -> EvaluationResult:
    """Evaluate the *source* expression once, for equivalence comparison only."""
    try:
        value = _evaluate_source_node(source, 0)
    except (ArithmeticError, ValueError) as exc:
        reason = "overflow" if isinstance(exc, OverflowError) else "undefined"
        return _failed_result(reason, f"{reason}: {exc}", -1)
    if value is None:
        return _failed_result(
            "undefined", "undefined: source expression has no complex value", -1
        )
    if not _is_finite(value) or not _within_guard(value):
        return _failed_result("overflow", "overflow: source value is not finite", -1)
    return _ok_result(value)


def _evaluate_source_node(node: SourceNode, depth: int) -> complex | None:
    if depth > MAX_NODE_EVAL_DEPTH:
        raise OverflowError("evaluation depth limit exceeded")
    if node.kind == "group":
        return _evaluate_source_node(node.children[0], depth + 1)
    if node.kind == "literal":
        assert isinstance(node.value, Fraction)
        return complex(float(node.value))
    if node.kind == "named_constant":
        return complex(cmath.pi if node.value == "pi" else cmath.e)
    if node.kind == "unary_minus":
        value = _evaluate_source_node(node.children[0], depth + 1)
        if value is None:
            return None
        # Preserve +0 imaginary on the negative real axis.  Python's complex
        # negation produces -0j there, which flips cmath.log's branch sign.
        return complex(-value.real, -value.imag if value.imag else 0.0)

    left = _evaluate_source_node(node.children[0], depth + 1)
    if node.kind == "function_call":
        return None if left is None else _apply_source_function(node.value, left)

    right = _evaluate_source_node(node.children[1], depth + 1)
    if left is None or right is None:
        return None
    assert isinstance(node.value, str)
    if node.value == "+":
        return left + right
    if node.value == "-":
        return left - right
    if node.value == "*":
        return left * right
    if node.value == "/":
        return None if right == 0 else left / right
    if node.value == "^":
        if right == 0:
            return complex(1, 0)
        if left == 0:
            return None
        try:
            return cmath.exp(right * cmath.log(left))
        except (OverflowError, ValueError, ZeroDivisionError):
            return None
    raise ValueError(f"unsupported source operator '{node.value}'")


def _apply_source_function(name: str, value: complex) -> complex | None:
    if name == "ln":
        return None if value == 0 else cmath.log(value)
    functions = {
        "exp": cmath.exp,
        "sqrt": cmath.sqrt,
        "sin": cmath.sin,
        "cos": cmath.cos,
        "tan": cmath.tan,
    }
    try:
        return functions[name](value)
    except (OverflowError, ValueError, ZeroDivisionError):
        return None


def evaluate_tree(tree):
    """Evaluate every node once, children first, returning a *new* tree."""
    from .rewrite import EMLTree  # local import: evaluate defines the shared types

    evaluations: dict[int, EvaluationResult] = {}
    stack = [(tree.root, False, 0)]
    while stack:
        node, expanded, depth = stack.pop()
        if node.is_leaf:
            evaluations[node.id] = _ok_result(complex(1, 0), node.id)
            continue
        if not expanded:
            if depth > MAX_NODE_EVAL_DEPTH:
                evaluations[node.id] = _failed_result(
                    "overflow", "overflow: evaluation depth limit exceeded", node.id
                )
                continue
            stack.append((node, True, depth + 1))
            stack.append((node.right, False, depth + 1))
            stack.append((node.left, False, depth + 1))
            continue

        left = evaluations[node.left.id]
        right = evaluations[node.right.id]
        evaluations[node.id] = _evaluate_eml_node(
            node,
            left,
            right,
            tree.zero_check_node_ids,
            tree.log_argument_node_ids,
            evaluations,
        )

    root = evaluations[tree.root.id]
    if root.status == "ok" and root.value is not None and not _is_finite(root.value):
        evaluations[tree.root.id] = _failed_result(
            "overflow", "overflow: root value is not finite", tree.root.id
        )

    return EMLTree(
        root=tree.root,
        node_count=tree.node_count,
        source_text=tree.source_text,
        evaluations=evaluations,
        zero_check_node_ids=tree.zero_check_node_ids,
        log_argument_node_ids=tree.log_argument_node_ids,
    )


def _evaluate_eml_node(
    node,
    left: EvaluationResult,
    right: EvaluationResult,
    zero_check_ids: frozenset[int],
    log_argument_ids: dict[int, int],
    evaluations: dict[int, EvaluationResult],
) -> EvaluationResult:
    if left.status == "failed" or right.status == "failed":
        return _failed_result("undefined", "undefined: ancestor of a failed node", node.id)
    assert left.value is not None and right.value is not None

    if right.value == 0 and node.id in zero_check_ids:
        return _failed_result("undefined", "undefined: right child evaluates to zero", node.id)

    argument_id = log_argument_ids.get(node.id)
    if argument_id is not None:
        argument = evaluations.get(argument_id)
        if (
            argument is not None
            and argument.status == "ok"
            and argument.value is not None
            and not _is_finite(argument.value)
        ):
            extended = _extended_log(_as_extended(argument.value))
            if extended is None:
                return _failed_result("undefined", "undefined: log has no finite value", node.id)
            value = _from_extended(extended)
            if extended.kind == "finite" and not _within_guard(value):
                return _failed_result("overflow", "overflow: non-finite result", node.id)
            return _ok_result(value, node.id)

    exponent = _extended_exp(_as_extended(left.value))
    logarithm = _extended_log(_as_extended(right.value))
    if logarithm is None:
        return _failed_result("undefined", "undefined: log has no finite value", node.id)
    result = _extended_subtract(exponent, logarithm)
    if result is None:
        return _failed_result("overflow", "overflow: indeterminate extended result", node.id)
    value = _from_extended(result)
    if result.kind == "finite" and not _within_guard(value):
        return _failed_result("overflow", "overflow: non-finite result", node.id)
    return _ok_result(value, node.id)


def build_failure_summary(tree, *, source_value_available: bool = True) -> FailureSummary:
    entries = tuple(
        (node_id, result.failure_reason or "undefined", result.message)
        for node_id, result in sorted(tree.evaluations.items())
        if result.status == "failed"
    )
    return FailureSummary(entries=entries, source_value_available=source_value_available)


def root_value(tree) -> EvaluationResult | None:
    return tree.evaluations.get(tree.root.id)
