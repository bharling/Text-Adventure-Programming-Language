import tpg


def make_op(s):
    return {
            '+': lambda x,y : x+y,
            '-': lambda x,y : x-y,
            '*': lambda x,y : x*y,
            '/': lambda x,y : x/y
            }[s]

class Calc(tpg.Parser):
    r"""
    
    separator spaces: '\s+' ;
    token number: '\d+' int ;
    token add: '[+-]' make_op ;
    token mul: '[*/]' make_op ;
    
    START/e -> Term/e ;
    Term/t -> Fact/t ( add/op Fact/f $t=op(t,f)$ )* ;
    Fact/f -> Atom/f ( mul/op Atom/a $f=op(f,a)$ )* ;
    Atom/a -> number/a | '\(' Term/a '\)' ;
    """
    
    
calc = Calc()
expr = raw_input(":> ")
print expr, '=', calc(expr)
    
    