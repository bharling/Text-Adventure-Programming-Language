'''
Created on 8 Feb 2012

@author: Hens
'''

'''

IMPLEMENT THIS AS THE PARSER FOR ITEMS IN THE GAME
AND POSSIBLY GAME COMMANDS THEMSELVES

http://effbot.org/zone/simple-top-down-parsing.htm

'''

import re

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

class int_literal_token:
    def __init__(self, value):
        self.value = int(value)
    def nud(self):
        return self.value
    
class operator_add_token:
    lbp = 10
    def led(self, left):
        right = expression(10)
        return left + right
    
class operator_sub_token:
    lbp = 10
    def led(self, left):
        return left - expression(10)
    
class operator_mul_token:
    lbp = 20
    def led(self, left):
        return left * expression(20)
    
class operator_div_token:
    lbp = 20
    def led(self, left):
        return left / expression(20)
    
class end_token:
    lbp = 0
    
token_pat = re.compile("\s*(?:(\d+)|(.))")

def tokenize(program):
    for number, operator in token_pat.findall(program):
        if number:
            yield int_literal_token(number)
        elif operator == "+":
            yield operator_add_token()
        elif operator == "*":
            yield operator_mul_token()
        elif operator == "/":
            yield operator_div_token()
        elif operator == "-":
            yield operator_sub_token()
        else:
            raise SyntaxError("unknown operator")
    yield end_token()
    
def parse(program):
    global token, next
    next = tokenize(program).next
    token = next()
    return expression()

print parse("1 + 2")
print parse("1 + 2 / 3 + 20 - 10 * 6")
    

        