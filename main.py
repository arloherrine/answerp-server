import socketserver

class AnswerpTCPHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def __init__(self):
        self.data = {}

    def handle(self):
        # self.request is the TCP socket connected to the client
        newdata = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))
        print(newdata)
        
        for call in newdata['calls']:
            if not self.data['calls'][call['id']]:
                call['new'] = True
                self.data['calls'][call['id']] = call

        for text in newdata['texts']:
            if not self.data['texts'][text['id']]:
                text['new'] = True
                self.data['texts'][text['id']] = text

        # TODO blink screen if new

if __name__ == "__main__":
    HOST, PORT = "localhost", 8888

    # Create the server, binding to localhost on port 9999
    server = socketserver.TCPServer((HOST, PORT), AnswerpTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
