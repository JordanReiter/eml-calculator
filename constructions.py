"""Authoritative table of ``eml`` constructions.

Every formula below is a direct, standard-library port of the plain-function
chain in ``EML_toolkit/EmL_compiler/eml_compiler_v4.py`` from
``VA00/SymbolicRegressionPackage`` (MIT, DOI 10.5281/zenodo.19183008), verified
against the Supplementary Information of arXiv:2603.21852v2.  No other module
may re-derive an ``eml`` construction; call these functions instead.

The upstream compiler emits strings.  Here the same functions emit a tiny
immutable ``EMLExpr`` tree so callers can compose them without parsing text.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "EMLExpr",
    "ONE",
    "eml",
    "exp",
    "log",
    "zero",
    "sub",
    "neg",
    "add",
    "inv",
    "mul",
    "div",
    "power",
    "integer",
    "rational",
    "const_e",
    "const_i",
    "const_pi",
    "sqrt",
    "sin",
    "cos",
    "tan",
]


@dataclass(frozen=True)
class EMLExpr:
    """A symbolic EML expression: ``ONE`` for ``1`` or ``eml(left, right)``.

    ``zero_check`` marks a node whose *right* child is a source-derived value
    that must be non-zero.  It is the rewrite-time provenance the evaluator
    uses to distinguish a genuine source domain error (``1/0``) from the
    internal ``log(0) = -inf`` identity the construction chain relies on.

    ``log_argument`` marks the root of a ``log`` construction.  The evaluator
    needs this provenance only when the argument is non-finite: the ordinary
    ``eml`` chain cannot express ``log(-inf) = +inf + i*pi`` by composition.
    """

    left: EMLExpr | None = None
    right: EMLExpr | None = None
    zero_check: bool = False
    log_argument: EMLExpr | None = None

    @property
    def is_one(self) -> bool:
        return self.left is None and self.right is None


ONE = EMLExpr()


def eml(
    left: EMLExpr,
    right: EMLExpr,
    *,
    zero_check: bool = False,
    log_argument: EMLExpr | None = None,
) -> EMLExpr:
    """The primitive itself: ``eml(x, y) = exp(x) - log(y)``."""
    return EMLExpr(left, right, zero_check, log_argument)


# ---- Core construction chain (ported one-for-one from the compiler) --------


def exp(z: EMLExpr) -> EMLExpr:
    """``exp(z) = eml(z, 1)``."""
    return eml(z, ONE)


def log(z: EMLExpr, *, zero_check: bool = False) -> EMLExpr:
    """``log(z) = eml(1, eml(eml(1, z), 1))``.

    A source-derived ``log`` checks the inner ``eml(1, z)`` node, whose right
    child is ``z`` itself.  Internal ``log`` calls use extended-real semantics.
    """
    return eml(ONE, eml(eml(ONE, z, zero_check=zero_check), ONE), log_argument=z)


def zero() -> EMLExpr:
    """``0 = log(1)``."""
    return log(ONE)


def sub(a: EMLExpr, b: EMLExpr) -> EMLExpr:
    """``a - b = eml(log(a), exp(b))``."""
    return eml(log(a), exp(b))


def neg(z: EMLExpr) -> EMLExpr:
    """``-z = 0 - z``."""
    return sub(zero(), z)


def add(a: EMLExpr, b: EMLExpr) -> EMLExpr:
    """``a + b = a - (-b)``."""
    return sub(a, neg(b))


def inv(z: EMLExpr, *, zero_check: bool = False) -> EMLExpr:
    """``1/z = exp(-log(z))``."""
    return exp(neg(log(z, zero_check=zero_check)))


def mul(a: EMLExpr, b: EMLExpr) -> EMLExpr:
    """``a*b = exp(log(a) + log(b))``."""
    return exp(add(log(a), log(b)))


def div(a: EMLExpr, b: EMLExpr, *, zero_check: bool = False) -> EMLExpr:
    """``a/b = a * (1/b)``."""
    return mul(a, inv(b, zero_check=zero_check))


def power(a: EMLExpr, b: EMLExpr, *, zero_check: bool = False) -> EMLExpr:
    """``a^b = exp(b * log(a))``."""
    return exp(mul(b, log(a, zero_check=zero_check)))


# ---- Literals and constants (same doubling/rational scheme as upstream) ----


def integer(n: int) -> EMLExpr:
    """Build a non-negative integer by repeated doubling, from ``1`` leaves."""
    if n < 0:
        return neg(integer(-n))
    if n == 0:
        return zero()
    if n == 1:
        return ONE
    acc: EMLExpr | None = None
    term = ONE
    remaining = n
    while remaining:
        if remaining & 1:
            acc = term if acc is None else add(acc, term)
        remaining >>= 1
        if remaining:
            term = add(term, term)
    assert acc is not None
    return acc


def rational(p: int, q: int) -> EMLExpr:
    """Build ``p/q`` from integer constructions."""
    if q == 1:
        return integer(p)
    if q <= 0:
        raise ValueError("rational denominator must be positive")
    value = mul(integer(abs(p)), inv(integer(q)))
    return value if p >= 0 else neg(value)


def const_e() -> EMLExpr:
    """``e = exp(1) = eml(1, 1)``."""
    return exp(ONE)


def const_i() -> EMLExpr:
    """``i = -exp(log(-1)/2)``.

    The leading minus is the compiler's documented hand correction for the
    branch jump on the negative real axis.  Under CPython's principal ``log``
    this evaluates to approximately ``-i`` here, while ``const_pi()`` still
    evaluates to approximately ``+pi`` because both factors pick up the same
    sign.  The deviation is recorded in ``decisions.md``.
    """
    return neg(exp(div(log(neg(ONE)), integer(2))))


def const_pi() -> EMLExpr:
    """``pi = i * log(-1)``."""
    return mul(const_i(), log(neg(ONE)))


def sqrt(z: EMLExpr, *, zero_check: bool = False) -> EMLExpr:
    """``sqrt(z) = z^(1/2)``."""
    return power(z, rational(1, 2), zero_check=zero_check)


# ---- Trigonometric functions, composed only from the chain above -----------


def _imes(z: EMLExpr) -> EMLExpr:
    return mul(const_i(), z)


def sin(z: EMLExpr) -> EMLExpr:
    """``sin(z) = (exp(iz) - exp(-iz)) / (2i)``."""
    iz = _imes(z)
    return div(sub(exp(iz), exp(neg(iz))), mul(const_i(), integer(2)))


def cos(z: EMLExpr) -> EMLExpr:
    """``cos(z) = (exp(iz) + exp(-iz)) / 2``."""
    iz = _imes(z)
    return div(add(exp(iz), exp(neg(iz))), integer(2))


def tan(z: EMLExpr) -> EMLExpr:
    """``tan(z) = sin(z) / cos(z)``."""
    return div(sin(z), cos(z))
