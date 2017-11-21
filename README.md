MiniJIT
=======

Contains code for the posts

  * Writine a basic x86-64 JIT compiler from scratch in stock Python
    https://csl.name/post/python-jit/

  * JIT compiling a tiny subset of Python to x86-64 from scratch — in Python
    https://csl.name/post/python-compiler/

You need a UNIX/POSIX system and an x86-64 compatible CPU. I've tested this on
Linux and macOS, using Python 2.7 and 3+

How to run
----------

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

    Installing JIT for <function foo at 0x7ff583c905f0>

    Calling foo

    JIT-compiling <function foo at 0x7ff583c905f0>
    Installed native code for <function foo at 0x7ff583c905f0>
    Calling function <CFunctionType object at 0x7ff583cde600>
    foo(1, 2) => -3
    Calling function <CFunctionType object at 0x7ff583cde600>
    foo(2, 3) => -5

    Disassembly of foo

    0x7ff583e6d000 48 89 fb       mov rbx, rdi
    0x7ff583e6d003 48 89 f8       mov rax, rdi
    0x7ff583e6d006 48 f af c3     imul rax, rbx
    0x7ff583e6d00a 50             push rax
    0x7ff583e6d00b 48 89 f3       mov rbx, rsi
    0x7ff583e6d00e 48 89 f0       mov rax, rsi
    0x7ff583e6d011 48 f af c3     imul rax, rbx
    0x7ff583e6d015 48 89 c3       mov rbx, rax
    0x7ff583e6d018 58             pop rax
    0x7ff583e6d019 48 29 d8       sub rax, rbx
    0x7ff583e6d01c c3             ret

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
