MiniJIT
=======

Contains code for the posts

  * Writine a basic x86-64 JIT compiler from scratch in stock Python
    https://csl.name/post/python-jit/

  * JIT compiling a tiny subset of Python to x86-64 from scratch — in Python
    https://csl.name/post/python-compiler/

You need a UNIX/POSIX system and an x86-64 compatible CPU. I've tested this on
Linux and macOS, using Python 2.7 and 3+

The ~500 lines of code relies only on standard Python libraries and contains a
Python bytecode converter, peephole optimizer and x86-64 machine code
assembler. The code is meant to be simple to understand and pedagogical.

Finally, there is a decorator that automatically swaps out Python functions
with native code:

    >>> from jitcompiler import jit, disassemble
    >>> @jit
    ... def foo(a, b): return a + b
    ... 
    --- Installing JIT for <function foo at 0x10bc48c08>
    >>> foo(10, -2)
    --- JIT-compiling <function foo at 0x10bc48c08>
    8
    >>> print(disassemble(foo))
    0x10bb3c000 48 89 fb       mov rbx, rdi
    0x10bb3c003 48 89 f0       mov rax, rsi
    0x10bb3c006 48 01 d8       add rax, rbx
    0x10bb3c009 c3             ret 

How to run tests
----------------

The first one patches up some machine code and runs it at runtime

    $ python mj.py

The second one JIT compiles Python bytecode to machine code at runtime

    $ python tests.py

If you have the `capstone` module installed, it will display an in-memory
disassembly as well.

You can also run the decorator test. It defines a function like this

    import jitcompiler

    #...

    @jitcompiler.jit
    def foo(a, b):
        return a*a - b*b

On the first *call* to `foo`, it will be compiled to native code and swap out
the original Python function. It treats all arguments as signed 64-bit
integers. If you have the Capstone module installed, it will also print a
disassembly. To run:

    $ python test-decorator.py
    Definition point of foo

    Installing JIT for <function foo at 0x1f855f0>

    Calling foo

    JIT-compiling <function foo at 0x1f855f0>
    Installed native code for <function foo at 0x1f855f0>
    Calling function <CFunctionType object at 0x7f867642b600>
    foo(1, 2) => -3
    Calling function <CFunctionType object at 0x7f867642b600>
    foo(2, 3) => -5

    Disassembly of foo

    0x7f86765f9000 48 89 fb       mov rbx, rdi
    0x7f86765f9003 48 89 f8       mov rax, rdi
    0x7f86765f9006 48 0f af c3    imul rax, rbx
    0x7f86765f900a 50             push rax
    0x7f86765f900b 48 89 f3       mov rbx, rsi
    0x7f86765f900e 48 89 f0       mov rax, rsi
    0x7f86765f9011 48 0f af c3    imul rax, rbx
    0x7f86765f9015 48 89 c3       mov rbx, rax
    0x7f86765f9018 58             pop rax
    0x7f86765f9019 48 29 d8       sub rax, rbx
    0x7f86765f901c c3             ret

If you want to get serious about this
-------------------------------------

  * Check out a full-blown assembler library for Python:
    https://github.com/Maratyszcza/PeachPy

References
----------

  * Intel assembly manuals:
    https://software.intel.com/en-us/articles/intel-sdm

  * x86 Reference: http://ref.x86asm.net/

  * Capstone disassembler:
    http://www.capstone-engine.org/lang_python.html

License
-------

Put in the public domain in 2017 by the author Christian Stigen Larsen
