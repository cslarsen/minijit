// Written by Christian Stigen Larsen
// Public domain, 2017

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

int main()
{
  const size_t pagesize = sysconf(_SC_PAGE_SIZE);
  printf("pagesize %zu\n", pagesize);

  uint8_t* block = static_cast<uint8_t*>(malloc(pagesize));

  ret2_program(block, pagesize);

  if (mprotect(block, pagesize, PROT_READ | PROT_EXEC)) {
    perror("mprotect");
    return 1;
  }

  printf("calling JIT\n");
  int (*call)(void) = reinterpret_cast<int (*)(void)>(block);
  int8_t result = call();
  printf("result %d\n", result);

  printf("done\n");
  return 0;
}
