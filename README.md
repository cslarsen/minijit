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

If you want to get serious about this
-------------------------------------

  * Check out a full-blown assembler library for Python:
    https://github.com/Maratyszcza/PeachPy

References
----------

  * Intel assembly manuals:
    https://software.intel.com/en-us/articles/intel-sdm

  * x86 Reference: http://ref.x86asm.net/

License
-------

Put in the public domain in 2017 by the author Christian Stigen Larsen
