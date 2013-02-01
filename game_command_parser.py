import re

commands= r"""
(?P<say>\b[Ss]ay\b)
|(?P<examine>\b[eE]xamine\b)
|(?P<identifier>[a-zA-Z_][a-zA-Z0-9_]*)
|(?P<whitespace>[\s+])
|(?P<playerself>@me)
|(?P<playerlocation>@here)
|(?P<dot>[.])
|(?P<string>".*")
|(?P<open_brace>[(])
|(?P<close_brace>[)])
|(?P<newline>[\n])
|(?P<end>$)
"""

token_re = re.compile(commands, re.VERBOSE)


class Symbol(object):
    first = None
    second = None
    third = None
    id = ""
    value = None
    def __init__(self, id, token, next):
        self.id = id
        self.token = token
        self.next = next
        
    def nud(self):
        raise SyntaxError("Not implemented")
    def led(self, left):
        raise SyntaxError("Not implemented")
    
    def __repr__(self):
        if self.id == "say" or self.id == "(literal)":
            return "(%s %s)" % (self.id[1:-1], self.value)
        out = [self.id, self.first, self.second, self.third]
        out = map(str, filter(None, out))
        return "(" + " ".join(out) + ")"
        
    
class Say(Symbol):
    def nud(self):
        self.value = ""
        t = self.next()
        vals = []
        while True:
            if t.type == 'end' : break
            while t.type == 'whitespace':
                t = self.next()
            vals.append(t.value)
            t=self.next()
        self.value = " ".join(vals)
        print self
        return self




class Parser(object):
    token = None
    next = None
    lbp = 0
    
    def parse(self, program):
        self.next = self.tokenize(program).next
        self.token = self.next()
        return self.expression()
    
    def expression(self, rbp=0):
        l = self.getSymbol(self.token)
        n = self.getSymbol(self.next())
        left = l.nud()
        while True:
            if not self.token : break
            l = self.getSymbol(self.token)
            
            self.token = self.next()
            left = l.led(left)
        return left
        
    def getSymbol(self, _token):
        if _token.type == 'say':
            return Say('say', _token, self.next)
        
    def tokenize(self, text):
        pos = 0
        while True:
            m = token_re.match(text, pos)
            if not m: break
            pos = m.end()
            yield Token(m.lastgroup, m.group(m.lastgroup))


    
class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value
    def __repr__(self):
        return "[ " + self.type + " : " + self.value + " ]"
    
def tokenize(text):
    pos = 0
    while True:
        m = token_re.match(text, pos)
        if not m:break
        pos = m.end()
        tokname = m.lastgroup
        tokvalue = m.group(tokname)
        yield Token(tokname, tokvalue)
    if pos != len(text):
        print "failed to parse"

def parse(program):
    global token, next
    next = tokenize(program).next
    token = next()
    return expression()

def expression():
    global token
    t = token
    t = next()
    left = t.nud()
    while True:
        if token.type == 'end': break
        
    

stuff = "say this is all nonsense you know"
stuff2 = "examine cock"
stuff3 = '@me.operation("something i like")'

print " stuff ".center(60, "=")

p = Parser()
p.parse(stuff)
