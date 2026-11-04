from assembly import ASM

KEYWORDS = {
    "print:": 1, "printl:": 2
}

class Dl:
    def __init__(self):
        self._asm = ASM()
        self._var = [0, "v4r"]
        self._defined_vars = []
        self._intBufReserved = False
        self._hasNumPrintFunc = False
        self._hasPrintFunc = False
        self._hasNewline = False

    def newline(self):
        name = f"{self._var[1]}_nl"
        if not self._hasNewline:
            self._asm.section.data.append(f"{name}: db 10")
            self._hasNewline = True
        return name

    def printFunc(self):
        fname = "pstr"
        if not self._hasPrintFunc:
            body = [
                f"\n{fname}:", "mov rax, 1", "mov rdi, 1", "syscall", "ret"
            ]
            self._asm.section.funcs.append("\n".join(body))
            self._hasPrintFunc = True
        return fname

    def numPrintFunc(self):
        fname = "pnum"
        if not self._hasNumPrintFunc:
            buf = self.resvIntBuf()
            body = [
                f"\n{fname}:", f"mov rcx, {buf}", "add rcx, 20", "mov rbx, 10", 
                ".next_digit:", "xor rdx, rdx", "div rbx", "add dl, '0'", "dec rcx",
                "mov [rcx], dl", "test rax, rax", "jnz .next_digit", f"mov rbx, {buf}",
                "add rbx, 20", "sub rbx, rcx", "mov rax, 1", "mov rdi, 1", "mov rsi, rcx",
                "mov rdx, rbx", "syscall", "ret"
            ]
            self._asm.section.funcs.append("\n".join(body))
            self._hasNumPrintFunc = True
        return fname

    def getVar(self):
        self._var[0] += 1
        return f"{self._var[1]}_{self._var[0]}"

    def resvIntBuf(self):
        name = "ibuf"
        if not self._intBufReserved:
            self._asm.section.bss.append(f"{name}: resb 20")
            self._intBufReserved = True
        return name

    def varDec(self, tokens):
        if len(tokens) < 3: return False
        if tokens[1] != "=": return False
        if tokens[2][0] in ["'", "\""]:
            self._asm.section.data.append(f"{tokens[0]}: db {tokens[2]}")
            self._asm.section.data.append(f"{tokens[0]}_len: equ $ - {tokens[0]}")
            self._defined_vars.append((tokens[0], str))
        else:
            try:
                num = int(tokens[2])
                if num > (2 ** 63) - 1: # signed integer
                    raise Exception("integer overflow")
                self._asm.section.data.append(f"{tokens[0]}: dq {num}")
                self._defined_vars.append((tokens[0], int))
            except Exception:
                raise Exception("invalid variable definition")
        return True

    def print(self, tokens: list):
        if KEYWORDS.get(tokens[0]) not in [1, 2]: return False
        for token in tokens[1:]:
            if token[0] in ["'", "\""]:
                var = self.getVar()
                lenv = f"{var}_len"
                fname = self.printFunc()
                self._asm.section.data.append(f"{var}: db {token}")
                self._asm.section.data.append(f"{lenv}: equ $ - {var}")
                self._asm.section.text.append(f"mov rsi, {var}")
                self._asm.section.text.append(f"mov rdx, {lenv}")
                self._asm.section.text.append(f"call {fname}")

            elif token[0] == "#":
                defined_vars = [var for var, _ in self._defined_vars]
                var = token[1:]
                if var not in defined_vars:
                    raise Exception(f"Undefined variable '{var}'")
                _, _type = self._defined_vars[defined_vars.index(var)]
                if _type == str:
                    lenv = f"{var}_len"
                    self._asm.section.text.append("mov rax, 1")
                    self._asm.section.text.append("mov rdi, 1")
                    self._asm.section.text.append(f"mov rsi, {var}")
                    self._asm.section.text.append(f"mov rdx, {lenv}")
                    self._asm.section.text.append("syscall")

                elif _type == int:
                    fname = self.numPrintFunc()
                    self._asm.section.text.append(f"mov rax, [{var}]")
                    self._asm.section.text.append(f"call {fname}")

            else:
                raise Exception(f"invalid token '{token}'")
        
        if KEYWORDS.get(tokens[0]) == 2:
            self._asm.section.text.append("mov rax, 1")
            self._asm.section.text.append("mov rdi, 1")
            self._asm.section.text.append(f"mov rsi, {self.newline()}")
            self._asm.section.text.append("mov rdx, 1")
            self._asm.section.text.append("syscall")

        return True

    def parse(self, tokens: list):
        if len(tokens) == 0: return
        if self.varDec(tokens): return
        if self.print(tokens): return
        raise Exception("undefined state")

    def write(self):
        return self._asm.write()

