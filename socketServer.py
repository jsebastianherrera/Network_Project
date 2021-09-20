import argparse as arg
import re
import socket
import signal
from _thread import *
import logging


class SocketServer:
    def __init__(self, port, address, max_conn, file):
        logging.basicConfig(
            filename="log.txt",
            level=logging.INFO,
            format="{asctime} {levelname:<8} {message}",
            style="{",
        )
        self.__port = int(port)
        self.__address = address
        self.__buffer_size = 4096
        self.__virtual_sites = self.sites(file)
        # Init socket server
        self.severSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind socket -> Assing a specified IP and port, It's like a unique number that each socket has
        self.severSocket.bind((self.__address, self.__port))
        self.severSocket.listen(int(max_conn))
        while True:
            (socket_client, addr_client) = self.severSocket.accept()
            start_new_thread(self.handle_request, (socket_client, addr_client))

    def sites(self, file_name) -> dict:
        try:
            f = open(file_name, "r")
            nhost = []
            hostv = []
            root = []
            for i in f:
                r = re.findall("([a-zA-Z\.]*\,|\~[a-zA-Z]*\/)", i)
                nhost.append(r[0][: len(r[0]) - 1])
                hostv.append(r[1][: len(r[1]) - 1])
                root.append(r[2])
            return {"Virtual host": nhost, "Real host": hostv, "Root directory": root}
        except Exception as e:
            print(e)
            return {}

    def handle_request(self, client: socket, addr):
        request = client.recv(self.__buffer_size)
        results = re.findall(b"\/\/(.*)\ ", request)
        if len(results) > 0:
            url = bytes.decode(results[0])
            if len(re.findall(":[0-9]*", url)) > 0:
                port = int(re.search(":[0-9]*", url)[0][1:])
                webserver = re.search("([A-Z\.a-z0-9]*)", url)[0]
            else:
                # default port 80
                port = 80
                webserver = re.search("([A-Z\.a-z0-9]*)", url)[0]
                self.proxy_server(webserver, port, client, request, addr)

    def proxy_server(self, webserver, port, client, recv, addr):
        try:
            t = 0
            resend = ""
            flag = True
            logging.info(str(addr) + " requests ->" + webserver)
            print("Port:", port, "\t", "Web:", webserver, end="\n\n")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if webserver in self.__virtual_sites["Virtual host"]:
                for i in self.__virtual_sites["Virtual host"]:
                    if i == webserver:
                        tmp = self.__virtual_sites["Real host"][t]
                        root = self.__virtual_sites["Root directory"][t]
                        flag = False
                        break
                    t += 1
                aux = bytes.decode(recv)
                aux = aux.replace(webserver, tmp)
                aux = aux.replace("http://" + tmp + "/", "http://" + tmp + "/" + root)
                recv = aux.encode(aux)
                resend = "http://" + tmp + "/" + root

            print("*************Requested**************")
            print(recv)
            s.connect((webserver, port))
            s.send(recv)
            while True:
                reply = s.recv(self.__buffer_size)
                if len(reply) > 0:
                    client.send(reply)
                    print("************Replied***********")
                    print(reply)
                    if not flag:
                        logging.info("Replied ->" + resend)
                    else:
                        logging.info("Replied ->" + webserver)
                else:
                    logging.info("Replied -> none")
                    break
            s.close()

        except Exception as e:
            print(e)


if __name__ == "__main__":
    n = 5
    port = 5555
    address = "127.0.0.1"
    file = "virtual_sites.txt"
    parser = arg.ArgumentParser(description="Basic python proxy")
    parser.add_argument("-p", "--port", type=int, help="[0-9]*")
    parser.add_argument("-a", "--address", help="Ipv4 address")
    parser.add_argument("-n", "--connections", type=int, help="Max connections")
    parser.add_argument("-f", "--file", help="File name")
    args = parser.parse_args()
    if args.port != None:
        port = args.port
    if args.connections != None:
        n = args.connections
    if args.address != None:
        address = args.address
    if args.file != None:
        file = args.file
    sock = SocketServer(port, address, n, file)
