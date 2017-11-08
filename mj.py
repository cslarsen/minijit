"""
A rudimentary x86-64 JIT-compiler using only standard Python libraries.

Meaning, you need to be on a UNIX system with mmap, mprotect and so on.

Yes, this *actually* works! I've only tested on macOS so far, but it should be
very simple to get it to work on other systems. There isn't much error checking
going on, so be prepared for weird crashes!

Written by Christian Stigen
"""

import ctypes
import sys
import warnings

# A few system enums.
# NOTE: These *may* be different on various platforms. This is for macOS.

# Load the C standard library
if sys.platform.startswith("darwin"):
    libc = ctypes.cdll.LoadLibrary("libc.dylib")
    _SC_PAGESIZE = 29
    MAP_ANONYMOUS = 0x1000
    MAP_PRIVATE = 0x0002
    PROT_EXEC = 0x04
    PROT_NONE = 0x00
    PROT_READ = 0x01
    PROT_WRITE = 0x02
    MAP_FAILED = -1 # voidptr actually
elif sys.platform.startswith("linux"):
    libc = ctypes.cdll.LoadLibrary("libc.so.6")
    _SC_PAGESIZE = 30
    MAP_ANONYMOUS = 0x20
    MAP_PRIVATE = 0x0002
    PROT_EXEC = 0x04
    PROT_NONE = 0x00
    PROT_READ = 0x01
    PROT_WRITE = 0x02
    MAP_FAILED = -1 # voidptr actually
else:
    raise RuntimeError("Unsupported platform: %s" % sys.platform)

strerror = libc.strerror
strerror.argtypes = [ctypes.c_int]
strerror.restype = ctypes.c_char_p

# Set up sysconf
sysconf = libc.sysconf
sysconf.argtypes = [ctypes.c_int]
sysconf.restype = ctypes.c_long

# Get pagesize
PAGESIZE = sysconf(_SC_PAGESIZE)

# 8-bit unsigned pointer type
c_uint8_p = ctypes.POINTER(ctypes.c_uint8)

mmap = libc.mmap
mmap.argtypes = [ctypes.c_void_p,
                 ctypes.c_size_t,
                 ctypes.c_int,
                 ctypes.c_int,
                 ctypes.c_int,
                 # Below is actually off_t, which is 64-bit on macOS
                 ctypes.c_int64]
mmap.restype = c_uint8_p

munmap = libc.munmap
munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
munmap.restype = ctypes.c_int

mprotect = libc.mprotect
mprotect.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
mprotect.restype = ctypes.c_int

def create_block(size):
    ptr = mmap(0, size,
            PROT_WRITE | PROT_READ,
            MAP_PRIVATE | MAP_ANONYMOUS, 0, 0)
    if ptr == MAP_FAILED:
        raise RuntimeError(strerror(ctypes.get_errno()))

    return ptr

def make_executable(block, size):
    if mprotect(block, size, PROT_READ | PROT_EXEC) != 0:
        raise RuntimeError(strerror(ctypes.get_errno()))

def make_multiplier(block, multiplier):
    if multiplier > (2**64-1):
        raise ValueError("Multiplier does not fit in unsigned 64-bit integer")

    # This function encodes the disassembly of multiply.c, which you can see
    # with the command `make dis`. It may be different on your CPU, so adjust
    # to match.
    #
    #   48 ba ed ef be ad de    movabs $0xdeadbeefed,%rdx
    #   00 00 00
    #   48 89 f8                mov    %rdi,%rax
    #   48 0f af c2             imul   %rdx,%rax
    #   c3                      retq

    # Encoding of: movabs <multiplier>, rdx
    block[0] = 0x48
    block[1] = 0xba

    # Little-endian encoding of multiplier
    block[2] = (multiplier & 0x00000000000000ff) >>  0
    block[3] = (multiplier & 0x000000000000ff00) >>  8
    block[4] = (multiplier & 0x0000000000ff0000) >> 16
    block[5] = (multiplier & 0x00000000ff000000) >> 24
    block[6] = (multiplier & 0x000000ff00000000) >> 32
    block[7] = (multiplier & 0x0000ff0000000000) >> 40
    block[8] = (multiplier & 0x00ff000000000000) >> 48
    block[9] = (multiplier & 0xff00000000000000) >> 56

    # Encoding of: mov rdi, rax
    block[10] = 0x48
    block[11] = 0x89
    block[12] = 0xf8

    # Encoding of: imul rdx, rax
    block[13] = 0x48
    block[14] = 0x0f
    block[15] = 0xaf
    block[16] = 0xc2

    # Encoding of: retq
    block[17] = 0xc3

    # Return a ctypes function with the right prototype
    function = ctypes.CFUNCTYPE(ctypes.c_int64)
    function.restype = ctypes.c_int64
    return function

def destroy_block(block, size):
    if munmap(block, size) == -1:
        raise RuntimeError(strerror(ctypes.get_errno()))
    del block

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
    del block
    del mul

if __name__ == "__main__":
    main()
