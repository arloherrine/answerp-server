import copy
import enum
import json
import socketserver
import threading
import time
import Adafruit_CharLCD as LCD

class AnswerpTCPHandler(socketserver.StreamRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def __init__(self):
        self.server.data = {}

    def handle(self):
        # self.request is the TCP socket connected to the client
        raw_json = self.rfile.readline().strip()
        print("{} wrote: {}".format(self.client_address[0], raw_json))
        newdata = json.loads(raw_json)
        
        self.server.data['calls'] = merge_new_old(newdata['calls'], self.server.data['calls'])
        self.server.data['texts'] = merge_new_old(newdata['texts'], self.server.data['texts'])


    # TODO periodically purge old data?
    def merge_new_old(new, old):
        for datum in new:
            if not old[datum['id']]:
                datum['new'] = True
                old[datum['id']] = datum

        for datum in old:
            if datum not in new:
                datum['new'] = False

        # TODO sort by date
        return old

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class UIState(enum.Enum):
    off = 1
    main_menu = 2
    call_menu = 3
    call_display = 4
    text_menu = 5
    text_display = 6


class LCDUI:
    def __init__(self, *args, **keywords):
        self.state = UIState.off
        self.lcd = LCD.Adafruit_CharLCDPlate()
        self.top_selected = True
        self.content = ['','']
        self.index = 0
        self.callbacks = {}
        self.selectable = True

        self.register_callback((UIState.main_menu, LCD.SELECT, True), self.turn_off)
        self.register_callback((UIState.call_menu, LCD.SELECT, True), self.turn_off)
        self.register_callback((UIState.call_display, LCD.SELECT, True), self.turn_off)
        self.register_callback((UIState.text_menu, LCD.SELECT, True), self.turn_off)
        self.register_callback((UIState.text_display, LCD.SELECT, True), self.turn_off)

        self.register_callback((UIState.off, LCD.SELECT, False), self.turn_on)
        self.register_callback((UIState.off, LCD.SELECT, True), self.turn_on)

        self.register_callback((UIState.main_menu, LCD.UP, False), self.scroll_up)
        self.register_callback((UIState.main_menu, LCD.DOWN, False), self.scroll_down)
        self.register_callback((UIState.main_menu, LCD.SELECT, False), self.main_menu_select)

        self.register_callback((UIState.call_menu, LCD.UP, False), self.scroll_up)
        self.register_callback((UIState.call_menu, LCD.DOWN, False), self.scroll_down)
        self.register_callback((UIState.call_menu, LCD.SELECT, False), self.call_menu_select)

        self.register_callback((UIState.text_menu, LCD.UP, False), self.scroll_up)
        self.register_callback((UIState.text_menu, LCD.DOWN, False), self.scroll_down)
        self.register_callback((UIState.text_menu, LCD.SELECT, False), self.text_menu_select)

        self.register_callback((UIState.call_display, LCD.UP, False), self.scroll_up)
        self.register_callback((UIState.call_display, LCD.DOWN, False), self.scroll_down)
        self.register_callback((UIState.call_display, LCD.SELECT, False), self.self.open_call_menu)

        self.register_callback((UIState.text_display, LCD.UP, False), self.scroll_up)
        self.register_callback((UIState.text_display, LCD.DOWN, False), self.scroll_down)
        self.register_callback((UIState.text_display, LCD.SELECT, False), self.self.open_text_menu)

    def register_callback(self, state, button, long, func):
        self.callbacks.setdefault((button, long), []).append(func)

    def display(self):
        if self.top_selected:
            line1 = self.content[self.index]
            line2 = self.content[self.index + 1]
        else:
            line1 = self.content[self.index - 1]
            line2 = self.content[self.index]

        if self.selectable:
            if self.top_selected:
                line1 = "> " + line1
                line2 = "  " + line2
            else:
                line1 = "  " + line1
                line2 = "> " + line2

        self.lcd.clear()
        self.lcd.message(line1 + "\n" + line2)
 
    def turn_on(self):
        self.lcd.set_backlight(1)
        self.state = UIState.main_menu
        self.top_selected = True
        self.index = 0
        self.content = ['{} new texts'.format(len(self.server.data['texts'])),
                '{} new calls'.format(len(self.server.data['calls']))]
        self.selectable = True
        self.display()

    def turn_off(self):
        self.lcd.set_backlight(0)
        self.lcd.clear()
        self.state = UIState.off
        self.context = ['','']

    def scroll_up(self):
        self.top_selected = True
        if self.index != 0:
            self.index -= 1
        self.display()

    def scroll_up(self):
        self.top_selected = not self.selectable
        self.index += 1
        if self.index >= len(self.content):
            self.index -= 1
        self.display()

    def main_menu_select(self):
        if self.top_selected:
            self.open_text_menu()    
        else:
            self.open_call_menu()    

    def open_text_menu(self):
        self.state = UIState.text_menu
        self.index = 0
        self.top_selected = True
        self.selectable = True
        self.content = ["{}-{}".format(text['date'], text['name'] for text in self.server.data['texts'])]
        self.display()

    def open_call_menu(self):
        self.state = UIState.call_menu
        self.index = 0
        self.top_selected = True
        self.selectable = True
        self.content = ["{}-{}".format(call['time'], call['name'] for call in self.server.data['texts'])]
        self.display()

    def text_menu_select(self):
        text = self.server.data['text'][self.index]
        self.state = UIState.text_display
        self.index = 0
        self.top_selected = True
        self.selectable = False
        self.content = [text['body'][i:i+16] for i in range(0, len(text['body]']), 16)]
        self.display()

    def call_menu_select(self):
        call = self.server.data['calls'][self.index]
        self.state = UIState.call_display
        self.index = 0
        self.top_selected = True
        self.selectable = False
        self.content = [
                call['time'],
                call['name'],
                call['callNumber']
            ]
        self.display()

    def main_loop(server):
        while(True):
            # TODO implement
            pass



if __name__ == "__main__":
    HOST, PORT = "localhost", 8888

    server = ThreadedTCPServer((HOST, PORT), AnswerpTCPHandler)
    server_thread = threading.Thread(name='data-update-server-thread', target=server.serve_forever)

    ui = LCDUI()
    ui.main_loop()

