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
_SC_PAGESIZE = 29
MAP_ANONYMOUS = 0x1000
MAP_PRIVATE = 0x0002
PROT_EXEC = 0x04
PROT_NONE = 0x00
PROT_READ = 0x01
PROT_WRITE = 0x02
MAP_FAILED = -1 # voidptr actually

# Load the C standard library
if sys.platform.startswith("darwin"):
    libc = ctypes.cdll.LoadLibrary("libc.dylib")
else:
    libc = ctypes.cdll.LoadLibrary("libc.so")
    warnings.warn("Some enums MAY be wrong on your platform")

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
  # Prologue

  # push rbp
  block[0] = 0x55

  # mov rbp, rsp
  block[1] = 0x48
  block[2] = 0x89
  block[3] = 0xe5

  # put argument onto stack.. :)
  block[4] = 0x89
  block[5] = 0x7d
  block[6] = 0xfc

  # get argument into eax :D mov eax, dword ptr [rbp-0x4]
  block[7] = 0x8b
  block[8] = 0x45
  block[9] = 0xfc

  # mov edx, immediate 32-bit value
  block[10] = 0xba

  # little-endian
  block[11] = (multiplier & 0x000000ff)
  block[12] = (multiplier & 0x0000ff00) >> 8
  block[13] = (multiplier & 0x00ff0000) >> (4*4)
  block[14] = (multiplier & 0xff000000) >> (6*4)

  # imul eax, edx
  block[15] = 0x0f
  block[16] = 0xaf
  block[17] = 0xc2

  # Epilogue: pop rbp
  block[18] = 0x5d

  # retq
  block[19] = 0xc3

  # Make a function out of this

  function = ctypes.CFUNCTYPE(ctypes.c_int)
  function.restype = ctypes.c_int
  return function

def destroy_block(block, size):
    if munmap(block, size) == -1:
        raise RuntimeError(strerror(ctypes.get_errno()))
    del block

def main():
    if len(sys.argv) > 1:
        arg = int(sys.argv[1])
    else:
        arg = 2

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
        print("mul(%d) = %d" % (i, mul(i)))

    print("Deallocating function")
    destroy_block(block, PAGESIZE)
    del block
    del mul

if __name__ == "__main__":
    main()
