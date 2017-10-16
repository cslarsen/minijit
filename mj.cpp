// Written by Christian Stigen Larsen
// Public domain, 2017

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/mman.h>

void ret_program(uint8_t* block, const size_t /*length*/)
{
  block[0] = 0xc3; // RETN
}

void ret2_program(uint8_t* block, const size_t /*length*/)
{
  // mov ax, 123
  block[0] = 0xb0; // mov r8, imm8 (+0 = ax=
  block[1] = 123;  // immediate value
  block[2] = 0xc3; // RETN
}

void mul2_program(uint8_t* block, const size_t length)
{
  /*
   * 40085a:	55                   	push   %rbp
   * 40085b:	48 89 e5             	mov    %rsp,%rbp
   * 40085e:	89 7d fc             	mov    %edi,-0x4(%rbp)
   * 400861:	8b 45 fc             	mov    -0x4(%rbp),%eax
   * 400864:	01 c0                	add    %eax,%eax
   * 400866:	5d                   	pop    %rbp
   * 400867:	c3                   	retq
   */

  assert(length >= 14);

  // prologue; don't usually need this
  block[0] = 0x55; // push rbp
  // mov %rsp, %rbp
  block[1] = 0x48;
  block[2] = 0x89;
  block[3] = 0xe5;

  // mov %edi, -0x4(%rbp)
  block[4] = 0x89;
  block[5] = 0x7d;
  block[6] = 0xfc;

  // get argument into eax: mov -0x4(%rbp), %eax
  block[7] = 0x8b;
  block[8] = 0x45;
  block[9] = 0xfc;

  // add eax, eax
  block[10] = 0x01;
  block[11] = 0xc0;

  // prologue: pop rbp
  block[12] = 0x5d;

  // retq
  block[13] = 0xc3;
}

int main()
{
  const size_t pagesize = sysconf(_SC_PAGE_SIZE);
  printf("pagesize %zu\n", pagesize);

  uint8_t* block = static_cast<uint8_t*>(mmap(NULL, pagesize, PROT_WRITE |
        PROT_READ, MAP_PRIVATE | MAP_ANONYMOUS, 0, 0));

  if (reinterpret_cast<int64_t>(block) == -1) {
    perror("mmap");
    exit(1);
  }

  printf("compiling code\n");
  mul2_program(block, pagesize);

  printf("marking as executable\n");
  if (mprotect(block, pagesize, PROT_READ | PROT_EXEC)) {
    perror("mprotect");
    exit(1);
  }

  printf("calling JIT\n");
  int (*call)(int) = reinterpret_cast<int (*)(int)>(block);
  int result = call(12);
  printf("%s result %d\n", result == 24? "OK" : "FAIL", result);
  for ( int i=0; i<10; ++i ) {
    result = call(i);
    printf("%s call(%d) = %d\n", result == i*2 ? "OK" : "FAIL", i, result);
  }

  printf("done\n");
  return 0;
}
