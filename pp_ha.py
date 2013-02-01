import pyparsing as PP
PP.ParserElement.enablePackrat()

Farthest = None

compOperators = {"<":lambda x, y: x < y,
                 ">":lambda x, y: x > y,
                 "<=":lambda x, y: x <= y,
                 ">=":lambda x, y: x >= y,
                 "==":lambda x, y: x == y,
                 "!=":lambda x, y: x != y
                 }

mathOperators = {"+":lambda x, y: x + y,
                 "-":lambda x, y: x - y,
                 "*":lambda x, y: x * y,
                 "/":lambda x, y: x / y,
                 "%":lambda x, y: x % y
                 }


def FindRowCol(Text, Pos):
    Lines = Text[:Pos].split("\n")
    return len(Lines), len(Lines[-1]) + 1

def SPA(Template, Klass):
    Klass.Template = Template
    Template.setParseAction(Klass)
    return Template

def Literal(String):
    Template = PP.Literal(String)
    Klass = type("Literal", (BaseObj,), {"Template": Template})
    return Template.setParseAction(Klass)

class BaseObj(object):
    def __init__(self, Str, Pos, Tokens):
        global Farthest
        self.Str, self.Pos, self.Tokens = Str, Pos, Tokens
        if not Farthest or (Pos > Farthest.Pos):
            Farthest = self
        for Token in Tokens:
            if isinstance(Token, BaseObj):
                Token.Parent = self

class IdentClass(BaseObj): pass
class IntegerClass(BaseObj): pass
class AssignClass(BaseObj): pass
class CompareClass(BaseObj): pass
class BlockClass(BaseObj): pass
class ForCmdClass(BaseObj): pass
class IfCmdClass(BaseObj): pass
class SymbolClass(BaseObj): pass
class AnythingClass(BaseObj): pass

AddOps    = PP.oneOf("+ -")
MulOps    = PP.oneOf("* /")
LParen    = Literal("(")
RParen    = Literal(")")
Semi      = Literal(";")
Ident     = SPA(PP.Word(PP.alphas, PP.alphanums + "_"), IdentClass)
Integer   = SPA(PP.Word(PP.nums), IntegerClass)
Assign    = SPA(Ident + Literal("=") + Integer, AssignClass)
Compare   = SPA(Ident + PP.oneOf("< > <= >= == !=") + Integer, CompareClass)
Statement = PP.Forward()
Block     = SPA(Literal("{") + PP.OneOrMore(Statement) + Literal("}"),
    BlockClass)
ForCmd    = SPA(Literal("for") + LParen + Assign + Semi + Compare + Semi + \
    Assign + RParen + Statement, ForCmdClass)
IfCmd     = SPA(Literal("if") + LParen + Compare + RParen + \
                PP.Suppress("{") + Statement + PP.Suppress("}") + \
                PP.Optional(Literal("else") + PP.Suppress("{") + Statement + PP.Suppress("}")), IfCmdClass)
AssignCmd = Assign + Semi
Statement << (Block | ForCmd | IfCmd | AssignCmd)
Program = PP.OneOrMore(Statement) + PP.StringEnd()
Program.ignore("//" + PP.restOfLine)
Program.ignore(PP.cStyleComment)

# NextThing is used to find whatever follows an error
Symbol = SPA(PP.Regex("\\S"), SymbolClass)
Anything = PP.Empty().suppress()
Gap = PP.Optional(PP.White()).suppress()
NextThing = Gap + (Ident | Integer | Symbol | Anything)

Code = """
a=5;
for (i = 5; i < 10; i = 7)
{
    c=9;

    if (a < 6) 
    {
        a = 6;
    }
    else
    {
        b = 9;
    }
}
x = 5;
"""

try:
    X = Program.parseString(Code)
except PP.ParseException:
    # The parse failed. Find the last thing we did parse successfully.
    FarPos = Farthest.Pos
    SubStr = Code[FarPos:]
    # Reparse this segment to find out what follows.
    Parser = Farthest.Template + NextThing
    Parser.ignore("//" + PP.restOfLine)
    Parser.ignore(PP.cStyleComment)
    NextObj = Parser.parseString(SubStr)[-1]
    ErrPos, NextStr = FarPos + NextObj.Pos, NextObj.Tokens[-1]
    Row, Col = FindRowCol(Code, ErrPos)
    print "Parse error: did not expect %r on line %d (column %d)" % (NextStr,
        Row, Col)