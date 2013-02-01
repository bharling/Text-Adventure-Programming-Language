Text Adventure Programming Language
===================================

This project is an attempt to create a dynamic, multiplayer text-based environment for creating collaborative adventures.

It features a multiplayer html server based on the websockets standard, and a dynamic, chainable language similar to javascript / jquery for creating content.

Content can be saved and reloaded and shared with other users.


Requirements
============

The server is implemented in cherrypy, but could easily be ported to any python wsgi framework.

dependencies
------------
python 2.7+ -> http://www.python.org
pyparsing -> http://pyparsing.wikispaces.com/
cherrypy -> http://www.cherrypy.org/
Websocket for python -> https://github.com/Lawouach/WebSocket-for-Python


Running
=======

Execute TAPL_host.py. The server should start on port 9023. In Chrome or Firefox go to:

http://localhost:9023/

you should see the default screen.

type help for a list of commands. Autocomplete is also implemented.
