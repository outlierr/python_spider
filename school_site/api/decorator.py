from functools import wraps


def wrapper(func):
    @wraps(func)
    def wrapper_func():
        print("pre wrapper")
        func()
        print("post wrapper")
    return wrapper_func


@wrapper
def f():
    print('do something')


f()