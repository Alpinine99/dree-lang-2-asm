CC := pyinstaller
CC_FLAGS := --onefile
SOURCES := $(wildcard src/*.py)

all: dl-compiler

dl-compiler: $(SOURCES)
	$(CC) $(CC_FLAGS) --name $@ $^

clean:
	$(RM) -r build dist dl-compiler.spec

.PHONY: dl-compiler clean all

