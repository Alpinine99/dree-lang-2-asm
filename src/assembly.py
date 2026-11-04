
class ASM:
    def __init__(self):
        self.section = self.Section()

    def write(self):
        body = "global _start"
        if self.section.bss.edited:
            body += f"\n{self.section.bss.getBody()}"
        if self.section.data.edited:
            body += f"\n{self.section.data.getBody()}"
        body += f"\n{self.section.text.getBody()}"
        body += "\nmov rax, 60\nmov rdi, 0\nsyscall\n"
        if self.section.funcs.edited:
            body += f"\n{self.section.funcs.getBody()}"
        return body

    class Section:
        def __init__(self):
            self.bss = self.InnerSec("\nsection .bss")
            self.data = self.InnerSec("\nsection .data")
            self.text = self.InnerSec("\nsection .text\n_start:")
            self.funcs = self.InnerSec("\n")

        class InnerSec:
            def __init__(self, definition: str):
                self._body = definition
                self.edited = False

            def append(self, s: str):
                self._body += f"\n{s}"
                self.edited = True

            def getBody(self):
                return self._body


