"""
JIT compiles a tiny subset of Python to x86-64 machine code.
Only relies on stock Python.

Explanation on https://csl.name/post/python-compiler/

Tested on Python 2.7, 3.4 and 3.6.

Written by Christian Stigen Larsen
Put in the public domain by the author, 2017
"""

import ctypes
import dis
import mj
import sys

# Used for compatibility with Python 2.7 and 3+
PRE36 = sys.version_info[:2] < (3, 6)

def get_codeobj(function):
    if hasattr(function, "func_code"):
        return function.func_code
    else:
        return function.__code__

class Assembler(object):
    def __init__(self, size):
        """An x86-64 assembler."""
        self.block = mj.create_block(size)
        self.index = 0
        self.size = size

    @property
    def raw(self):
        """Returns machine code as a raw string."""
        if sys.version_info.major == 2:
            return "".join(chr(x) for x in self.block[:self.index])
        else:
            return bytes(self.block[:self.index])

    @property
    def address(self):
        """Returns address of block in memory."""
        return ctypes.cast(self.block, ctypes.c_void_p).value

    def little_endian(self, n):
        """Converts 64-bit number to little-endian format."""
        return [(n & (0xff << i*2)) >> i*8 for i in range(8)]

    def registers(self, a, b=None):
        """Encodes one or two registers for machine code instructions."""
        order = ("rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi")
        enc = order.index(a)
        if b is not None:
            enc = enc << 3 | order.index(b)
        return enc

    def emit(self, *args):
        """Writes machine code to memory block."""
        for code in args:
            self.block[self.index] = code
            self.index += 1

    def ret(self, a, b):
        self.emit(0xc3)

    def push(self, a, _):
        self.emit(0x50 | self.registers(a))

    def pop(self, a, _):
        self.emit(0x58 | self.registers(a))

    def imul(self, a, b):
        self.emit(0x48, 0x0f, 0xaf, 0xc0 | self.registers(a, b))

    def add(self, a, b):
        self.emit(0x48, 0x01, 0xc0 | self.registers(b, a))

    def sub(self, a, b):
        self.emit(0x48, 0x29, 0xc0 | self.registers(b, a))

    def neg(self, a, _):
        self.emit(0x48, 0xf7, 0xd8 | self.register(a))

    def mov(self, a, b):
        self.emit(0x48, 0x89, 0xc0 | self.registers(b, a))

    def immediate(self, a, number):
        self.emit(0x48, 0xb8 | self.registers(a), *self.little_endian(number))


class Compiler(object):
    """Compiles Python bytecode to intermediate representation (IR)."""
    def __init__(self, bytecode, constants):
        self.bytecode = bytecode
        self.constants = constants
        self.index = 0

    def fetch(self):
        byte = self.bytecode[self.index]
        self.index += 1
        return byte

    def decode(self):
        opcode = self.fetch()
        opname = dis.opname[opcode]

        if opname.startswith(("UNARY", "BINARY", "INPLACE", "RETURN")):
            argument = None
            if not PRE36:
                self.fetch()
        else:
            argument = self.fetch()
            if PRE36:
                argument |= self.fetch() << 8

        return opname, argument

    def variable(self, number):
        # AMD64 argument passing order for our purposes.
        order = ("rdi", "rsi", "rdx", "rcx")
        return order[number]

    def compile(self):
        while self.index < len(self.bytecode):
            op, arg = self.decode()

            if op == "LOAD_FAST":
                yield "push", self.variable(arg), None

            elif op == "STORE_FAST":
                yield "pop", "rax", None
                yield "mov", self.variable(arg), "rax"

            elif op == "LOAD_CONST":
                yield "immediate", "rax", self.constants[arg]
                yield "push", "rax", None

            elif op == "BINARY_MULTIPLY":
                yield "pop", "rax", None
                yield "pop", "rbx", None
                yield "imul", "rax", "rbx"
                yield "push", "rax", None

            elif op in ("BINARY_ADD", "INPLACE_ADD"):
                yield "pop", "rax", None
                yield "pop", "rbx", None
                yield "add", "rax", "rbx"
                yield "push", "rax", None

            elif op in ("BINARY_SUBTRACT", "INPLACE_SUBTRACT"):
                yield "pop", "rbx", None
                yield "pop", "rax", None
                yield "sub", "rax", "rbx"
                yield "push", "rax", None

            elif op == "UNARY_NEGATIVE":
                yield "pop", "rax", None
                yield "neg", "rax", None
                yield "push", "rax", None

            elif op == "RETURN_VALUE":
                yield "pop", "rax", None
                yield "ret", None, None
            else:
                raise NotImplementedError(op)

def optimize(ir):
    """Performs peephole optimizations on the IR."""
    def fetch(n):
        if n < len(ir):
            return ir[n]
        else:
            return None, None, None

    index = 0
    while index < len(ir):
        op1, a1, b1 = fetch(index)
        op2, a2, b2 = fetch(index + 1)
        op3, a3, b3 = fetch(index + 2)
        op4, a4, b4 = fetch(index + 3)

        # Remove nonsensical moves
        if op1 == "mov" and a1 == b1:
            index += 1
            continue

        # Translate
        #    mov rsi, rax
        #    mov rbx, rsi
        # to mov rbx, rax
        if op1 == op2 == "mov" and a1 == b2:
            index += 2
            yield "mov", a2, b1
            continue

        # Short-circuit push x/pop y
        if op1 == "push" and op2 == "pop":
            index += 2
            yield "mov", a2, a1
            continue

        # Same as above, but with an in-between instruction
        if op1 == "push" and op3 == "pop" and op2 not in ("push", "pop"):
            # Only do this if a3 is not mofidied in the middle instruction. An
            # obvious improvement would be to allow an arbitrary number of
            # in-between instructions.
            if a2 != a3:
                index += 3
                yield "mov", a3, a1
                yield op2, a2, b2
                continue

        # TODO: Generalize this, then remove the previous two
        # Same as above, but with an in-between instruction
        if (op1 == "push" and op4 == "pop" and op2 not in ("push", "pop") and
                op3 not in ("push", "pop")):
            # Only do this if a3 is not mofidied in the middle instruction. An
            # obvious improvement would be to allow an arbitrary number of
            # in-between instructions.
            if a2 != a4 and a3 != a4:
                index += 4
                yield "mov", a4, a1
                yield op2, a2, b2
                yield op3, a3, b3
                continue

        index += 1
        yield op1, a1, b1

def print_ir(ir):
    for instruction in ir:
        op, args = instruction[0], instruction[1:]
        args = filter(lambda x: x is not None, args)
        print("  %-6s %s" % (op, ", ".join(map(str, args))))

def compile_native(function, verbose=True):
    if verbose:
        print("Python disassembly:")
        dis.dis(function)
        print("")

    codeobj = get_codeobj(function)
    if verbose:
        print("Bytecode: %r" % codeobj.co_code)
        print("")

    if verbose:
        print("Intermediate code:")
    constants = codeobj.co_consts

    python_bytecode = list(codeobj.co_code)

    if sys.version_info.major == 2:
        python_bytecode = map(ord, codeobj.co_code)

    ir = Compiler(python_bytecode, constants).compile()
    ir = list(ir)
    if verbose:
        print_ir(ir)
        print("")

    if verbose:
        print("Optimization:")
    while True:
        optimized = list(optimize(ir))
        reduction = len(ir) - len(optimized)
        ir = optimized
        if verbose:
            print("  - removed %d instructions" % reduction)
        if not reduction:
            break
    if verbose:
        print_ir(ir)
        print("")

    # Compile to native code
    assembler = Assembler(mj.PAGESIZE)
    for name, a, b in ir:
        emit = getattr(assembler, name)
        emit(a, b)

    # Make block executable and read-only
    mj.make_executable(assembler.block, assembler.size)

    argcount = codeobj.co_argcount

    if argcount == 0:
        signature = ctypes.CFUNCTYPE(None)
    else:
        # Assume all arguments are 64-bit
        signature = ctypes.CFUNCTYPE(*[ctypes.c_int64] * argcount)

    signature.restype = ctypes.c_int64
    return signature(assembler.address), assembler

def jit(function, verbose=True):
    """Decorator that JIT-compiles function to native code on first call.

    Use this on non-class functions, because our compiler does not support
    objects (rather, it does not support the attr bytecode instructions).

    Example:
        @jit
        def foo(a, b):
            return a*a - b*b
    """
    if verbose:
        print("Installing JIT for %s" % function)

    def frontend(*args, **kw):
        if not hasattr(frontend, "function"):
            if verbose:
                print("JIT-compiling %s" % function)

            try:
                native, asm = compile_native(function, verbose=False)
                native.raw = asm.raw
                native.address = asm.address
                frontend.function = native
                print("Installed native code for %s" % function)
            except Exception as e:
                if verbose:
                    print("Could not compile %s: %s: %s" % (function,
                        e.__class__.__name__, e))
                    print("Falling back to %s" % function)
                frontend.function = function

        if verbose:
            print("Calling function %s" % frontend.function)
        return frontend.function(*args, **kw)

    return frontend

def disassemble(function):
    """Returns disassembly string of natively compiled function.

    Requires the Capstone module."""
    def hexbytes(raw):
        return "".join("%02x " % b for b in raw)

    try:
        import capstone

        out = ""
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

        for i in md.disasm(function.raw, function.address):
            out += "0x%x %-15s%s %s\n" % (i.address, hexbytes(i.bytes), i.mnemonic, i.op_str)
            if i.mnemonic == "ret":
                break

        return out
    except ImportError:
        print("You need to install the Capstone module for disassembly")
        raise
