'''
Created on 4 Feb 2012
@author: Hens
'''

import math

import socket
import threading
import thread
from exceptions import ValueError
from difflib import get_close_matches, SequenceMatcher
import pickle

import string
import os

import copy


class SpecialBadge(object):
    def __init__(self, badgeTitle, grantsFunctionName, rewardDescription):
        self.title = badgeTitle
        self.functionGranted = grantsFunctionName
        self.description = rewardDescription
        
        
def aOrAn(name):
    if name[0] in "aeiou":
        return "an"
    return "a"




SPACE_CREATE_BADGES = {3:"Novice Bricklayer",
                       8:"Apprentice Builder",
                       16:"Builders Mate",
                       24:"Professional Builder",
                       48:SpecialBadge("Experienced Professional Builder", 
                                       "copySpace", 
                                       """Use copySpace to create copies of spaces you've already made, 
                                          including items they contain.\n\nusage: @me.copySpace(dirIn, dirBack, space)"""),
                       70:"Master Builder",
                       100:"Architect Novice",
                       130:"Architect Apprentice",
                       160:"Architect",
                       200:SpecialBadge("Expert Architect",
                                        "destroySpace",
                                        """Use destroySpace to completely remove a space that you have created. All 
                                        items inside are destroyed, and players are moved randomly to adjacent spaces,
                                        possibly resulting in them being cut off from the rest of the world!"""),
                       240:"Master Architect",
                       300:SpecialBadge("Master Architect of Creation",
                                        "createArea",
                                        """Grants the ability to create multiple spaces in a single command""")
                       }

EXPLORATION_BADGES = {5:"Traveller",
                      15:"Journeyman",
                      30:"Interested Explorer",
                      50:"Weary Explorer",
                      80:"Experienced Explorer",
                      120:"Reknowned Explorer",
                      160:"Great Explorer",
                      200:"Legendary Explorer"
                      }

ITEM_CREATION_BADGES = {5:"Amateur Tinkerer",
                        20:"Novice Item Maker",
                        40:"Adept Item Maker",
                        70:"Artisan",
                        110:"Master Artisan"
                        }

welcome = '''
            <div id='game_welcome'>
            <h1>==[ Text Adventure Programming Language ]==</h1>

            Welcome to the text adventure programming
            language. Please read the documentation to
            learn how to start creating your own worlds
            to enjoy with friends.
            <hr/><br/>
            </div>

'''


class GameEvent(object):
    def __init__(self, eventType, target, *args):
        self.type = eventType
        self.target = target
        self.args = args
        
class PlayerEvent(GameEvent):
    PLAYER_ENTERED = "player_entered"
    PLAYER_LEFT = "player_left"
    PLAYER_CREATED_ITEM = "player_created_item"
    PLAYER_SAID = "player_said"
    PLAYER_CREATED_WORLD = "player_created_world"
    PLAYER_CHANGED_NAME = "player_changed_name"
    PLAYER_EMOTE = "player_emote"
    PLAYER_SHOUTED = "player_shouted"
    
class WorldEvent(GameEvent):
    SUNDOWN = "sundown"
    SUNRISE = "sunrise"


class SocketForwarder(threading.Thread):
    def __init__(self, host, port_in, port_out):
        threading.Thread.__init__(self)
        self.sock = None
        
    def run(self):
        pass


#gameCommands =[ 'help', 'say', 'examine', 'go', 'shout', 'take', 'drop', 'tell', 'use', 'look', 'give', 'inventory' ,'print_state', "warp", "list_worlds", "download_world", "save_world", "who"]

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

shortcuts = {'>':'say'}

def closestMatchItem(u, sequence):
        items = [i._name for i in sequence]
        #result = min(_items, key=lambda v: len(set(u) ^ set(v)))
        result = get_close_matches(u, items, 1, 0.4)
        if len(result)<1:
            return "[NO MATCH]"
        
        return result[0]
    
def closestMatchString(u,sequence):
    result = get_close_matches(u, sequence, 1, 0.4)
    if len(result)<1:
        return "[NO MATCH]"
        
    return result[0]

class Player(object):
    def __init__(self, name, conn, addr):
        self._name=name
        self._handler = conn
        #self._handler.send(welcome)
        self._health = 100
        self._inventory = []
        self._emotes = {}
        self._description = ""
        self._sneaking = False
        self._currentLocation = None
        self._joined = False
        self._avatar = "http://www.gravatar.com/avatar/00000000000000000000000000000000?d=mm&f=y"
        self._email = ""
        self._password = ""
        self._userName = ""
        self._creationStage = 0
        self._loginStage = 0
        self._title = "Greenling"
        #self._handler = None
        
    def __repr__(self):
        return "[Player - %s, %s]" % (self._name, self._title)
    
    
    def _setTitle(self, title):
        self._title = title
        self._message_confirmation("Your title is set to %s" % title)
        self._currentLocation._fireEvent(PlayerEvent(PlayerEvent.PLAYER_SAID, self, "changed their title to %s" % title))
    
    def _save(self, arg=None):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        valid_name = ''.join(c for c in self._userName if c in valid_chars) + ".taplPlayer"
        print "SAVING PLAYER:", valid_name
        return TAPL()._savePlayer(self, valid_name)
        self._creationStage = 4
        #obj = pickle.dumps(self)
        #f = open(os.path.join(os.path.abspath(os.curdir), valid_name), "w")
        #f.write(obj)
        #f.close()
    
    def save(self, player=None):
        '''
        Save your character.
        If you have not saved before,
        you can set a user name and
        password to load the character
        later on.
        '''
        
        if self._loginStage == 3:
            self._save(None)
            return
        self._creationStage = 1
        self._message_notification("Please choose a user name")
    
    def _message_notification(self,message):
        html = "<div class='notification'><p>%s</p></div>" % message
        if self._handler:
            self._handler.sendMessage(html)
    
    def _message_alert(self,message):
        html = "<div class='alert'><p>%s</p></div>" % message
        if self._handler:
            self._handler.sendMessage(html)
    
    
    
    def _message_confirmation(self, message):
        html = "<div class='confirmation'><img src='/images/tick.png' align='left'><p>%s</p></div>" % message
        if self._handler:
            self._handler.sendMessage(html)
    
    
    def emote(self, player, trigger, action):
        '''
        Add an emote to your character.
        
        @param trigger: the command you want to assign for
                        the emote
                        
        @param action: the action as you want it to appear
                        in the world.
        
        Example:
        @me.emote("slap", "bitch slaps")
        
        >>slap ryan
        Norman bitch slaps Ryan
        '''
        self._emotes[trigger] = action
        self._message_confirmation("Emote '%s' set." % trigger)
        return self
    
    def setAvatar(self, player, avatarUrl):
        '''
        Set an image for your character
        @param url: The URL to an image to display
        '''  
        self._avatar = avatarUrl
        self._message_confirmation("Your avatar has changed to<br/><img src='%s'/>" % avatarUrl)
        return self
        
    def _joinGame(self):
        self._joined = True
        self._handler.sendMessage(welcome)
        
    def say(self, player, message):
        '''
        Say something to everyone in your current location
        
        aliases:
        @me.say("Something")
        say Something
        >something
        
        '''
        
        if self._currentLocation:
            self._currentLocation._fireEvent(PlayerEvent( PlayerEvent.PLAYER_SAID, self, message))
            #self._message_notification("You say, " + message)
            
    def shout(self, player, message):
        '''
        shout something to everyone in your current location
        
        aliases:
        @me.shout("Something")
        shout Something
        
        '''
        if self._currentLocation:
            self._currentLocation._fireEvent(PlayerEvent( PlayerEvent.PLAYER_SHOUTED, self, message))
        
    def _setHandler(self, handler):
        self._handler = handler
        #self._handler.send(welcome)

    def _setLocation(self, location):
        if self._currentLocation:
            if self in self._currentLocation._occupants:
                self._currentLocation._occupants.remove(self)
            self._currentLocation._fireEvent( PlayerEvent( PlayerEvent.PLAYER_LEFT, self ) )
        self._currentLocation = location
        if self not in location._occupants:
            location._occupants.append(self)
        location._fireEvent( PlayerEvent( PlayerEvent.PLAYER_ENTERED, self ))
        if self._handler and self._joined:
            self._message_notification("You are in " + self._currentLocation._name)
        return self
    
    def setName(self, player, name):
        '''
        Change your display name.
        
        @param name: Your new chosen name
        ''' 
        oldname = self._name
        self._name = name
        if self._currentLocation:
            self._currentLocation._fireEvent( PlayerEvent( PlayerEvent.PLAYER_CHANGED_NAME, self, name, oldname))
        self._message_confirmation("Your name has changed to " + name)
        return self;
    
    def describe(self, player, description):
        '''
        Give yourself a description
        
        @param description: the description you want others to see
        @return: The Player
        '''
         
        self._description = description
        self._message_confirmation("You are now described as ")
        return self;
    
    def createItem(self, player, name):
        '''
        Create an item and add it straight to your inventory
        
        @me.createItem("A new Item")
        
        @param name: name of the item
        @return: The newly created Item
        ''' 
        item = Item(name)
        self._inventory.append(item)
        if self._currentLocation:
            self._currentLocation._fireEvent(PlayerEvent( PlayerEvent.PLAYER_CREATED_ITEM, self, item ))
        self._message_confirmation("Item created")
        return item
    
    def addItem(self, player, item):
        '''
        Not yet implemented!
        '''
        self._inventory.append(item)
        return self
    
    def removeItem(self, player, item):
        '''
        Not yet implemented!
        '''
        if item in self._inventory:
            self._inventory.remove(item)
        return self
    
    def getItem(self, itemName):
        '''
        Not yet implemented!
        '''
        match = closestMatchItem(itemName, self._inventory)
        #print "[----------" + str(self._inventory)
        if match != "[NO MATCH]":
            for i in self._inventory:
                if i._name == itemName:
                    return i
        return "You Aren't carrying a " + itemName

    def createWorld(self, player, name):
        '''
        Create an entirely new world
        and warp to the entrance room in that
        world
        
        @param name: The name of the new world
        @return: The newly created world object
        ''' 
        w = World(name)
        TAPL().addWorld(w)
        if self._currentLocation:
            self._currentLocation._fireEvent(PlayerEvent(PlayerEvent.PLAYER_CREATED_WORLD, self, w))
            self._currentLocation._fireEvent(PlayerEvent(PlayerEvent.PLAYER_LEFT, self ))
        self._setLocation(w.spaces[0])
        return w
         
class PortalDoorway(object):
    def __init__(self, portal, space, direction):
        # direction is the way this door goes ( eg 'E', 'SE' )
        self.space = space
        self.direction = direction
        self.portal
        
def getCompassOpposite(direction):
    d = direction.lower();
    if d == "n":
        return "s"
    if d == "ne":
        return "sw"
    if d == "e":
        return "w"
    if d == "se":
        return "nw"
    if d == "s":
        return "n"
    if d == "sw":
        return "ne"
    if d == "w":
        return "e"
    if d == "nw":
        return "se"
    return "n"
        

class Portal(object):
    def __init__(self,dirIn,dirOut,spaceOne,spaceTwo,name="door"):
        self._name = name
        self.spaceOne = spaceOne
        self.spaceTwo = spaceTwo
        self.dirIn = dirIn
        self.dirOut = dirOut
        self.shortDirIn = ""
        self.shortDirOut = ""
        if dirIn.find("[") > -1 and dirIn.find("]") > -1:
            self.shortDirIn = dirIn[dirIn.find("[")+1:dirIn.find("]")]
            self.dirIn = self.dirIn[self.dirIn.find("]")+1:]
        if not len(self.shortDirIn) : self.shortDirIn = dirIn[0:1]
        if dirOut.find("[") > -1 and dirOut.find("]") > -1:
            self.shortDirOut = dirOut[dirOut.find("[")+1:dirOut.find("]")]
            self.dirOut = self.dirOut[self.dirOut.find("]")+1:]
        if not len(self.shortDirOut) : self.shortDirOut = dirOut[0:1]
        
    def addExit(self, doorway):
        if len(self.doorways) < 2:
            if self.doorways[0] != doorway:
                self.doorways.append(doorway)
        
    def setName(self, player, name):
        self._name = name
        return self

    def describe(self, player, description):
        self._description = description
        return self

class Space(object):
    def __init__(self, name):
        self._name = name
        self._description = "";
        self._items = []
        self._portals = []
        self._occupants = []
        self._world = None
        
    def __repr__(self):
        return "[SPACE: %s]" % self._name
        
    def _fireEvent(self, event):
        self._propagateEvent(event)
        if event.type == PlayerEvent.PLAYER_ENTERED:
            msg = event.target._name + " entered."
            self._messageOccupants(msg, event.target)
            return
        if event.type == PlayerEvent.PLAYER_LEFT:
            msg = event.target._name + " left."
            self._messageOccupants(msg, event.target)
            return
        if event.type == PlayerEvent.PLAYER_SAID:
            msg = event.args[0]
            self._occupantSaid(msg, event.target)
            return
        if event.type == PlayerEvent.PLAYER_SHOUTED:
            self._occupantSaid("<h2>" + event.args[0] + "</h2>", event.target)
        if event.type == PlayerEvent.PLAYER_CREATED_ITEM:
            msg = event.target._name + " created a " + event.args[0]._name
            self._messageOccupants(msg, event.target)
            return
        if event.type == PlayerEvent.PLAYER_CHANGED_NAME:
            msg = event.args[1] + " changed their _name to " + event.args[0]
            self._messageOccupants(msg, event.target)
            return
        if event.type == PlayerEvent.PLAYER_EMOTE:
            msg = event.args[0]
            self._messageOccupants(msg, event.target)
        
    def _propagateEvent(self, event):
        for i in self._items:
            if i.eventHandlers.has_key(event.type):
                self._messagePlayer(event.target, i.eventHandlers[event.type])
                
    def _messagePlayer(self, target, message):
        if isinstance(target, Player):
            if target._joined:
                target._message_notification(message)
        
    
    def _messageOccupants(self, msg, originator):
        for o in self._occupants:
            if o._handler and o is not originator:
                o._message_notification(msg)
                
    def _occupantSaid(self, msg, originator):
        message = """<div class='speech'><p>
                        <img src='%s' align='left' /><br/>
                        <span class='player_name'>%s</span><br/>
                        <span class='player_title'>%s</span>
                        </p>
                        <p>
                        <span>%s</span>
                        </p>
                        </div>""" % (originator._avatar,
                                     originator._name,
                                     originator._title,
                                     msg)
        for o in self._occupants:
            if o._joined:
                o._handler.sendMessage(message)
        

    def _setWorld( self, world ):
        self._world = world
        if not self in world.spaces:
            world.spaces.append(self)
        return self
        
    def setName(self, player, name):
        '''
        Set the name for this space
        
        @param name: the new name
        @return: the Space
        '''
         
        self._name = name
        player._message_confirmation("Done")
        self._messageOccupants("%s changed the name of this location to %s." % ( player._name, name ), player)
        return self;
    
    def describe(self, player, description):
        '''
        Set the description for this space
        
        @param description: The new description
        '''
         
        self._description = description
        player._message_confirmation("Done")
        self._messageOccupants("%s changed the description of this location to %s." % ( player._name, description ), player)
        return self;
    
    def createItem(self, player, name):
        '''
        Create a new item in this location
        
        @param name: the name for the item
        @return: The new item
        '''
         
        item = Item(name)
        player._message_confirmation("Done")
        self._messageOccupants("%s created a %s." % ( player._name, name ), player)
        self._items.append(item)
        return item
    
    def addItem(self, player, item):
        self._items.append(item)
        return self
    
    def removeItem(self, player, item):
        if item in self._items:
            self._items.remove(item)
        return self
    
    def _getPossibleDirections(self):
        directions = []
        for p in self._portals:
            if p.spaceOne == self:
                directions.append(p.dirIn)
                directions.append(p.shortDirIn)
            else:
                directions.append(p.dirOut)
                directions.append(p.shortDirOut)
        return directions
    
    def _goPortal(self, name):
        destination = self
        via = ""
        for p in self._portals:
            if p.direction == name:
                via = p._name
                if p.start._name == self._name:
                    destination = p.end
                else:
                    destination = p.start
                break
        #print "you travel to", destination._name, "via", via
        return destination

    def dig(self, player, directionIn, directionOut, roomName, portalName = "door"):
        '''
        Create a tunnel to a new location ( also creates the new space at the same time )
        
        @param directionIn: the direction of the room
        @param directionBack: the direction BACK to this room
        @param roomName: the name of the new room
        @param portalName: [OPTIONAL] the name of the portal, defaults to "door"
        '''
        r = Space( roomName )
        r._setWorld(self._world)
        p = Portal( directionIn, directionOut, self, r, portalName )
        r._portals.append(p)
        self._messageOccupants("%s created a %s leading %s to %s" % ( player._name, portalName, directionOut, roomName ), player)
        player._message_confirmation("Done")
        self._portals.append( p )
        return r
        
            
        
    
    
class World(object):
    def __init__(self, name="DefaultWorld"):
        self.name = name
        basePlayer = Player("DefualtPlayer", None, None)
        self.spaces = [Space("The Entrance Hall").describe(basePlayer, "An empty, blank room")]
        self.spaces[0]._setWorld(self)
        self._items = []
        self.npcs = []
        self.players = []
        self._currentLocation = None;
        self.defaultLocation = self.spaces[0]
        
    def download(self, player):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        valid_name = ''.join(c for c in self.name if c in valid_chars) + ".taplWorld"
        print "saving " + valid_name
        dup = copy.deepcopy(self)
        
        # delete the player objects from this copy
        for s in dup.spaces:
            s._occupants = []
        
        f=open(os.path.join(os.path.abspath(os.curdir), "static", "worlds", valid_name), 'wb')
        pickle.dump(dup, f, -1)
        f.close()
        player._message_confirmation("Click <a href='%s' target='_blank'>Here</a> to download the world" % (TAPL().getHostName() + "/worlds/" + valid_name))
        #player._handler.offerFile(os.path.join(os.path.abspath(os.curdir), valid_name))
        return "Downloading world from %s" % (TAPL().getHostName() + "/worlds/" + valid_name)
        
    
    def createItem(self, player, name):
        item = Item( name )
        self._items.append(item)
        return item

    def save(self, player):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        valid_name = ''.join(c for c in self.name if c in valid_chars) + ".taplWorld"
        print "saving " + valid_name
        dup = copy.deepcopy(self)
        
        # delete the player objects from this copy
        for s in dup.spaces:
            s._occupants = []
        
        f=open(os.path.join(os.path.abspath(os.curdir), valid_name), 'w')
        f.write(pickle.dumps(dup))
        f.close()
        return "World saved as '" + valid_name + "'"

    def load(self, player, filename):
        try:
            f=open(filename, "r")
            world = pickle.reads(f.read())
            return world
        except:
            return "Cannot load world!"

    def getWorlds(self, player=None):
        worlds = "Available worlds on this server:\n" + "\n".join([w.name for w in TAPL().worlds])
        return worlds
        
    def createSpace(self, player, name):
        space = Space(name)
        self.spaces.append(space)
        return space
    
    def setCurrentLocation(self,spaceName):
        #print "Setting Location", spaceName
        if type( spaceName ) == Space:
            self._currentLocation=spaceName
            return
        for s in self.spaces:
            if s._name == spaceName:
                self._currentLocation = s
                return

    def setEntrance( self, space ):
        self.defaultLocation = space
        return self
        
    
class Item:
    def __init__(self, name):
        self._name = name
        self._description = ""
        self.alias = ""
        self.verbs = {}
        self.props = {}
        self.eventHandlers = {}
        self.contents = []
        self.openable = False
        
    def __repr__(self):
        return "[ ITEM: %s ]" % self._name
        
        
    def putInside(self, player, container):
        if isinstance(container, Item):
            container.contents.append(self)
            container.openable = True
            
    def removeItem(self, player, item):
        pass
    
    def notify(self, player, eventName, response):
        self.eventHandlers[eventName] = response
        return self
        
    def describe(self, player, description):
        self._description = description
        return self
    
    def setAlias(self, player, alias):
        self.alias = alias
        return self
        
    def verb(self, player, verbName, response, item=None):
        self.verbs[verbName] = response
        return self
    
    def setProp(self, player, propName, propValue):
        self.props[propName]=propValue
        return self
        
    def getProp(self, player, propName):
        if self.props.has_key(propName):
            return self.props[propName]
        return "Error: No property named: " + propName + " on "
        
class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance

##get auto complete arrays
p = Player("Nob", None, None)
PlayerCommands = ["@me." + i for i in dir(p) if not (i.startswith("_"))]
PlayerDocs = []
AllDocs = {}
for i in dir(p):
    if not i.startswith("_"):
        AllDocs["@me." + i] = getattr(p, i).__doc__
        
AllDocs.update(gameCommands)
    
    
itm = Item("TestItem")
ItemCommands = [i for i in dir(itm) if not (i.startswith("_"))]
ItemDocs = []
for i in dir(itm):
    if not i.startswith("_"):
        AllDocs[i] = getattr(itm, i).__doc__
#ItemDocs = map( lambda x : (x[0], "") if x[1] == None else x, ItemDocs )

spc = Space("TestSpace")
SpaceCommands = [ "@here." + i for i in dir(spc) if not (i.startswith("_"))]
SpaceDocs = []
for i in dir(spc):
    if not i.startswith("_"):
        AllDocs["@here." + i] = getattr(spc, i).__doc__
#SpaceDocs = map( lambda x : (x[0], "") if x[1] == None else x, SpaceDocs )

wrld = World("TestWorld")
WorldCommands = ["@world." + i for i in dir(wrld) if not (i.startswith("_"))]
WorldDocs = []
for i in dir(wrld):
    if not i.startswith("_"):
        AllDocs["@world." + i] = getattr(wrld, i).__doc__
#WorldDocs = map( lambda x : (x[0], "") if x[1] == None else x, WorldDocs )

print SpaceCommands
#AllDocs = map( lambda x : (x[0], "") if x[1] == None else x, AllDocs )

class TAPL(object):
    '''
    classdocs
    '''

    __metaclass__ = Singleton
    
    def jsonArray(self, array):
        return "[" + ",".join(['{ "id" : "%s", "label" : "%s", "value" : "%s" }' % ( i, i, i ) for i in array]) + "]"
    
    def getAutoComplete(self, val):
        
        ret = []
        if val.find(".") > -1:
            precedent = val[0:val.index(".")]
            if precedent == "@me":
                return self.jsonArray([i for i in PlayerCommands if i.startswith(val)])
            elif precedent == "@here":
                return self.jsonArray([i for i in SpaceCommands if i.startswith(val)])
            elif precedent == "@world":
                return self.jsonArray([i for i in WorldCommands if i.startswith(val)])
            else:
                # here we need to search in the current namespace for items
                return self.getContextAutoComplete(precedent, val)
        elif val[0] == "@":
            return self.jsonArray(["@me", "@here", "@world"])
        coms = [g for g in gameCommands.keys() if g.startswith(val)]
        if len(coms):
            return self.jsonArray(coms)
        return '[]'
    
    def getContextAutoComplete(self, var, fullCommand):
        print "Context auto complete", var, fullCommand
        if self.variables.has_key(var):
            if isinstance(self.variables[var], Item):
                ar = [var + "." + i for i in ItemCommands]
                return self.jsonArray( [k for k in ar if k.startswith(fullCommand) ] )
        return "[]"
    
    def getAllCommands(self):
        ret = "<span class='title'>-=[ HELP ]=-</span><br/><br/>"
        ret += "<table cellspacing='10'><tr>"
        ret += "<td valign='top'><b>Game Commands:</b><br/>" + "<br/>".join(gameCommands.keys()) + "</td></tr><tr>"
        ret += "<td valign='top'><b>Player Commands:</b><br/>" + "<br/>".join(PlayerCommands) + "</td>"
        ret += "<td valign='top'><b>Location Commands:</b><br/>" + "<br/>".join(SpaceCommands) + "</td>"
        ret += "</tr><tr>"
        ret += "<td valign='top'><b>Item Commands:</b><br/>" + "<br/>".join(ItemCommands) + "</td>"
        ret += "<td valign='top'><b>World Commands:</b><br/>" + "<br/>".join(WorldCommands) + "</td>"
        ret += "</tr></table>"
        ret += "<br/><br/>type 'help &lt;command&gt;' to get help on a specific command. eg:<br/>help @me.createItem<br/>"
        return ret
        
        

    def __init__(self):
        '''
        Constructor
        '''
        self.variables = {}
        self._world = World()
        self.worlds = [self._world]
        self.loadWorlds()
        self.hostName = ""
        self.loggedInPlayers = []
        #self.createServer()
        #self.createDefaultLocation()
        
    def getLoggedInPlayers(self):
        return self.loggedInPlayers
    
    def isPlayerLoggedIn(self, player):
        for p in self.loggedInPlayers:
            if p._userName == player._userName:
                return True
        return False
    
    def getPlayerByUserName(self, name):
        for p in self.loggedInPlayers:
            if p._userName == name:
                return p
        return None
        
               
    def setHostName(self, name):
        self.hostName = name
        
    def getHostName(self):
        return self.hostName
        
        
    def loadWorlds(self):
        path = os.path.abspath(os.curdir)
        files = os.listdir(path)
        toLoad = []
        for f in files:
            root, ext = os.path.splitext(f)
            if ext == ".taplWorld":
                toLoad.append(os.path.join(os.path.abspath(os.curdir), f))
        for n in toLoad:
            print "server loading world: " + n
            fl = open(n, "r")
            self.worlds.append(pickle.load(fl))
            fl.close()
            
        for w in self.worlds:
            for s in w.spaces:
                s._occupants = []
            
        
    
    def createDefaultLocation(self):
        '''
        Create a default space in the _world that
        players arrive in
        '''
        space = self._world.createSpace("Starting Room")
        space.describe("A white room with bare walls.")
        self._world.setCurrentLocation(space)
        self.defaultLocation = space
        
    def playerLoggedIn(self, name, conn, addr):
        '''
        This function is called from the websocket server
        for each player that logs in. It returns the corresponding
        game player object so the connection can identify itself
        when passing commands from the web console
        '''
        #print "player _joined: " + _name + ", " + str(conn)
        p = Player(name, conn, addr)
        self.loggedInPlayers.append(p)
        self.worlds[0].defaultLocation._occupants.append(p)
        p._setLocation(self.worlds[0].defaultLocation)
        return p
        
    def playerLoggedOut(self, player):
        pass

    def addWorld( self, world ):
        if not world in self.worlds:
            self.worlds.append( world )
            print "Adding new _world"
        
    def closestMatchItem(self, u, player):
        '''
        Fuzzy match a _name typed in by the player to a real object
        '''
        items = [i._name for i in player._currentLocation._items]
        #result = min(_items, key=lambda v: len(set(u) ^ set(v)))
        result = get_close_matches(u, items, 1, 0.4)
        if len(result)<1:
            return "[NO MATCH]"
        
        return result[0]

    def doPlayerLogin(self, player):
        player._loginStage = 1
        player._message_notification("<b>LOGIN:</b> Please enter your user name")
        return
    
    def processLogin(self, msg, client):
        if client._loginStage == 1:
            # we're expecting a username here
            # try to load the pickled user state
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            fileName = ''.join(c for c in msg if c in valid_chars) + ".taplPlayer"
            try:
                f = open(os.path.join(os.path.abspath(os.curdir), fileName))
                client._player = pickle.loads(f.read())
                print "Desired Password", client._player._password
                client._message_notification("Please enter your password")
                client._loginStage = 2
                f.close()
            except:
                client._message_alert("No user named %s on this server!" % msg)
                client._loginStage = 0
                return
            
            
            return
        
        if client._loginStage == 2:
            # we're expecting a password now
            # the correct password ( and the loaded 
            # user ) are currently stored as variables
            # on the 'client' object. Currently
            # the client is still a 'Guest', if the password
            # is correct, we replace the player object
            # with the loaded pickled version
            # and set _loginStage to 3
            if hasattr(client, '_player'):
                if client._player != None:
                    if msg == client._player._password:
                        # save the socket and apply to
                        # the loaded player
                        _handler = client._handler
                        _loc = client._currentLocation
                        if client in _loc._occupants:
                            _loc._occupants.remove(client)
                        if TAPL().isPlayerLoggedIn(client._player):
                            client = TAPL().getPlayerByUserName(client._player._userName)
                        else:
                            client = client._player
                        client._loginStage = 3
                        client._setHandler(_handler)
                        _handler.player = client
                        client._setLocation(_loc)
                        client._player = None
                        client._message_confirmation("Welcome back %s!" % client._name)
                        self.loggedInPlayers.append(client)
                        return
                    else:
                        client._player = None
                        client._message_alert("Password is incorrect!")
                        client.loginStage = 0
                        return
            client._message_alert("Login Error!") 
    
    def processPlayerSave(self, instruction, player):
        if player._creationStage == 1:
            # we want a username
            player._userName = instruction.lstrip().rstrip()
            player._message_notification("Please enter your email address ( see our privacy policy for details of how your data is held)")
            player._creationStage = 2
            print "USER ENTER EMAIL"
            return
        elif player._creationStage == 2:
            player._email = instruction
            player._message_notification("Finally please choose a password")
            player._creationStage = 3
            print "USER ENTER PASSWORD"
            return
        elif player._creationStage == 3:
            print "Player set password"
            player._password = instruction
            player._loginStage=3
            player._creationStage = 4
            player._save()
            
            return
        elif player._creationStage == 4:
            pass
        else:
            #some sort of error
            player._creationStage = 0
        
            
    def _savePlayer(self, player, fileName):
        print "saving player", fileName
        h = player._handler
        l = player._currentLocation
        player._currentLocation = None
        player._handler=None
        d = pickle.dumps(player)
        f = open(os.path.join(os.path.abspath(os.curdir), fileName), "w")
        f.write(d)
        player._setHandler(h)
        player._currentLocation = l
        player._message_confirmation("Saved")
        return player
    
    def interpret(self, instruction, fromClient):
        '''
        The main interpreting / parsing function,
        commands from players go in here, and this
        returns the output.
        
        The output may be returned only to that player,
        or all players, or all players in a room etc.
        '''
        #sanitize the quotation marks
        instruction = instruction.replace('"', "'")
        returnVal = None
        thingToSet = None
        operateOnObject = None 
        address = []
        
        print "\n-->" + instruction + "\n"
        print "LOGIN STAGE :----> ", fromClient._loginStage
        print "CREATION STAGE :----> ", fromClient._creationStage
        if fromClient._loginStage > 0:
            if fromClient._loginStage < 3:
                self.processLogin(instruction, fromClient)
                return
        
        if fromClient._creationStage > 0:
            if fromClient._creationStage < 4:
                self.processPlayerSave(instruction, fromClient)
                return
        
        if instruction == "login":
            if fromClient._loginStage == 3:
                fromClient._message_notification("You're already logged in")
                return
            self.doPlayerLogin(fromClient)
            return
        
        if instruction == "__JOIN__GAME__":
            fromClient._joinGame()
            fromClient._setLocation(self.worlds[0].defaultLocation)
            return "\n"
        
        test = instruction.split(" ")[0].lstrip().rstrip()
        result = "I dont know what you mean."

        if len(instruction.lstrip().rstrip()) == 0:
            return "\n"
        
        if test in gameCommands.keys():
            result = self.processGameCommand(fromClient, test, instruction[instruction.find(" "):])
            return result + "\n"
        
        if shortcuts.has_key(test[0]):
            result = self.processGameCommand(fromClient, shortcuts[test[0]], instruction[1:])
            
        if fromClient._emotes.has_key(test):
            action = fromClient._emotes[test]
            eventArgs = [fromClient._name, action]
            com = instruction.lstrip().rstrip().split(" ")
            target = "at no-one in particular"
            if len(com) == 3:
                eventArgs.append(com[1])
                target = closestMatchItem(com[2], fromClient._currentLocation._occupants)
                if target == "[NO MATCH]": target = "no-one in particular"
            eventArgs.append(target)
            fromClient._currentLocation._fireEvent(PlayerEvent(PlayerEvent.PLAYER_EMOTE, fromClient, " ".join(eventArgs)))
            eventArgs = "You"
            fromClient._message_notification(" ".join(eventArgs))
            return " ".join(eventArgs)
        
        if fromClient._currentLocation != None:
            for i in fromClient._currentLocation._items:
                if i.verbs.has_key(test):
                    result = i.verbs[test]
                    return result + "\n"
        
        if fromClient._currentLocation:
            for p in fromClient._currentLocation._portals:
                if p.spaceOne == fromClient._currentLocation:
                    if test == p.dirIn or test == p.shortDirIn:
                        fromClient._setLocation(p.spaceTwo)
                        #p.spaceOne._occupants.remove(fromClient)
                        #p.spaceTwo._occupants.append(fromClient)
                        
                        return " "
                else:
                    if test == p.dirOut or test == p.shortDirOut:
                        fromClient._setLocation(p.spaceOne)
                        #p.spaceTwo._occupants.remove(fromClient)
                        #p.spaceOne._occupants.append(fromClient)
                        return " "
            
        
        if "=" in instruction:
            # we're either changing an existing object or need to return a new one
            thingToSet = instruction.split("=")[0].rstrip().lstrip()
            instructionList = instruction.split('=')[1].lstrip().rstrip()
            val = self.processClientProgram(instruction.split('=')[1], fromClient)
            
            if val[0]:
                if isinstance(val[0], str):
                    # there was some sort of error, we wont alter the _world state
                    return val[0] + "\n"
                self.variables[thingToSet] = val[0]
                return val[1] + "\n"
            else:
                match = self.closestMatchItem(instructionList, fromClient)
                if match != "[NO MATCH]":
                    item = None
                    for i in fromClient._currentLocation._items:
                        if i._name == match:
                            item = i
                            break
                    if item:
                        self.variables[thingToSet] = item
                        return "Done" + "\n"
            return
        else:
            # we're changing a pre-exisiting object via a method directly
            # or just retrieving some property on a preexisting object
            val = self.processClientProgram(instruction, fromClient)
            if val[0]:
                if isinstance(val[0], str):
                    return val[0]
                return val[1] + "\n"
        return result + "\n\n"
            
    def processClientProgram(self, instructions, client):
        '''
        Execute a function that is going to change the game _world in 
        some way, either by creating new content, or modifying existing
        objects. This is the 'coding' of the game _world
        
        Game interactions may change objects as well, but cannot directly
        create them as in this function
        
        '''
        inString = False
        chr = 0
        returnVal = [None, '']
        while len(instructions):
            if instructions.find('.') > -1:
                if instructions.find("(") > -1:
                    # careful, we may have a full stop in an argument somewhere
                    if instructions.find("(") < instructions.find('.'):
                        command = instructions[:instructions.find(")")+1]
                        chr = instructions.find(")") + 1
                    else:
                        command = instructions[:instructions.find('.')].lstrip().rstrip()
                        chr = instructions.find('.')
                else:
                    command = instructions[:instructions.find('.')].lstrip().rstrip()
                    chr = instructions.find('.')
            else:
                command = instructions
                chr = len(instructions)-1
            
            if returnVal == [None, '']:
                # first return value must be some object we already know about
                if command == '@_world':
                    returnVal = [client._currentLocation._world, 'Done']
                elif command == '@here':
                    if client._currentLocation != None:
                        returnVal = [client._currentLocation, 'Done']
                    else:
                        client._currentLocation = self.defaultLocation
                        returnVal = [self.defaultLocation, 'Done']
                elif command == '@me':
                    returnVal = [client, 'Done']
                elif self.variables.has_key(command):
                    returnVal = [self.variables[command], 'Done']
                else:
                    #print command + " not found!"
                    return (None, "I really don't know what you mean, sorry!")
                
            else:
                if isinstance(returnVal[0], World):
                    if returnVal[0] not in self.worlds:
                        self.worlds.append( returnVal[0] )
                        print "New world created: " + returnVal[0]._name
                if command.find("(") > -1:
                    com, args = command.split("(")
                    args = args.split(")")[0]
                    
                    args = self.resolveArguments(args, client)  
                    if hasattr(returnVal[0], com):
                        func = getattr(returnVal[0], com)
                        returnVal = [func(*args), 'Done']
                        #if args.find("'") > -1:
                            #args = args.replace("'", "")
                            #func = getattr(returnVal, com)
                            #returnVal = func(*args)
                        #else:
                            
                            #if self.variables.has_key(args):
                                #args = self.variables[args]
                                #func = getattr(returnVal, com)
                                #returnVal = func(args)
                else:
                    if hasattr(returnVal[0], command):
                        returnVal = [getattr(returnVal[0], command), 'Done']
                    
                    
            try:
                instructions = instructions[chr+1:]
            except:
                instructions = ""
        return returnVal
    
    def resolveArguments(self, args, player):
        '''
        Resolve a number of arguments into 
        actual objects or strings to act upon
        
        we ALWAYS pass the player that initiated the call
        as the first argument
        '''
        
        ret = []
        if args.find(",") == -1:
            # only one argument, resolve it and return
            if args.find("'") > -1:
                return [player, args.replace("'","")]
            elif self.variables.has_key(args):
                return [player, self.variables[args]]
            else:
                return [player]
                
        if args.find("'") > -1:
            instring = False
            i = 0
            last = 0
            for c in str(args):
                if c == "," and instring == False:
                    ret.append(args[last:i])
                    last = i+1
                if c == "'":
                    if instring:
                        ret.append(args[last:i+1])
                        last = i+1
                        instring = False
                    else:
                        last = i
                        instring = True
                i+=1
            if last < i:
                ret.append(args[last:i])
            final = []
            for r in ret:
                if len(r) > 0:
                    e = r.lstrip().rstrip()
                    if len(e):
                        if e.find("'") > -1:
                            final.append(e.replace("'",""))
                        else:
                            if self.variables.has_key(e):
                                final.append(self.variables[e])
                            else:
                                # not a variable, should be a base type
                                try:
                                    f = float(e)
                                    final.append(f)
                                except ValueError,TypeError:
                                    pass
                                
        #print final  
        final.insert(0, player)  
        return final
        
    
    def resolveItemAction(self, item, client, command, rest):
        '''
        TODO:
        Items need their own interaction processing language
        possibly using keywords. eg:
        
        "@this.someProp++; if @this.someProp > 40: @user.message("You won");etc."
        
        
        '''
        pass
    
    def messageUser(self, message, client):
        '''
        Send a message to a single user
        this will often be feedback from the scripting
        language
        '''
        pass
    
    def messageAllUsers(self, message):
        '''
        Send out a system wide message to all connected users
        ''' 
        pass
    
    def messageRoom(self, room):
        '''
        Send a message to all users in a specific room
        '''
        pass        
          
    def processGameCommand(self, client, command, rest):
        '''
        Process game instructions like:
        
        'examine knife'
        'use clock'
        'give cigar to william'
        'N'
        'look'
        'attack goblin'
    
        '''
        #print "Game command", command
        result = False
        if client._currentLocation == None:
            client._setLocation( self.defaultLocation )
        if command == "print_state":
            client._message_notification("\n".join([str(k) + " = " + str(v) for k,v in self.variables.items()]))
            return "\n".join([str(k) + " = " + str(v) for k,v in self.variables.items()])
        
        if command == 'look':
            locale = 'You are in ' + client._currentLocation._name + ", " + client._currentLocation._description
            if len(client._currentLocation._items):
                locale += ".\nLooking around you see " + ", ".join(["a " + i._name for i in client._currentLocation._items])
            if len(client._currentLocation._portals):
                locale += ".\nYou see "
                ports = []
                for i in client._currentLocation._portals:
                    d = i.dirIn if i.spaceOne == client._currentLocation else i.dirOut
                    other = i.spaceOne if i.spaceTwo == client._currentLocation else i.spaceTwo
                    st = "a " + i._name + " leading " + d + " to " + other._name
                    
                    ports.append(st)
                locale += ", ".join(ports)
            client._message_notification(locale.replace("\n", "<br/>"))
            return locale
        
        if command == 'help':
            print "--->" + command + "<----"
            print "--->" + rest + "<-----"
            r = rest.lstrip().rstrip()
            if len(r) < 2:
                client._message_notification(self.getAllCommands())
            elif AllDocs.has_key(r):
                g = AllDocs[r]
                if g:
                    client._message_notification("<br/>".join(g.splitlines()))
                else:
                    client._message_alert("Sorry, docs haven't been written for that command yet!")
                
            else:
                client._message_alert("Not sure what you mean...")
            return ""
        
        if command == 'say':
            print client._currentLocation._occupants
            client.say(client,  rest.lstrip().rstrip() )
            #client._message_notification("You say: " + rest.lstrip().rstrip())
            return  "you say " + rest.lstrip().rstrip()
        
        
        if command == 'shout':
            client.shout(client, rest.lstrip().rstrip() )
            return "you shout " +  rest.lstrip().rstrip()
        
        if command == 'examine':
            target = rest.lstrip().rstrip()
            if self.variables.has_key(target):
                #print ">>> " + str(self.variables[target])
                if hasattr(self.variables[target], "_description"):
                    client._message_notification(self.variables[target]._description)
                    return self.variables[target]._description
                else:
                    client._message_notification(self.variables[target])
                    return str(self.variables[target])
            match = self.closestMatchItem(target, client)
            if match == "[NO MATCH]":
                client._message_alert("I don't know what %s is" % target)
                return 'I dont know what %s is' % target
            for i in client._currentLocation._items:
                if i._name == match:
                    client._message_notification(i._description)
                    return i._description
        if command == 'take':
            target = rest.lstrip().rstrip()
            if len(target):
                match = self.closestMatchItem(target, client)
                if match != '[NO MATCH]':
                    for i in client._currentLocation._items:
                        if i._name == match:
                            if i.verbs.has_key(command):
                                return i.verbs[command]

        if command == "warp":
            worldNames = [w.name for w in self.worlds]
            target = rest.lstrip().rstrip()
            match = closestMatchString( target, worldNames )
            if match != '[NO MATCH]':
                for i in self.worlds:
                    if i.name == match:
                        client._currentLocation._occupants.remove(client)
                        client._setLocation( i.defaultLocation )
                        client._message_notification("Warp complete<br/>You are now in %s, %s" % (client._currentLocation._name, client._currentLocation._world.name))
                        return 'You are in ' + client._currentLocation._name + ", " + client._currentLocation._description
                            
        if command == 'inventory':
            client._message_notification("You're carrying:<br/>" + "<br/>".join(["a" + i._name for i in client._inventory]))
            return "You're holding " + ",".join(["a" + i._name for i in client._inventory])
        
        if command == 'list_worlds':
            client._message_notification("Worlds on this server:<br/>" + "<br/>".join([w.name for w in self.worlds]))
            return "Worlds on this server:\n" + "\n".join([w.name for w in self.worlds]) + "\n"
        
        if command == 'save_world':
            result = client._currentLocation._world.save(client)
            client._message_confirmation(result)
            return result
        
        if command == 'download_world':
            result = client._currentLocation._world.download(client)
            client._message_notification("Downloading...")
            return ""
        
        if command == 'who':
            result = "Other people in the room:\n" + "\n".join([p._name for p in client._currentLocation._occupants])
            client._message_notification(result)
            return ""
            

        return "\n"
                    
        
if __name__ == '__main__':
    game = TAPL()
    
    #print game.resolveArguments("someVariable, 'Some string argument, with a comma', anotherVariable")
    #print game.resolveArguments("'some String'")
    
    #game.interpret('myItem = @_world.createItem("sword fragment").describe("a fragment of a sword")', None)
    #game.interpret('myItem._description', None)
    #game.interpret('myItem.describe("A rusty old sword with a bad attitude")', None)
    #game.interpret('myItem._description', None)
    #game.interpret('thisRoom = @_world.createSpace("The Temple of Noggin")', None)
    #game.interpret('thisRoom.describe("A splendid temple, filled with columns and statues. An ornamental fountain bubbles in the central courtyard")', None)
    #game.interpret('thisRoom._description',None)
    #game.interpret('altar = thisRoom.createItem("altar").describe("A large stone altar, dripping with blood and gore")', None)
    #game.interpret('thisRoom.createItem("bubblegum dispenser").describe("Its nearly empty")', None)
    #game.interpret('@_world.setCurrentLocation(thisRoom)', None)
    #game.interpret('look', None)
    #game.interpret('examine Bubblegum dispenser', None)
    #game.interpret('say You bunch of Wankers!', None)
    #game.interpret('p = thisRoom.createPortal("green door")', None)
    #game.interpret('thisRoom.addItem(myItem)', None)
    #game.interpret('look', None)
    #game.interpret('examine altar', None)
    #game.interpret('chest = @here.createItem("Chest").describe("A big, locked chest").verb("open", "Try as you might, the chest remains closed")', None)
    #game.interpret('tunnel = thisRoom.createPortal("A winding tunnel leading north")',None)
    #game.interpret('nextRoom = @_world.createSpace("The temple inner sanctum")', None)
    #game.interpret('tunnel.setEnd(nextRoom)', None)
    #game.interpret('look',None)
    #game.interpret('examine dispenser', None)
    #game.interpret('examine stone altar', None)
    #game.interpret('examine fragment', None)
    
    x = ""
    print welcome
    player = Player("Ben", None, None)
    player._setLocation(game.worlds[0].defaultLocation)
    
    while x != "quit":
        x = raw_input("Enter command: ")
        if x == "quit" or x == "exit":
            break
        print game.interpret(x, player)
    
    #07753245487
    
    
