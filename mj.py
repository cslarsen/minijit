"""
Provides a way to generate machine code and bind it to callable Python
functions at runtime.

You need a UNIX system with mmap, mprotect and so on. Tested on macOS and
Linux.

See https://csl.name/post/python-jit/ for a write-up on how everything works!

Written by Christian Stigen Larsen
"""

import ctypes
import ctypes.util
import mmap as MMAP
import os
import sys

# Load the C standard library
libc = ctypes.CDLL(ctypes.util.find_library("c"))

# A few constants
MAP_FAILED = -1 # voidptr actually

# Set up strerror
strerror = libc.strerror
strerror.argtypes = [ctypes.c_int]
strerror.restype = ctypes.c_char_p

# Get pagesize
PAGESIZE = os.sysconf(os.sysconf_names["SC_PAGESIZE"])

# 8-bit unsigned pointer type
c_uint8_p = ctypes.POINTER(ctypes.c_uint8)

# Setup mmap
mmap = libc.mmap
mmap.argtypes = [ctypes.c_void_p,
                 ctypes.c_size_t,
                 ctypes.c_int,
                 ctypes.c_int,
                 ctypes.c_int,
                 # Below is actually off_t, which is 64-bit on macOS
                 ctypes.c_int64]
mmap.restype = c_uint8_p

# Setup munmap
munmap = libc.munmap
munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
munmap.restype = ctypes.c_int

# Set mprotect
mprotect = libc.mprotect
mprotect.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
mprotect.restype = ctypes.c_int

def create_block(size):
    """Allocated a block of memory using mmap."""
    ptr = mmap(0, size, MMAP.PROT_WRITE | MMAP.PROT_READ,
            MMAP.MAP_PRIVATE | MMAP.MAP_ANONYMOUS, 0, 0)

    if ptr == MAP_FAILED:
        raise RuntimeError(strerror(ctypes.get_errno()))

    return ptr

def make_executable(block, size):
    """Marks mmap'ed memory block as read-only and executable."""
    if mprotect(block, size, MMAP.PROT_READ | MMAP.PROT_EXEC) != 0:
        raise RuntimeError(strerror(ctypes.get_errno()))

def destroy_block(block, size):
    """Deallocated previously mmapped block."""
    if munmap(block, size) == -1:
        raise RuntimeError(strerror(ctypes.get_errno()))
    del block

def make_multiplier(block, multiplier):
    """JIT-compiles a function that multiplies its RDX argument with an
    unsigned 64-bit constant."""
    if multiplier > (2**64-1) or multiplier < 0:
        raise ValueError("Multiplier does not fit in unsigned 64-bit integer")

    # This function encodes the disassembly of multiply.c, which you can see
    # with the command `make dis`. It may be different on your CPU, so adjust
    # to match.
    #
    #   48 b8 ed ef be ad de    movabs $0xdeadbeefed,%rax
    #   00 00 00
    #   48 0f af c7             imul   %rdi,%rax
    #   c3                      retq

    # Encoding of: movabs <multiplier>, rax
    block[0] = 0x48
    block[1] = 0xb8

    # Little-endian encoding of multiplier
    block[2] = (multiplier & 0x00000000000000ff) >>  0
    block[3] = (multiplier & 0x000000000000ff00) >>  8
    block[4] = (multiplier & 0x0000000000ff0000) >> 16
    block[5] = (multiplier & 0x00000000ff000000) >> 24
    block[6] = (multiplier & 0x000000ff00000000) >> 32
    block[7] = (multiplier & 0x0000ff0000000000) >> 40
    block[8] = (multiplier & 0x00ff000000000000) >> 48
    block[9] = (multiplier & 0xff00000000000000) >> 56

    # Encoding of: imul rdi, rax
    block[10] = 0x48
    block[11] = 0x0f
    block[12] = 0xaf
    block[13] = 0xc7


    # Encoding of: retq
    block[14] = 0xc3

    # Return a ctypes function with the right prototype
    function = ctypes.CFUNCTYPE(ctypes.c_uint64)
    function.restype = ctypes.c_uint64
    return function

def main():
    # Fetch the constant to multiply with on the command line. If not
    # specified, use the default value of 11.
    if len(sys.argv) > 1:
        arg = int(sys.argv[1])
    else:
        arg = 11

    print("Pagesize: %d" % PAGESIZE)

    print("Allocating one page of memory")
    block = create_block(PAGESIZE)

    print("JIT-compiling a native mul-function w/arg %d" % arg)
    function_type = make_multiplier(block, arg)

    print("Making function block executable")
    make_executable(block, PAGESIZE)
    mul = function_type(ctypes.cast(block, ctypes.c_void_p).value)

    print("Testing function")
    for i in range(10):
        expected = i*arg
        actual = mul(i)
        print("%-4s mul(%d) = %d" % ("OK" if actual == expected else "FAIL", i,
            actual))

    print("Deallocating function")
    destroy_block(block, PAGESIZE)

    # Unbind local variables
    del block
    del mul

if __name__ == "__main__":
    main()
