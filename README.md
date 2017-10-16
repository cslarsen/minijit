Minijit
=======

A naive, educational x86-64 machine code JIT-compiler written in C++ from
scratch.

It doesn't do anything cool except write machine code into a memory region and
then execute it. That's really all you need for a simple example.

Requirements
------------

    * A UNIX system with POSIX functions `mmap`, `mprotect`
    * An x86-64 / amd64 compatible CPU
    * A C++ compiler

I've tested this on Linux and macOS systems.

References
----------

    * Intel assembly manuals:
      https://software.intel.com/en-us/articles/intel-sdm
    * x86 Reference:
      http://ref.x86asm.net/

License
-------

Put in the public domain in 2017 by the author Christian Stigen Larsen
