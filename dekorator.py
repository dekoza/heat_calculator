def debug(f):
    def opakowanie(*args, **kwargs):
        print(f"Mam takie parametry: {args} {kwargs}")
        return f(*args, **kwargs)
    return opakowanie


@debug
def suma(a, b):
    return a+b
