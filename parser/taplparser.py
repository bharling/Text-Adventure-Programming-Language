'''
Created on 22 Feb 2012

@author: bharling
'''

import ast
import sys
import os
import imp
import marshal
from optparse import OptionParser
import re







gameCommands = {
                'help' : 'get help',
                'say' : "say something to all occupants in the room you're in",
                'examine' : 'examine an item',
                'go' : 'go somewhere',
                'shout' : 'say to all users in the current world',
                'take' : 'pick up an item in the current location',
                'drop' : 'drop an item in your inventory in the current room',
                'tell' : 'message a specific user - syntax = tell Norman Granger: some message',
                'use' : 'try to use an item',
                'give' : 'give an item to a user, syntax = give Norman Granger: sword',
                'inventory' : 'show all items you are carrying',
                'print_state' : 'show all variables defined in the current scope',
                'warp' : 'warp to a different world',
                'look': 'see what is around you',
                'list_worlds' : 'show a list of all the worlds running on the current server',
                'download_world' : 'save the current world and make it available to download',
                'save_world': 'save the current world',
                'who': 'list users in the current room'
                }


TOK_IDENT = "<id>"
TOK_STR   = "<str>"
TOK_NUM   = "<num>"
_KEYWORDS = []
def keyword(s):
    _KEYWORDS.append(s)
    return s

# game commands
TOK_SAY = keyword("say")
TOK_EXAMINE = keyword('examine')
TOK_LOOK = keyword('look')
TOK_HELP = keyword('help')
TOK_SHOUT = keyword('shout')
TOK_TAKE = keyword('take')
TOK_DROP = keyword('drop')
TOK_TELL = keyword('tell')
TOK_USE = keyword('use')
TOK_GIVE = keyword('give')
TOK_INV = keyword('inventory')
TOK_STACK = keyword('print_state')
TOK_WARP = keyword('warp')
TOK_WHO = keyword('who')

# const references
TOK_ME = keyword('@me')
TOK_HERE = keyword('@here')

# item function types
TOK_THISITEM = keyword('@this')
TOK_EVENT = keyword('@event')

# language constructs
TOK_IF  = keyword("if")
TOK_ELSE   = keyword("else")
TOK_TRUE = keyword("true")
TOK_FALSE = keyword("false")
TOK_NULL   = keyword("null")

#TOK_IMPORT = keyword("import")
#TOK_IF  = keyword("if")
#TOK_ELSE   = keyword("else")
#TOK_TRUE = keyword("true")
#TOK_FALSE = keyword("false")
#TOK_DEF   = keyword("def")
#TOK_RETURN = keyword("return")
#TOK_NULL   = keyword("null")


def readwhile(s, i, pred):
    buf = ""
    while i < len(s) and pred(s[i]):
        buf += s[i]
        i += 1
    return i, buf

def error(s):
    print >>sys.stderr, s
    sys.exit(1)

class Scanner(object):
    def __init__(self):
        object.__init__(self)

    def scan(self, s):
        i = 0
        tokens = []
        while i < len(s):
            #
            # [a-zA-Z_] -> start of an identifier or a keyword
            #
            if s[i].isalpha() or s[i] == '_' or s[i] == '@':
                def isidentchar(c):
                    return c.isalpha() or c.isdigit() or c == '_' or c == '@'
                i, sval = readwhile(s, i, isidentchar)
                if sval in _KEYWORDS:
                    tokens.append((sval, None))
                else:
                    tokens.append((TOK_IDENT, sval))
            #
            # [0-9] -> start of a number
            #
            elif s[i].isdigit():
                i, sval = readwhile(s, i, lambda c: c.isdigit())
                tokens.append((TOK_NUM, sval))
            #
            # " -> start of a string
            #
            elif s[i] == '"':
                i += 1
                i, sval = readwhile(s, i, lambda c: c != '"')
                i += 1
                tokens.append((TOK_STR, sval))
            #
            # [\(\);,.{}\[\]=] -> special characters
            #
            elif s[i] in ('(', ')', ';', ',', '.', '{', '}', '[', ']', '='):
                tokens.append((s[i], None))
                i += 1
            #
            # [ \t\r\n] -> skip whitespace
            #
            elif s[i] in (' ', "\t", "\r", "\n"):
                i += 1
            #
            # # -> comment
            #
            elif s[i] == '#':
                while s[i] != "\n": i += 1
                i += 1
            #
            # Everything else -> error
            #
            else:
                error("unexpected token: %s" % s[i])

        return tuple(tokens)

input = 'say hello you buggers'
print Scanner().scan(input)
input = 'examine patchwork quilt'
print Scanner().scan(input)
input = '@me.describe("willy wonka")'
print Scanner().scan(input)