from pyprodtest import step


def test_stacked_step_decorators_accumulate_in_source_order():
    @step("First")
    @step("Second")
    def production_test():
        pass

    assert production_test.test_meta["steps"] == ["First", "Second"]


def test_step_decorator_preserves_multiple_steps():
    @step("First", "Second")
    def production_test():
        pass

    assert production_test.test_meta["steps"] == ["First", "Second"]
