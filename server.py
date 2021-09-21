#  coding: utf-8
import pathlib
import socketserver
import urllib
import mimetypes

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


class MyWebServer(socketserver.BaseRequestHandler):
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print ("Got a request of: %s\n" % self.data)
        self.parse_request()

    def parse_request(self):
        # read http request message
        requestline = str(self.data, 'iso-8859-1')
        line = requestline.rstrip('\r\n')
        word = line.split()
        if len(word) < 3:
            raise Exception("invalid http request")
        # http method and path
        method, pth = word[:2]
        if method != 'GET':
            return self.return_405()

        # site root is www folder
        root = pathlib.Path('./www')
        try:
            f = root / resolve_path(pth)
        except IndexError:  # if http path invalid
            return self.return_404()
        if f.is_dir():
            if not pth.endswith('/'):  # redirect correct paths
                return self.return_301(pth + '/')
            return self.return_file(f/'index.html')  # The webserver can return index.html from directories (paths that end in /)
        elif f.is_file():
            return self.return_file(f)  # The webserver can serve files from ./www
        else:
            return self.return_404()  # The webserver can server 404 errors for paths not found

    def return_404(self):
        """
        if resource not found
        """
        self.request.sendall(b'HTTP/1.1 404 Not Found\r\n')

    def return_405(self):
        """
        send 405 http code
        """
        self.request.sendall(b'HTTP/1.1 405 Method Not Allowed\r\n')

    def return_301(self, location):
        """
        301 redirect special location
        :param location: target location
        """
        self.request.sendall(b'HTTP/1.1 301 Move Permanently\r\n')
        h = 'Location: %s\r\n' % location
        self.request.sendall(h.encode('utf-8'))

    def return_file(self, file):
        """
        return file and mime-types
        :param file: filename string
        """
        content_type, _ = mimetypes.guess_type(file)
        self.request.send(b'HTTP/1.1 200 OK\r\n')
        self.request.send(('Content-Type: {}\r\n'.format(content_type)).encode('utf-8'))
        self.request.send(b'\r\n')
        self.request.sendfile(open(file, 'rb'))


def resolve_path(path):
    """
    Parse the path to the expected format
    :param path: /dir/../index.html?key=name
    :return: index.html
    """
    path, _, query = path.partition('?')  # remove query
    path = urllib.parse.unquote(path)  # unquote

    path_parts = path.split('/')
    head_parts = []
    for part in path_parts:  # remove illegal path
        if part == '..':
            head_parts.pop()  # IndexError if more '..' than prior parts
        elif part and part != '.':
            head_parts.append(part)

    return "/".join(head_parts)


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
