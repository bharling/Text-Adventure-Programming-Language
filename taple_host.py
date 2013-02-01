# -*- coding: utf-8 -*-
import argparse
import random
import os
import socket
import cherrypy

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.server.handler.threadedhandler import WebSocketHandler, EchoWebSocketHandler
from ws4py.framing import Frame, OPCODE_CONTINUATION, OPCODE_TEXT, \
     OPCODE_BINARY, OPCODE_CLOSE, OPCODE_PING, OPCODE_PONG
    
import TAPL
from cherrypy.lib.static import serve_download

print dir(cherrypy.lib.static)
print dir(cherrypy.lib.static.mimetypes)

__tapl = TAPL.TAPL()

def getTapl():
    return __tapl

class MyWebSocketPlugin(WebSocketPlugin):
    def __init__(self, bus):
        WebSocketPlugin.__init__(self, bus)
        
        
    def start(self):
        cherrypy.log("Starting WebSocket processing")
        self.bus.subscribe('handle-websocket', self.handle)
        self.bus.subscribe('websocket-broadcast', self.broadcast)
        self.bus.subscribe('main', self.cleanup)
        self.bus.subscribe('websocket-message', self.message)
        
        
    def stop(self):
        self.bus.unsubscribe('websocket-message', self.message)
        WebSocketPlugin.stop(self)
        
    
    def message(self, m, h, b):
        """
        Sends a message to just one client handler

        @param m: a message suitable to pass to the send() method
          of the connected handler.
        @param b: whether or not the message is a binary one
        @param h: the handler to send to 
        """
        
        print "message: " + str(h)
        
        handlers = self.handlers[:]
        for peer in handlers:
            try:
                handler, addr = peer
                if handler is h:
                    handler.send(m, b)
                    break
            except:
                cherrypy.log(traceback=True)
        

class ChatWebSocketHandler(WebSocketHandler):
    def __init__(self, sock, protocols, extensions):
        print "Handler init"
        WebSocketHandler.__init__(self, sock, protocols, extensions)
        print dir(sock)
        print sock.getpeername()
    
    def closed(self, code, reason=None):
        print "closed socket"
        WebSocketHandler.closed(self, code, reason)
        if self.player:
            self.player._currentLocation._world.save(self.player)
            
    def __copy__(self):
        return None
    
    def __deepcopy__(self, memo):
        return None
    
    def opened(self):
        print "[>>> OPENED CONNECTION <<]"
        WebSocketHandler.opened(self)
        self.player = getTapl().playerLoggedIn("Player" + str(random.randint(0,100)), self, None)
        self.player._setHandler(self)
        
    def sendMessage(self, m):
        print "sending message"
        cherrypy.engine.publish('websocket-message', m, self, False)
        
    def offerFile(self, filePath):
        print "downloading", filePath
        serve_download(filePath)
    
    def received_message(self, m):
        if m.opcode == OPCODE_TEXT:
           result = getTapl().interpret(str(m.data), self.player)
           if 0:
               self.sendMessage(result)

class Root(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        
    @cherrypy.expose
    def autocomplete(self, term):
        return getTapl().getAutoComplete(term)

    @cherrypy.expose
    def index(self):
        return """<html>
    <head>
      <link rel="stylesheet" href="/css/tapl.css"/>
      <script type='application/javascript' src='/js/jquery-1.7.1.min.js'></script>
      <script type='application/javascript' src='/js/jquery-ui-1.8.17.custom.min.js'></script>
      <link rel='stylesheet' href='/css/ui-lightness/jquery-ui-1.8.17.custom.css'/>
      <script type='application/javascript'>
        $(document).ready(function() {

          websocket = 'ws://%(host)s:%(port)s/ws';
          if (window.WebSocket) {
            ws = new WebSocket(websocket);
          }
          else if (window.MozWebSocket) {
            ws = MozWebSocket(websocket);
          }
          else {
            console.log('WebSocket Not Supported');
            return;
          }

          $(window).unload(function() {
             ws.close();
          });
          ws.onmessage = function (evt) {
             $('#chat').html($('#chat').html() + evt.data);
             $('#chat').scrollTop(
                     $('#chat')[0].scrollHeight - $('#chat').height()
             );
          };
          ws.onopen = function() {
             ws.send("__JOIN__GAME__");
          };

          $('#chatform').submit(function() {
               console.log($('#message').val());
                ws.send($('#message').val());
                 $('#message').val("");
                 

             return false;
    
          });
          
          $('#message').autocomplete({
              source:'/autocomplete'
            })

          /*$('#send').click(function() {
             console.log($('#message').val());
             ws.send($('#message').val());
             $('#message').val("");
            


             return false;
          });*/
        });
      </script>
    </head>
    <body>
    <div id="container">
        <div id="chat"></div>
        <form action='#' id='chatform' method='get'>
          <!--<textarea id='chat' cols='80' rows='40'></textarea>-->
          <br />
          <label for='message'>%(username)s: </label><input type='text' id='message' />
          <input id='send' type='submit' value='Send' />
        </form>
      </div>
    </body>
    </html>
    """ % {'username': "User%d" % random.randint(0, 100),
           'host': self.host,
           'port': self.port}

    @cherrypy.expose
    def ws(self):
        cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Echo CherryPy Server')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('-p', '--port', default=9023, type=int)
    args = parser.parse_args()
    args.host = socket.gethostbyname(socket.gethostname())
    #args.host="192.168.1.66"
    getTapl().setHostName("http://" + args.host + ":" + str(args.port))
    print "serving on: " + args.host
    cherrypy.config.update({'server.socket_host': args.host,
                            'server.socket_port': args.port,
                            'tools.staticdir.root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')),
                            'tools.sessions.on':True,
                            'tools.sessions.storage_type':'file',
                            'tools.sessions.storage_path':os.path.abspath(os.curdir),
                            'tools.sessions.timeout': 60})

    MyWebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()
    cherrypy.lib.static.mimetypes.add_type("application/x-download", ".taplWorld")
    cherrypy.quickstart(Root(args.host, args.port), '', config={
        '/ws': {
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': ChatWebSocketHandler
            },
        '/js': {
              'tools.staticdir.on': True,
              'tools.staticdir.dir': 'js'
            },
        '/css': {
              'tools.staticdir.on': True,
              'tools.staticdir.dir': 'css'
            },
        '/images': {
              'tools.staticdir.on': True,
              'tools.staticdir.dir': 'images'
            },
        '/worlds': {
              'tools.staticdir.on': True,
              'tools.staticdir.dir': 'worlds'
            }
        }
    )
