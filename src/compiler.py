import sys, os, tempfile, subprocess
from dl import Dl

DEBUG, INFO, WARNING, ERROR = 1, 2, 3, 4, 
LOG_LEVEL = INFO

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
    if level >= LOG_LEVEL: print(f"{TAG}: {' '.join(msg)}")
    if level==4: exit(1)

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
    LOG(INFO, "rewriting ...")
    with open(file_name, 'r') as f:
        lines = f.readlines()

    line_no = 0
    LOG(INFO, "tokenizing ...")
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

def main():
    global LOG_LEVEL
    try:
        usage = f"{sys.argv[0]} <path/to/file.dl> (log level)<1|2|3|4> --asm"
        if len(sys.argv) == 1:
            raise Exception("file path required")

        gen_asm = False
        file_name = sys.argv[1]
        try: LOG_LEVEL = int(sys.argv[2])
        except IndexError: pass
        except Exception: raise Exception("log level must be int")

        try:
            if sys.argv[3] == "--asm": gen_asm = True
            else: raise Exception(f"Unknown flag {sys.argv[3]}")
        except IndexError: pass

        if not os.path.exists(file_name):
            raise Exception(f"file '{file_name}' doesn't exist")
    except Exception as e:
        LOG(ERROR, f"{e}\n{usage}")

    executable_file = os.path.splitext(os.path.basename(file_name))[0]
    assembly_file = f"{executable_file}.asm"
    object_file = f"{executable_file}.o"
    body = rewrite(file_name)
    with open(assembly_file, "w") as f: f.write(body)

    LOG(INFO, "compiling ... ")
    result = subprocess.run([
        "nasm", "-f", "elf64", "-o", object_file, assembly_file
    ], capture_output=True, text=True)
    if not gen_asm: os.remove(assembly_file)
    if result.returncode != 0:
        LOG(ERROR, result.stderr)

    LOG(INFO, "linking ... ")
    result = subprocess.run([
        "ld", "-o", executable_file, object_file
    ], capture_output=True, text=True)
    if not gen_asm: os.remove(object_file)
    if result.returncode != 0:
        LOG(ERROR, result.stderr)

main()

