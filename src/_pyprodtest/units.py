from dataclasses import dataclass

# ======================
# UNIT DEFINITIONS
# ======================

@dataclass(frozen=True)
class Unit:
    name: str
    symbol: str
    scale: float = 1.0  # multiplier to convert to base unit (e.g. mV → 1e-3 V)

    def convert_to(self, value: float, other: "Unit") -> float:
        """Convert `value` in this unit to another unit of same dimension."""
        if self.name != other.name:
            raise ValueError(f"Incompatible units: {self.symbol} -> {other.symbol}")
        return value * (self.scale / other.scale)

    def __str__(self):
        return self.symbol


# Base units
VOLT = Unit("voltage", "V")
AMPERE = Unit("current", "A")
OHM = Unit("resistance", "Ω")
HERTZ = Unit("frequency", "Hz")
SECOND = Unit("time", "s")
DEGREE = Unit("angle", "°")

# Scaled units
MILLIVOLT = Unit("voltage", "mV", 1e-3)
KILOVOLT = Unit("voltage", "kV", 1e3)

MILLIAMP = Unit("current", "mA", 1e-3)
KILOAMP = Unit("current", "kA", 1e3)

MILLISECOND = Unit("time", "ms", 1e-3)
MICROSECOND = Unit("time", "µs", 1e-6)

KILOHERTZ = Unit("frequency", "kHz", 1e3)
MEGAHERTZ = Unit("frequency", "MHz", 1e6)


# ======================
# VALIDATORS
# ======================

def within(min_v, max_v):
    """Check that value lies between min_v and max_v (inclusive)."""
    def _v(value):
        ok = min_v <= value <= max_v
        return ok, None if ok else f"{value} not in range [{min_v}, {max_v}]"
    return _v


def greater_than(threshold):
    """Check that value > threshold."""
    def _v(value):
        ok = value > threshold
        return ok, None if ok else f"{value} ≤ {threshold}"
    return _v


def less_than(threshold):
    """Check that value < threshold."""
    def _v(value):
        ok = value < threshold
        return ok, None if ok else f"{value} ≥ {threshold}"
    return _v


def non_negative(value):
    """Ensure value >= 0."""
    ok = value >= 0
    return ok, None if ok else f"{value} is negative"


def is_close_to(target, tol):
    """Check |value - target| <= tol."""
    def _v(value):
        ok = abs(value - target) <= tol
        return ok, None if ok else f"{value} not within ±{tol} of {target}"
    return _v
