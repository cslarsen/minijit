CXXFLAGS := -W -Wall -O2 -march=native
TARGETS := mj

all: $(TARGETS)

run: mj
	./mj
	@echo exited w/code $$?

clean:
	rm -f $(TARGETS)
