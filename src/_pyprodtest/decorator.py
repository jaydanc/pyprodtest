"""
Additional decorators for PyProdTest tests.
These decorators add metadata to test functions and are optional.
"""

def info(name, desc):
    """
    Adds name and description metadata to a test function.
    """
    def wrapper(fn):
        fn.test_meta = getattr(fn, "test_meta", {})
        fn.test_meta["name"] = name
        fn.test_meta["desc"] = desc
        return fn
    return wrapper

def req(*reqs):
    """
    Adds requirement IDs to the metadata.
    """
    def wrapper(fn):
        fn.test_meta = getattr(fn, "test_meta", {})
        fn.test_meta["requirements"] = list(reqs)
        return fn
    return wrapper

def step(*steps):
    """
    Adds step metadata to the metadata
    """
    def wrapper(fn):
        fn.test_meta = getattr(fn, "test_meta", {})
        if not hasattr(fn.test_meta, "steps"):
            fn.test_meta["steps"] = []
        fn.test_meta["steps"].extend(steps)
        return fn
    return wrapper
