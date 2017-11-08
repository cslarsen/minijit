CXXFLAGS := -W -Wall -O2 -g -march=native
TARGETS := mj

all: $(TARGETS)

run: mj
	./mj
	@echo exited w/code $$?

libmultiply.so: multiply.c
	gcc -W -Wall -march=native -Os -fPIC -shared $< -o$@

dis: libmultiply.so
	objdump -d $<

clean:
	rm -f $(TARGETS) libmultiply.so
