#!/usr/bin/env python
# vim: ts=4 sw=4 et

class Parser:
    def __init__(self, callback):
        self.callback = callback
        self.buffer = None
        self.missed = 0
    def parse(self, line):
        line = line.strip()
        if self.buffer is None:
            if "Traceback (most recent call last):" in line:
                self.buffer = [line]
        else:
            if line.startswith("File \""):
                self.buffer.append(line)
            elif self.buffer[-1].startswith("File \""):
                self.buffer.append(line)
            else:
                sp = line.split()
                if sp[0][-1] != ":":
                    self.missed += 1
                    if self.missed > 4:
                        self.buffer = None
                        self.missed = 0
                    return
                self.buffer.append(line)
                self.callback(self.buffer)
                self.buffer = None
                self.missed = 0

if __name__ == '__main__':
    import sys
    filename = sys.argv[1]
    def p(data):
        print(data[-1].strip())
    p = Parser(p)
    for line in open(filename).readlines():
        line = line.split(";",2)[2]
        p.parse(line)

