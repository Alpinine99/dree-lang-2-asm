CC 				:= pyinstaller
CC_FLAGS 	:= --onefile
SOURCES 	:= $(wildcard src/*.py)
DL_FILES 	:= $(wildcard examples/*.dl)

all: build/dl-compiler $(DL_FILES)

build/dl-compiler: $(SOURCES)
	$(CC) $(CC_FLAGS) --name compiler $^
	$(RM) -r build/* compiler.spec
	mv ./dist/compiler $@
	$(RM) -r dist

%.dl: build/dl-compiler | build
	@echo "compiling: $@"
	cd build && ./dl-compiler ../$@

build:
	mkdir -p build

clean:
	$(RM) -r build

.PHONY: all clean

