from flask import Flask, Response, jsonify, request
import requests
from queue import Queue
from time import sleep


class Server:
    def __init__(self, hostname: str, connections: int):
        self.app = Flask(__name__)

        self.host, self.port = self.__parseHost(hostname)
        self.port = int(self.port)
        self.host = str(self.host)

        if(connections == 0):
            raise Exception('connections cannot be 0!')
        else:
            self.connections = connections

        self.existingconnections = 0
        self.clients = {} # structure is {clientname: [clientPassword, Queue()]}
        self.groups = {}  # structure is {groupName: [clientList, clientPositions, messageList]}
        self.runServer()
    
    def __parseHost(self, hostname: str):
        split_hostname = hostname.split(":")
        return (split_hostname[0], split_hostname[1])

    def runServer(self):
        @self.app.route("/")
        def home():
            return "connected"

        @self.app.route("/checkClient", methods=['POST'])
        def checkClientHandler():
            clientname = str(request.json['clientname'])
            return jsonify(clientname in self.clients.keys())

        @self.app.route("/initializeGroup", methods=['POST'])
        def initializeGroupHandler():
            groupName = str(request.json['groupName'])
            clientList = list(request.json['clientList'])

            if(not(groupName in self.groups.keys()) and self.existingconnections == self.connections):
                self.groups[groupName] = [clientList, [Queue() for _ in range(0, len(clientList))]]
                return Response(status=200)
            else:
                return Response(status=400)

        @self.app.route("/initialize", methods=['POST'])
        def initializeHandler():
            clientname = str(request.json['clientname'])
            password = str(request.json['password'])

            if(not(clientname in self.clients.keys()) and self.existingconnections < self.connections):
                self.clients[clientname] = [password, Queue()]
                self.existingconnections += 1
                return jsonify(
                    [self.existingconnections, self.connections])
            elif(clientname in self.clients.keys() and self.clients[clientname][0] != password or (self.existingconnections == self.connections)):
                return Response(status=400)
            elif(clientname in self.clients.keys() and self.clients[clientname][0] == password and self.existingconnections < self.connections):
                return jsonify(
                    [self.existingconnections, self.connections])

            return Response(status=400)

        @self.app.route("/sendmessage", methods=['POST'])
        def sendHandler():
            recipient = str(request.json['recipient'])
            message = str(request.json['message'])
            sender = str(request.json['clientname'])
            clientPassword = str(request.json['password'])

            if sender in self.clients.keys() and (self.clients[sender])[0] == clientPassword and recipient in self.clients.keys() and self.existingconnections == self.connections:
                # list form = [sender, message]
                self.clients[recipient][-1].put([sender, message])
                return Response(status=200)
            else:
                return Response(status=400)

            return Response(status=400)
        
        @self.app.route("/sendGroupMessage", methods=['POST'])
        def sendGroupMessageHandler():
            sender = str(request.json['clientname'])
            clientPassword = str(request.json['password'])
            message = str(request.json['message'])
            groupName = str(request.json['groupName'])

            if sender in self.clients.keys() and (self.clients[sender])[0] == clientPassword and self.connections == self.existingconnections:
                clientList = (self.groups[groupName])[0]
                if groupName in self.groups.keys() and sender in clientList:
                    for queue in (self.groups[groupName])[-1]:
                        queue.put([sender, message])

                    return Response(status=200)
                else:
                    return Response(status=400)
            else:
                return Response(status=400)
            

        @self.app.route("/getmessage", methods=['POST'])
        def getHandler():
            clientname = str(request.json['clientname'])
            password = str(request.json['password'])
            number = str(request.json['number'])

            messages = []
            if clientname in self.clients.keys() and (self.clients[clientname])[0] == password and self.existingconnections == self.connections:
                for i in range(0, int(number)):
                    messages.append(self.clients[clientname][-1].get())

                return jsonify(messages)
            else:
                return Response(status=403)

            return Response(status=403)
        
        @self.app.route("/getGroupMessage", methods=['POST'])
        def getGroupMessageHandler():
            clientname = str(request.json['clientname'])
            password = str(request.json['password'])
            groupName = str(request.json['groupName'])
            number = str(request.json['number'])

            number = int(number)
            if clientname in self.clients.keys() and (self.clients[clientname])[0] == password and self.existingconnections == self.connections:
                if groupName in self.groups.keys() and clientname in (self.groups[groupName])[0]:
                    messages = []

                    clientQueueLocation: int = int(
                        (self.groups[groupName])[0].index(clientname)
                    )

                    clientMessageQueue: Queue = ((self.groups[groupName])[-1])[clientQueueLocation]

                    for i in range(0, int(number)):
                        messages.append(clientMessageQueue.get())
                    
                    return jsonify(messages)
            
            return Response(status=403)
        
        @self.app.route("/reset", methods=["POST"])
        def resetHandler():
            clientname = str(request.json['clientname'])
            password = str(request.json['password'])

            if clientname in self.clients.keys() and (self.clients[clientname])[0] == password and self.existingconnections == self.connections:
                self.existingconnections = 0
                self.clients = {}
                self.groups = {}
                    
                return Response(status=200)
            else:
                return Response(status=400)

            return Response(status=400)



        self.app.run(port=int(self.port), host=str(self.host))


class Client:
    def __init__(self, url, name, password):
        self.url = str(url)
        self.name = str(name)
        self.password = str(password)
        self.initialized = int(self.__initialize())
        if self.initialized == 1:
            raise Exception(
                "The client could not be initialized!"
            )

    def __initialize(self):
        init_url = self.url + "initialize"
        session = requests.Session()

        information = []
        initialized = 1
        waiting = 1
        num_requests_made = 0

        while(True):
            postData = {
                "clientname": str(self.name),
                "password": str(self.password)
            }
            response = session.post(init_url, json=postData)

            num_requests_made += 1

            if response.status_code == 200:
                initialized = 0
                waiting = 1

                information = response.json()
                if information[0] < information[1]:
                    waiting = 1
                    sleep(2)
                elif information[0] == information[1]:
                    waiting = 0
                    break
            elif response.status_code == 400:
                if num_requests_made == 1:
                    initialized = 1
                    return initialized
                elif num_requests_made > 1 and initialized == 0:
                    waiting = 0
                    break

        return initialized

    def sendMessage(self, recipient, message):
        send_url = self.url + "sendmessage"

        postData = {
            "recipient": str(recipient),
            "message": str(message),
            "clientname": str(self.name),
            "password": str(self.password)
        }
        response = requests.post(
            send_url, json=postData)
        if response.status_code == 400:
            return 1  # Error and exit
        else:
            return 0  # Clean exit

    def sendGroupMessage(self, groupName: str, message: str):
        send_url = self.url + "sendGroupMessage"

        postData = {
            "clientname": self.name,
            "password": self.password,
            "message": message,
            "groupName": groupName
        }

        response = requests.post(send_url, json=postData)
        if response.status_code == 400:
            return 1 # Error and exit
        else:
            return 0 # Clean exit 

    def getMessage(self, number: int):
        get_url = self.url + "getmessage"

        postData = {
            "clientname": str(self.name),
            "password": str(self.password),
            "number": str(number)
        }
        response = requests.post(get_url, json=postData)
        if response.status_code == 403:
            return 1  # Error and exit
        else:
            return response.json()  # return the list of messages
    
    def getGroupMessage(self, groupName: str, number: int):
        get_url = self.url + "getGroupMessage"

        postData = {
            "clientname": str(self.name),
            "password": str(self.password),
            "groupName": str(groupName),
            "number": str(number)
        }

        response = requests.post(get_url, json=postData)

        if response.status_code == 403 or response.status_code == 400:
            return 1 # Error and exit
        else:
            return response.json()
    
    def resetServer(self) -> int:
        reset_url = self.url + "reset"

        postData = {
            "clientname": str(self.name),
            "password": str(self.password)
        }

        response = requests.post(reset_url, json=postData)

        if response.status_code == 200:
            return 0 # Clean exit
        else:
            return 1 # Error and exit
        
        return 1
    
    def reinitialize(self):
        initialized = self.__initialize()
        if initialized == 1:
            raise Exception(
                "The client could not be initialized!"
            )


class Group:
    def __init__(self, url: str, name: str, clientnames: list):
        self.url = url
        self.name = name
        self.clientnames = clientnames
        self.__checkDuplicates()
        self.__checkClients()
        self.__initializeGroup()

    def __checkDuplicates(self):
        repeated = []
        for i in range(0, len(self.clientnames)):
            for j in range(i + 1, len(self.clientnames)):
                if self.clientnames[i] == self.clientnames[j] and self.clientnames[i] not in repeated:
                    repeated.append(self.clientnames[i])

        if len(repeated) > 0:
            error_string = "1 or more clients have been repeated. They are: "
            for i in range(0, len(repeated)):
                if(i == len(repeated) - 1 and i != 0):
                    error_string += ("and " + repeated[i] + ".")
                elif(i != (len(repeated) - 1)):
                    error_string += (repeated[i] + ",")
                else:
                    error_string += (repeated[i])
            raise ValueError(error_string)

    def __checkClients(self):

        for clientname in self.clientnames:
            self.__checkClient(clientname)

    def __checkClient(self, clientname: str):
        check_url = self.url + "checkClient"

        postData = {
            "clientname": clientname
        }

        response = requests.post(check_url, json=postData)
        if response.json() == False:
            raise ValueError(
                clientname + " has not been initialized yet. Please only provide clients that have been initialized"
            )

    def __initializeGroup(self):
        init_url = self.url + "initializeGroup"

        postData = {
            "groupName": str(self.name),
            "clientList": list(self.clientnames)
        }

        response = requests.post(init_url, json=postData)

        if response.status_code != 200:
            error_string = '''Group was unable to be initialized because of 1 of 2 reasons: \n
            1) There is already a group with this name.\n
            2) The number of connections have not been fullfilled yet.'''
            raise Exception(error_string)
