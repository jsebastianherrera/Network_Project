import re
import socket
from _thread import *
import logging
from requests import post


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

    def get_type_and_url(self, request):
        url = re.findall(b"\/\/(.*)\ ", request)
        type = re.findall(b"[A-Z]*", request)[0]
        if len(url) > 0 and type == b"GET" or type == b"POST":
            return bytes.decode(url[0]), bytes.decode(type)
        else:
            return "", ""

    def check_virtual_sites(self, webserver, recv):
        t = 0
        if webserver in self.__virtual_sites["Virtual host"]:
            for i in self.__virtual_sites["Virtual host"]:
                if i == webserver:
                    tmp = self.__virtual_sites["Real host"][t]
                    root = self.__virtual_sites["Root directory"][t]
                    break
                t += 1
            aux = bytes.decode(recv)
            aux = aux.replace(webserver, tmp)
            aux = aux.replace("http://" + tmp + "/",
                              "http://" + tmp + "/" + root)
            return True, tmp, aux.encode()
        else:
            return False, "", recv

    def handle_request(self, client: socket, addr):
        request = client.recv(self.__buffer_size)
        url, type = self.get_type_and_url(request)
        if url != "" and type != "":
            if len(re.findall(":[0-9]*", url)) > 0:
                port = int(re.search(":[0-9]*", url)[0][1:])
                webserver = re.search("([A-Z\.a-z0-9]*)", url)[0]
            else:
                # default port 80
                port = 80
                webserver = re.search("([A-Z\.a-z0-9]*)", url)[0]
            self.proxy_server(webserver, port, client, request, type)

    def get_request(self, socket: socket, client, webserver):
        try:
            while True:
                reply = socket.recv(self.__buffer_size)
                if len(reply) > 0:
                    logging.info("Replied GET->" + webserver)
                    print('______REPLIED GET______')
                    print(reply.decode(encoding="utf8", errors='ignore'))
                    client.send(reply)
                else:
                    break
        except Exception as e:
            print(str(e))

    def get_data_post(self, reply):
        try:
            index = reply.rindex("\"form\":")
            x = reply[index:].split("}")[0].split("{")[1]
            return x
        except Exception as e:
            return None

    def post_request(self, socket: socket, client, webserver):
        try:
            while True:
                reply = socket.recv(self.__buffer_size)
                if len(reply) > 0:
                    data = self.get_data_post(reply.decode(
                        encoding="utf8", errors='ignore'))
                else:
                    break
                if data is not None:
                    if len(data) > 0:
                        logging.info("Replied POST->" + webserver + data)
                        print('______REPLIED POST______')
                        print(reply.decode(encoding="utf8", errors='ignore'))
                        client.send(reply)

        except Exception as e:
            print(str(e))

    def proxy_server(self, webserver, port, client, recv, type):
        try:
            print("Port:", port, "\t", "Web:", webserver)
            print("_________REQUEST_________")
            logging.info("REQUESTED->" + webserver)
            print(recv.decode(encoding="utf8", errors='ignore'))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            flag, web, tmp = self.check_virtual_sites(webserver, recv)
            if flag:
                recv = tmp
                webserver = web
                print("_________REDIRECTED_________")
                logging.info("REDIRECTED->" + webserver)
                print(recv.decode(encoding="utf8", errors='ignore'))

            s.connect((webserver, port))
            s.send(recv)
            if type == "GET":
                self.get_request(s, client, webserver)
            elif type == "POST":
                self.post_request(s, client, webserver)
            s.close()

        except Exception as e:
            print(e)


if __name__ == "__main__":
    n = 5
    port = 5555
    address = "127.0.0.1"
    file = "virtual_sites.txt"
    sock = SocketServer(port, address, n, file)
