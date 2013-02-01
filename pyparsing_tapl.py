import pyparsing as pp

class Command(object):
    def __init__(self, verb, verbProg):
        self.verb = verb
        self.verbProg = verbProg
       
    def _doCommand(self, player):
        pass 
    
    def __call__(self, player):
        print self.verbProg.capitalize()+"..."
        self._doCommand(player)
        
def LookCommand(Command):
    def __init__(self, quals):
        super(LookCommand,self).__init__("LOOK", "looking")
        
    def _doCommand(self, player):
        player.room.describe()



class Parser(object):
    def __init__(self):
        self.bnf = self.makeBNF()
        
    def validateItemName(self,s,l,t):
        iname = " ".join(t)
        return iname
        
    def makeBNF(self):
        verbInventory = pp.oneOf("INV INVENTORY I", caseless=True)
        verbSay = pp.oneOf("SAY >", caseless=True)
        verbLook = pp.oneOf("LOOK L", caseless=True)
        verbExamine = pp.oneOf("EXAMINE EX", caseless=True)
        
        itemRef = pp.OneOrMore(pp.Word(pp.alphas)).setParseAction(self.findItem)
                                                                  
        commandInventory = verbInventory
        commandExamine = verbExamine + itemRef.setResultsName("item")        
        commandSay = verbSay
        commandLook = verbLook
        
        commandInventory.setParseAction(self.makeCommandParseAction( InventoryCommand ))
        commandExamine.setParseAction(self.makeCommandParseAction( ExamineCommand ))
        commandSay.setParseAction(self.makeCommandParseAction( SayCommand ))
        commandLook.setParseAction(self.makeCommandParseAction( LookCommand )) 
        
        return ( commandInventory | commandExamine | commandSay | commandLook  ).setResultsName("command") + pp.LineEnd()
        