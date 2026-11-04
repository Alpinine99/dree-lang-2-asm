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
                self._asm.section.data.append(f"{var}: db {token}")
                self._asm.section.data.append(f"{lenv}: equ $ - {var}")
                self._asm.section.text.append("mov rax, 1")
                self._asm.section.text.append("mov rdi, 1")
                self._asm.section.text.append(f"mov rsi, {var}")
                self._asm.section.text.append(f"mov rdx, {lenv}")
                self._asm.section.text.append("syscall")

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
                    buf = self.resvIntBuf()
                    body = [
                        f"mov rax, [{var}]", f"mov rcx, {buf}", "add rcx, 20", "mov rbx, 10", 
                        ".next_digit:", "xor rdx, rdx", "div rbx", "add dl, '0'", "dec rcx",
                        "mov [rcx], dl", "test rax, rax", "jnz .next_digit", f"mov rbx, {buf}",
                        "add rbx, 20", "sub rbx, rcx", "mov rax, 1", "mov rdi, 1", "mov rsi, rcx",
                        "mov rdx, rbx", "syscall"
                    ]
                    self._asm.section.text.append("\n".join(body))

            else:
                raise Exception(f"invalid token '{token}'")
        
        if KEYWORDS.get(tokens[0]) == 2:
            self._asm.section.text.append("mov rax, 1")
            self._asm.section.text.append("mov rdi, 1")
            self._asm.section.text.append("mov byte [rsi], 10")
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

