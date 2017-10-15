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

void mul2_program(uint8_t* block, const size_t /*length*/)
{
  /*
   * 100000de4:	89 7d fc             	mov    %edi,-0x4(%rbp)
   * 100000dea:	c1 e7 01             	shl    $0x1,%edi
   * 100000ded:	89 f8                	mov    %edi,%eax
   */

  // mov edi, rbp[-4]
  block[0] = 0x89;
  block[1] = 0x7d;
  block[3] = 0xfc;

  // shl edi, 1
  block[4] = 0xc1;
  block[5] = 0xe7;
  block[6] = 0x01;

  // mox eax, edi
  block[7] = 0x89;
  block[8] = 0xf8;

  block[9] = 0xc3; // RETN
}

int main()
{
  const size_t pagesize = sysconf(_SC_PAGE_SIZE);
  printf("pagesize %zu\n", pagesize);

  uint8_t* block = static_cast<uint8_t*>(malloc(pagesize));

  mul2_program(block, pagesize);

  if (mprotect(block, pagesize, PROT_READ | PROT_EXEC)) {
    perror("mprotect");
    return 1;
  }

  printf("calling JIT\n");
  int (*call)(int) = reinterpret_cast<int (*)(int)>(block);
  int result = call(12);
  assert(result == 24);
  printf("result %d\n", result);
  for ( int i=0; i<10; ++i )
    printf("call(%d) = %d\n", i, call(i));

  printf("done\n");
  return 0;
}
