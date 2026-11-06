import sys, os, argparse, subprocess, tempfile
from pathlib import Path
from dl import Dl
from config import *

DEBUG, INFO, WARNING, ERROR = 1, 2, 3, 4, 
LOG_LEVEL = INFO

__version__ = VERSION
PROG_NAME = os.path.basename(sys.argv[0])

def LOG(level: int, *msg):
    '''
    ERROR:      -> 4
    WARNING:    -> 3
    INFO:       -> 2
    DEBUG:      -> 1
    '''
    TAG = "DEBUG"
    if level==2: TAG = "INFO"
    elif level==3: TAG = "WARNING"
    elif level==4: TAG = "ERROR"
    if level >= LOG_LEVEL:
        if level >= WARNING:
            print(f"{PROG_NAME}: [{TAG}] {' '.join(msg)}", file=sys.stderr)
        else: 
            print(f"{PROG_NAME}: [{TAG}] {' '.join(msg)}")

    if level==4: os._exit(1)

def perLineToken(no: int, line: str):
    tokens = []
    token = ""
    quote = None
    index = 0
    for ch in line.strip():
        if ch in ["'", "\""]:
            if not quote: quote = ch
            elif quote == ch: quote = None

        index += 1
        if quote:
            token += ch
            continue

        if ch == " ":
            if token: tokens.append(token)
            token = ""
            continue
        token += ch

    if token: tokens.append(token)
    if quote:
        LOG(ERROR, f"unmatched quote in at (line {no}) {line}")

    return tokens

def rewrite(file_name: str):
    LOG(INFO, f"rewriting {file_name}")
    with open(file_name, 'r') as f:
        lines = f.readlines()

    line_no = 0
    LOG(INFO, f"tokenizing {file_name}")
    lang = Dl()
    for line in lines:
        line_no += 1
        if not line.strip(): continue
        tokens = perLineToken(line_no, line)
        LOG(DEBUG, f"[line {line_no}] {tokens}")
        try:
            lang.parse(tokens)
        except Exception as e:
            LOG(ERROR, f"parser at (line {line_no}) {e}")

    return lang.write()

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog=f"{PROG_NAME}",
        usage="%(prog)s [options] file...",
        allow_abbrev=False,          # gcc doesn't guess partial option names
    )

    p.add_argument("files", nargs="+", metavar="file", help="input files")

    p.add_argument("-o", dest="output", metavar="file",
                   help="place the output into <file>")
    p.add_argument("-c", dest="compile_only", action="store_true",
                   help="compile, but do not link")
    p.add_argument("-I", dest="include_dirs", action="append", default=[],
                   metavar="dir", help="add <dir> to the include path")
    p.add_argument("-L", dest="lib_dirs", action="append", default=[],
                   metavar="dir", help="add <dir> to the library path")
    p.add_argument("-l", dest="libs", action="append", default=[],
                   metavar="lib", help="link with <lib>")
    p.add_argument("-lv", dest="loglevel", type=int, default=INFO,
                   help=f"loglevel {LOG.__doc__}")
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s: build version {__version__}",
                   help="print build version")
    p.add_argument("--asm", dest="gen_asm", default=False,
                   action=argparse.BooleanOptionalAction, help="produce intermediate files")

    # parse_intermixed_args lets options and files be mixed: a.c -o out b.c
    return p.parse_intermixed_args(argv)

def compile(asms: list, exe: str, compile_only: bool=False, objfs: list=None, fasms: list=None):
    with tempfile.TemporaryDirectory(prefix=f"{PROG_NAME}_") as tmp:
        tmp = Path(tmp)
        srcs = list(Path(fasm) for fasm in fasms) if fasms else list([tmp / f"prog.{i}.s" for i in range(len(asms))])
        if compile_only and not objfs: return 1, "objfs required for compile_only=True"
        objfs = objfs if objfs else list([tmp / f"prog.{i}.o" for i in range(len(asms))])
        if compile_only:
            if len(asms) == 1:
                objfs = [exe] if exe.endswith(".o") else [f"{exe}.o"]

        LOG(INFO, "compiling ... ")
        for asm, src, objf in zip(asms, srcs, objfs):
            src.write_text(asm)
            cmd = ["nasm", "-f", "elf64", "-o", objf, src]
            LOG(DEBUG, "[shell]$", " ".join([str(i) for i in cmd]))
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0: return res.returncode, res
        
        if compile_only: return 0, None

        LOG(INFO, "linking ... ")
        cmd = ["ld", "-o", exe]
        cmd.extend(objfs)
        LOG(DEBUG, "[shell]$", " ".join([str(i) for i in cmd]))
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode, res

def main():
    global LOG_LEVEL
    args = parse_args(sys.argv[1:])

    try:
        if args.output and args.compile_only and len(args.files) > 1:
            raise Exception("cannot specify -o with -c and multiple files")
        if not args.output:
            args.output = "a.out"
        if len(args.files) < 1:
            raise Exception("no input files specified")
        fexist = [os.path.exists(file) for file in args.files]
        if False in fexist:
            raise Exception(f"file '{args.files[fexist.index(False)]}' doesn't exist")
    except Exception as e:
        LOG(ERROR, f"{e}")

    LOG_LEVEL = args.loglevel

    LIBS.extend(args.libs)
    LIB_DIRS.extend(args.lib_dirs)
    INCLUDE_DIRS.extend(args.include_dirs)

    LOG(DEBUG, f"libs: {','.join(LIBS)}")
    LOG(DEBUG, f"lib_dirs: {','.join(LIB_DIRS)}")
    LOG(DEBUG, f"include_dirs: {','.join(INCLUDE_DIRS)}")

    asmfs, objfs = None, None
    if args.gen_asm:
        asmfs = list([f"{os.path.splitext(os.path.basename(file))[0]}.s" for file in args.files])
    if args.compile_only:
        objfs = list([f"{os.path.splitext(os.path.basename(file))[0]}.o" for file in args.files])

    asms = list([rewrite(file) for file in args.files])
    code, res = compile(asms, args.output, args.compile_only, objfs, asmfs)
    if code != 0:
        LOG(ERROR, f"{res.returncode}:{res.stderr}")

if __name__ == "__main__":
    sys.exit(main())

