"""
Tests for: JIT compiles a tiny subset of Python to x86-64 machine code.

Explanation on https://csl.name/post/python-compiler/

Written by Christian Stigen Larsen
Put in the public domain by the author, 2017
"""

import random
import jitcompiler
import sys

try:
    import capstone
except ImportError:
    pass

good = True

def test_function(original, compiled, tests=10, minval=-999, maxval=999):
    for n in range(tests):
        # Create random arguments
        argcount = jitcompiler.get_codeobj(original).co_argcount
        args = [random.randint(minval, maxval) for x in range(argcount)]

        # Run original and compiled functions
        expected = original(*args)
        actual = compiled(*args)
        ok = (expected == actual)

        global good
        if not ok:
            good = False

        print("  %-4s %-16s => %10d, expected %10d" % (
            "OK" if ok else "FAIL",
            "(%s)" % ", ".join("%4d" % d for d in args),
            actual,
            expected))

def test(function):
    print("")
    print("=== Function %s ===" % function.__name__)
    print("")

    native, asm = jitcompiler.compile_native(function)

    try:
        print("Native code:")
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        for i in md.disasm(asm.raw, asm.address):
            print("  0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))
            if i.mnemonic == "ret":
                break
        print("")
    except NameError:
        pass

    test_function(function, native)

if __name__ == "__main__":
    def example0(n):
        return n

    def example1(n):
        return n*101

    def example2(a, b):
        return a*a + b*b

    def example3(a):
        b = a*101
        return b + a + 2

    def example4(a, b, c):
        return a*a + 2*a*b + c

    def example5(n):
        n -= 10
        return n

    def example6(a, b):
        return a*a - b*b

    def example7(a, b, c):
        return (a+c)*b - a*a*(a-c-b)-b*2+(c*(2+3*a*b-c*a)-3*c)

    def foo(a, b):
        return a*a - b*b

    test(example0)
    test(example1)
    test(example2)
    test(example3)
    test(example4)
    test(example5)
    test(example6)
    #test(example7) # works, but produces too much output
    test(foo)

    if not good:
        print("")
        print("One or more errors occurred.")
        sys.exit(1)
