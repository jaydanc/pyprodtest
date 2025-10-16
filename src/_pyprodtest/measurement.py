class Measurement:
    def __init__(self, name, value, unit, validator=None):
        self.name = name or "unnamed"
        self.value = value
        self.unit = unit
        self.validator = validator
        self.valid = None
        self.reason = None

    def validate(self):
        if not self.validator:
            self.valid = True
            return
        try:
            ok, msg = self.validator(self.value)
            self.valid = bool(ok)
            self.reason = msg if not ok else None
        except Exception as e:
            self.valid = False
            self.reason = f"Validator error: {e}"

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "valid": self.valid,
            "reason": self.reason,
        }