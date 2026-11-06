CC 				:= pyinstaller
CC_FLAGS 	:= --onefile
SOURCES 	:= $(wildcard src/*.py)
DL_FILES 	:= $(wildcard examples/*.dl)

all: build/dlc $(DL_FILES)

build/dlc: $(SOURCES)
	$(CC) $(CC_FLAGS) --name compiler $^
	$(RM) -r build/* compiler.spec
	mv ./dist/compiler $@
	$(RM) -r dist

%.dl: build/examples
	@echo "compiling: $@"
	./build/dlc $@ -o build/$(@:.dl=)

build/examples:
	mkdir -p $@

clean:
	$(RM) -r build

.PHONY: all clean

