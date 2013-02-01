'''
Created on 8 Feb 2012

@author: Hens
'''

import cStringIO, tokenize

def atom(next, token):
    if token[1] == "(":
        out = []
        token = next()
        while token[1] != ")":
            out.append(atom(next, token))
            token = next()
            if token[1] == ",":
                token = next()
        return tuple(out)
    elif token[0] is tokenize.STRING:
        return token[1][1:-1].decode("string-escape")
    elif token[0] is tokenize.NUMBER:
        try:
            return int(token[1], 0)
        except ValueError:
            return float(token[1])
    raise SyntaxError("Malformed expression (%s)" % token[1])

def simple_eval(source):
    src=cStringIO.StringIO(source).readline
    src = tokenize.generate_tokens(src)
    return atom(src.next, src.next())

if __name__=="__main__":
    print simple_eval("'hello'")
    print simple_eval("1, 34")
