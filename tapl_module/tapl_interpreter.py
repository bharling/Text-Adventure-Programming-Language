'''
Created on 9 Feb 2012

@author: bharling
'''

import re

token_pat = re.compile("\s*(?:(\d+)|(.))")


def expression(rbp=0):
    global token
    t = token
    token = next()
    left = t.nud()
    while rbp < token.lbp:
        t = token
        token = next()
        left = t.led(left)
    return left

class symbol_base(object):
    
    id = None
    value = None
    first = second = third = None
    
    def nud(self):
        raise SyntaxError("Syntax Error (%r)." % self.id)
    
    def led(self, left):
        raise SyntaxError("Unknown operator (%r)." % self.id)
    
    def __repr__(self):
        if self.id == "(name)" or self.id == "(literal)":
            return "(%s %s)" % (self.id[1:-1], self.value)
        out = [self.id, self.first, self.second, self.third]
        out = map(str, filter( None, out))
        return "(" + " ".join(out) + ")"
    
symbol_table = {}

def symbol(_id, bp=0):
    try:
        s = symbol_table[_id]
    except KeyError:
        class s(symbol_base):
            pass
        s.__name__ = "symbol_" + _id
        s.id = _id
        s.lbp = bp
        symbol_table[_id] = s
    else:
        s.lbp = max(bp, s.lbp)
    return s

symbol("(literal)")
symbol("+", 10)
symbol("-", 10)
symbol("*", 20)
symbol("/", 20)
symbol("**", 30)
symbol("(end)")

def tokenize(program):
    for number, operator in token_pat.findall(program):
        if number:
            symbol = symbol_table["(literal)"]
            s = symbol()
            s.value = number
            yield s
        else:
            symbol = symbol_table.get(operator)
            if not symbol:
                raise SyntaxError("Unknown operator")
            yield symbol()
    symbol = symbol_table["(end)"]
    yield symbol()
    
def led(self, left):
    self.first = left
    self.second = expression(10)
    return self
symbol("+").led = led

def led(self, left):
    self.first = left
    self.second = expression(10)
    return self
symbol("-").led = led



