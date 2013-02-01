import re

scope = None

class original_scope(object):
    
    _def = {}
    
    def __init__(self):
        pass
    
    def define(self, n):
        t = self._def[n.value]
        if t:
            if t.reserved:
                raise TypeError("%s is already reserved" % n.value)
            else:
                raise TypeError("%s is already defined" % n.value)
        self._def[n.value] = n
        n.reserved = False
        n.nud = lambda self : self
        n.led = None
        n.std = None
        n.lbp = 0
        n.scope = scope
        return n
    
    def find(self, n):
        e = self
        while True:
            o = e._def[n]
            if o and hasattr(o, "__call__"):
                return e._def[n]
            e = e.parent
            if not e:
                o = symbol_table[n]
                return o and not hasattr(o, "__call__")


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
    id = None # node/token type name
    value = None # used by literals
    first = second = third = None # used by tree nodes
    
    def nud(self):
        raise SyntaxError("Syntax Error (%r)." % self.id)
    def led(self, left):
        raise SyntaxError("Unknown Operator (%r)." % self.id)
    def __repr__(self):
        if self.id == "(name)" or self.id == "(literal)":
            return "(%s %s)" % (self.id[1:-1], self.value)
        out = [self.id, self.first, self.second, self.third]
        out = map(str, filter(None, out))
        return "(" + " ".join(out) + ")"
    
symbol_table = {}

def advance(id=None):
    global token
    if id and token.id != id:
        raise SyntaxError("Expected %r" % id)
    token = next()

def symbol(id, bp=0):
    try:
        s = symbol_table[id]
    except KeyError:
        class s(symbol_base):
            pass
        s.__name__ = "symbol-" + id
        s.id = id
        s.lbp = bp
        symbol_table[id] = s
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


def tokenize_python(program):
    import tokenize
    from cStringIO import StringIO
    type_map = {
        tokenize.NUMBER: "(literal)",
        tokenize.STRING: "(literal)",
        tokenize.OP: "(operator)",
        tokenize.NAME: "(name)",
        }
    for t in tokenize.generate_tokens(StringIO(program).next):
        try:
            yield type_map[t[0]], t[1]
        except KeyError:
            if t[0] == tokenize.ENDMARKER:
                break
            else:
                raise SyntaxError("Syntax Error")
    yield "(end)", "(end)"
    
def tokenize(program):
    for id, value in tokenize_python(program):
        if id == "(literal)":
            symbol = symbol_table[id]
            s = symbol()
            s.value = value
        else:
            symbol = symbol_table.get(value)
            if symbol:
                s = symbol()
            elif id == "(name)":
                symbol = symbol_table[id]
                s = symbol()
                s.value = value
            else:
                raise SyntaxError("Unknown Operator (%r)" % id)
        yield s


#def tokenize(program):
#    for number, operator in token_pat.findall(program):
#        if number:
#            symbol = symbol_table['(literal)']
#            s = symbol()
#            s.value = number
#            yield s
#        else:
#            symbol = symbol_table.get(operator)
#            if not symbol:
#                raise SyntaxError("Unknown Operator")
#            yield symbol()
#    symbol = symbol_table['(end)']
#    yield symbol()
    
def infix(id,bp):
    def led(self, left):
        self.first = left
        self.second = expression(bp)
        return self
    symbol(id, bp).led = led
    
def prefix(id,bp):
    def nud(self):
        self.first = expression(bp)
        self.second = None
        return self
    symbol(id).nud = nud
    
def infix_r(id,bp):
    def led(self, left):
        self.first = left
        self.second = expression(bp-1)
        return self
    symbol(id,bp).led = led
    
infix("**", 30)
    
prefix("+", 100)
prefix("-", 100)
    
infix("+", 10)
infix("-", 10)
infix("*", 20)
infix("/", 20) 
    
symbol("(literal)").nud = lambda self : self
symbol("(name)").nud = lambda self : self
symbol("(end)")

symbol("lambda", 20)
symbol("if", 20)
symbol("else")

symbol("lambda", 20)
symbol("if", 20) # ternary form

infix_r("or", 30); infix_r("and", 40); prefix("not", 50)

infix("in", 60); infix("not", 60) # in, not in
infix("is", 60) # is, is not
infix("<", 60); infix("<=", 60)
infix(">", 60); infix(">=", 60)
infix("<>", 60); infix("!=", 60); infix("==", 60)

infix("|", 70); infix("^", 80); infix("&", 90)

infix("<<", 100); infix(">>", 100)

infix("+", 110); infix("-", 110)

infix("*", 120); infix("/", 120); infix("//", 120)
infix("%", 120)

prefix("-", 130); prefix("+", 130); prefix("~", 130)

infix_r("**", 140)

symbol(".", 150); symbol("[", 150); symbol("(", 150)
symbol(")")
symbol("say", 160)

def nud(self):
    sentence = []
    while 1:
        try:
            token = expression()
            sentence.append( token.value )
        
        except:
            break
    self.value = " ".join(sentence)
    return self
symbol("say").nud = nud



def led(self, left):
    if token.id != "(name)":
        raise SyntaxError("%s is not an attribute of %s" % (token.id, left.id))
    self.first = left
    self.second = token
    advance()
    return self
symbol(".").led = led

def nud(self):
    expr = expression()
    advance(")")
    return expr
symbol("(").nud = nud

def led(self, left):
    self.first = left
    self.second = expression()
    advance("else")
    self.third = expression()
    return self
symbol("if").led = led

class int_literal:
    def __init__(self, val):
        self.value = int(val)
    def nud(self):
        return self.value
    def __repr__(self):
        return "(literal %d)" % self.value
    
    
class string_literal:
    def __init__(self, val):
        self.value = val
    def nud(self):
        return self.value
    def __repr__(self):
        return "(literal %s)" % self.value
    
class operator_add_token:
    lbp = 10
    def nud(self):
        self.first = expression(100)
        self.second = None
        # return self.first
        return self
    def led(self,left):
        self.first = left
        self.second = expression(10)
        #return self.first + self.second
        return self
    def __repr__(self):
        return "(add %s %s)" % (self.first, self.second)
        
        
class operator_sub_token:
    lbp = 10
    def nud(self):
        return -expression(100)
    def led(self, left):
        return left - expression(10)
    
class operator_mul_token:
    lbp = 20
    def led(self, left):
        self.first = left
        self.second = expression(20)
        return self
        #return self.first * self.second
    def __repr__(self):
        return "(mul %s %s)" % (self.first, self.second)
    
class operator_div_token:
    lbp = 20
    def led(self, left):
        return left / expression(20)
    
class operator_pow_token:
    lbp = 30
    def led(self, left):
        return left ** expression(30-1)
    
class end_token:
    lbp = 0
    
token_pat = re.compile("\s*(?:(\d+)|(\*\*|.))")

#def tokenize(program):
#    for number, operator in token_pat.findall(program):
#        if number:
#            yield int_literal(number)
#        elif operator == "+":
#            yield operator_add_token()
#        elif operator == "-":
#            yield operator_sub_token()
#        elif operator == "*":
#            yield operator_mul_token()
#        elif operator == "/":
#            yield operator_div_token()
#        elif operator == "**":
#            yield operator_pow_token()
#        else:
#            raise SyntaxError("unknown operator")
#    yield end_token()
    
def parse(program):
    global token, next
    next = tokenize(program).next
    token = next()
    return expression()

print parse("1 + 2")
print parse("1 + 5 + 10")
print parse("1+2-3*4/5")
print parse("1+2*3")
print parse("1.0*2+3")
print parse("'hello'+'world'")
print parse("2<<3")
print parse("(1+2)*3")
print parse("1 if 2 else 3")
print parse("foo.bar")
print parse("say You Bunch of Lilly Livered Cowards!")