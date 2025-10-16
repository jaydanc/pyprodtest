def Test(name, desc):
    def wrapper(fn):
        fn._test_meta = {"name": name, "desc": desc}
        return fn
    return wrapper

def Req(*reqs):
    def wrapper(fn):
        fn._requirements = list(reqs)
        return fn
    return wrapper

def Step(*steps):
    def wrapper(fn):
        if not hasattr(fn, "_steps"):
            fn._steps = []
        fn._steps.extend(steps)
        return fn
    return wrapper
