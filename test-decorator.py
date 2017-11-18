"""
Shows how to use the jitcompiler.jit decorator to automatically compile the
function to native code on the first call.
"""

import jitcompiler

print("++ definition of foo")

@jitcompiler.jit
def foo(a, b):
    return a*a - b*b

def test(a, b):
    result = foo(a, b)
    print("foo(%d, %d) => %d" % (a, b, result))
    assert(result == (a*a - b*b))

print("++ testing foo")
test(1, 2)
test(2, 3)
