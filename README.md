Minijit
=======

A naive, educational x86-64 machine code JIT-compiler written in C++ from
scratch. Contains code for the blog post at https://csl.name/post/python-jit/

It doesn't do anything cool except write machine code into a memory region and
then execute it. That's really all you need for a simple example.

I also made a version in Python, using only the standard Python library (i.e.,
ctypes).

This is another rite-of-passage project that I just had to do. I only knew
about mprotect, really, and just went from there. I see that this is the way
most people do it. I knew I had to use mmap to be sure to get a page-aligned
block of memory --- malloc cannot guarantee this --- and so far it seems to
work pretty well!

Requirements
------------

  * A UNIX system with POSIX functions `mmap`, `mprotect`
  * An x86-64 / amd64 compatible CPU
  * A C++ compiler

I've tested this on Linux and macOS systems.

How to test
-----------

It currently just JIT-compiles a multiplication function.

So, to JIT-compile a block of code that multiplies with the number 11, do:

    $ make mj
    $ mj 11
    $ ./mj 11
    pagesize 4096
    compiling code w/multiplier 11
    marking as executable
    calling JIT
    OK result 132
    OK call(0) = 0
    OK call(1) = 11
    OK call(2) = 22
    OK call(3) = 33
    OK call(4) = 44
    OK call(5) = 55
    OK call(6) = 66
    OK call(7) = 77
    OK call(8) = 88
    OK call(9) = 99
    done
    $ echo $?
    0

The default value is 2.

You can also run the Python version like so:

    $ python mj.py 10
    Pagesize: 4096
    Allocating one page of memory
    JIT-compiling a native mul-function w/arg 10
    Making function block executable
    Testing function
    mul(0) = 0
    mul(1) = 10
    mul(2) = 20
    mul(3) = 30
    mul(4) = 40
    mul(5) = 50
    mul(6) = 60
    mul(7) = 70
    mul(8) = 80
    mul(9) = 90
    Deallocating function

How to disassemble
------------------

    $ make mj
    $ gdb mj
    (gdb) break testmul
    (gdb) run 11 # create code to multiply with 11
    (gdb) x/20i block
       0x7ffff7ff7000:      push   %rbp
       0x7ffff7ff7001:      mov    %rsp,%rbp
       0x7ffff7ff7004:      mov    %edi,-0x4(%rbp)
       0x7ffff7ff7007:      mov    -0x4(%rbp),%eax
       0x7ffff7ff700a:      mov    $0xb,%edx
       0x7ffff7ff700f:      imul   %edx,%eax
       0x7ffff7ff7012:      pop    %rbp
       0x7ffff7ff7013:      retq

If you want to see the machine code for your own C code, modify `multiply.c`
and run `make dis`.

If you want to get serious about this
-------------------------------------

  * Check out a full-blown assembler library for Python:
    https://github.com/Maratyszcza/PeachPy

References
----------

  * Intel assembly manuals:
    https://software.intel.com/en-us/articles/intel-sdm
  * x86 Reference:
    http://ref.x86asm.net/

License
-------

Put in the public domain in 2017 by the author Christian Stigen Larsen
