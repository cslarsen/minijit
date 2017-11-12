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

extern "C" int hello(int n) {
  return n*113;
}

void make_mul(uint8_t* block, const size_t /*length*/, const int32_t multiplier)
{
  /*
   * 4007ed:	55                   	push   rbp
   * 4007ee:	48 89 e5             	mov    rbp,rsp
   * 4007f1:	89 7d fc             	mov    DWORD PTR [rbp-0x4],edi
   * 4007f4:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
   * 4007f7:	01 c0                	add    eax,eax
   * 4007f9:	5d                   	pop    rbp
   * 4007fa:	c3                   	ret
   */

  // function prologue
  // push rbp
  block[0] = 0x55;
  // mov rbp, rsp
  block[1] = 0x48;
  block[2] = 0x89;
  block[3] = 0xe5;

  // put argument onto stack.. :)
  block[4] = 0x89;
  block[5] = 0x7d;
  block[6] = 0xfc;

  // get argument into eax :D mov eax, dword ptr [rbp-0x4]
  block[7] = 0x8b;
  block[8] = 0x45;
  block[9] = 0xfc;

  // mov edx, immediate 32-bit value
  block[10] = 0xba;
  // little-endian
  block[11] = (multiplier & 0x000000ff);
  block[12] = (multiplier & 0x0000ff00) >> 8;
  block[13] = (multiplier & 0x00ff0000) >> (4*4);
  block[14] = (multiplier & 0xff000000) >> (6*4);

  // 400927:	0f af c2             	imul   eax,edx
  block[15] = 0x0f;
  block[16] = 0xaf;
  block[17] = 0xc2;

  // function prologue: pop rbp
  block[18] = 0x5d;

  // retq
  block[19] = 0xc3;
}

void testmul(uint8_t* block, int32_t mul)
{
  int (*call)(int) = reinterpret_cast<int (*)(int)>(block);

  printf("calling JIT\n");

  // test a simple example first
  int result = call(12);
  printf("%s result %d\n", result == (12*mul)? "OK" : "FAIL", result);

  for ( int i=0; i<10; ++i ) {
    result = call(i);
    printf("%s call(%d) = %d\n", result == i*mul ? "OK" : "FAIL", i, result);
  }
}

int main(int argc, char** argv)
{
  int32_t multiplier = 2;
  if ( argc > 1 )
    multiplier = atoi(argv[1]);

  const size_t pagesize = sysconf(_SC_PAGE_SIZE);
  printf("pagesize %zu\n", pagesize);

  uint8_t* block = static_cast<uint8_t*>(mmap(NULL, pagesize, PROT_WRITE |
        PROT_READ, MAP_PRIVATE | MAP_ANONYMOUS, 0, 0));

  if (reinterpret_cast<int64_t>(block) == -1) {
    perror("mmap");
    exit(1);
  }

  printf("compiling code w/multiplier %d\n", multiplier);
  make_mul(block, pagesize, multiplier);

  printf("marking as executable\n");
  if (mprotect(block, pagesize, PROT_READ | PROT_EXEC)) {
    perror("mprotect");
    exit(1);
  }

  testmul(block, multiplier);

  printf("freeing code block\n");
  if (munmap(block, pagesize) == -1) {
    perror("munmap");
    exit(1);
  }

  printf("done\n");
  return 0;
}
