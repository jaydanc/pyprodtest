"""
Data structure to hold test metadata.
"""
class TestRecord:
    """
    Represents a test record
    """
    def __init__(self, name, description, requirements, steps):
        self.name = name
        self.description = description
        self.requirements = requirements
        self.steps = steps

    def __repr__(self):
        return (
            f"TestRecord("
            f"name={self.name}, "
            f"description={self.description}, "
            f"requirements={self.requirements}, "
            f"steps={self.steps})"
        )
