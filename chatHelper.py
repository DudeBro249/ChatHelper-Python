from flask import Flask, Response, jsonify, request
import requests
from queue import Queue, Empty
import json
from threading import Thread
import time


class Server:
    
    @classmethod
    def createApp(cls, connections: int):
        app = Flask(__name__)

        app.config['EXISTINGCONNECTIONS'] = 0
        app.config['CLIENTS'] = {}
        app.config['GROUPS'] = {}
        if(connections == 0):
            raise Exception('connections cannot be 0!')
        else:
            app.config['CONNECTIONS'] = connections

        @app.route("/")
        def home():
            return "connected"

        @app.route("/checkClient", methods=["POST"])
        def checkClientHandler():
            clientname = str(request.json['clientname'])
            return jsonify(clientname in app.config['CLIENTS'].keys())

        @app.route("/initializeGroup", methods=["POST"])
        def initializeGroupHandler():
            data = request.get_json()
            groupName = str(data['groupName'])
            clientList = list(data['clientList'])

            if (groupName not in app.config['GROUPS'].keys()) and app.config['CONNECTIONS'] == app.config['EXISTINGCONNECTIONS']:
                app.config['GROUPS'][groupName] = clientList
                return Response(status=200)
            else:
                return Response(status=400)

        @app.route("/initialize", methods=['GET'])
        def initializeHandler():
            [clientname, password] = list(request.headers.get('Authorization').split(':'))

            def event_stream():
                while True:
                    if app.config['EXISTINGCONNECTIONS'] == app.config['CONNECTIONS']:
                        yield json.dumps({
                            "message": "ready"
                        })
                        break
                    else:
                        data = json.dumps({"message": "not ready"})
                        yield f'{data}\n\n'
                        time.sleep(3)
                
            isReady = (app.config['CONNECTIONS'] == app.config['EXISTINGCONNECTIONS'])

            if(not(clientname in app.config['CLIENTS'].keys()) and isReady == False):
                app.config['CLIENTS'][clientname] = [password, Queue()]
                app.config['EXISTINGCONNECTIONS'] = app.config['EXISTINGCONNECTIONS'] + 1
                return Response(event_stream(), status=200)
            else:
                return Response(status=400)

        @app.route("/sendmessage", methods=['POST'])
        def sendHandler():
            [author, password] = list(request.headers.get('Authorization').split(':'))
            data = request.get_json()
            recipient = str(data['recipient'])
            message = str(data['message'])

            authorized = (author in app.config['CLIENTS'].keys() and app.config['CLIENTS'][author][0] == password)
            isReady = (app.config['CONNECTIONS'] == app.config['EXISTINGCONNECTIONS'])

            if authorized and recipient in app.config['CLIENTS'].keys() and isReady:
                # list form = [sender, message, isGroupMessage]
                app.config['CLIENTS'][recipient][-1].put([author, message, False])
                return Response(status=200)
            else:
                return Response(status=400)

        
        @app.route("/sendGroupMessage", methods=['POST'])
        def sendGroupMessageHandler():
            [sender, password] = list(request.headers.get('Authorization').split(':'))
            data = request.get_json()
            message = str(data['message'])
            groupName = str(data['groupName'])

            authorized = (sender in app.config['CLIENTS'].keys() and app.config['CLIENTS'][sender][0] == password)
            isReady = (app.config['CONNECTIONS'] == app.config['EXISTINGCONNECTIONS'])

            if authorized and isReady:
                clientList: list = app.config['GROUPS'][groupName]
                for client in clientList:
                    if client != sender:
                        app.config['CLIENTS'][client][-1].put([
                            sender, message, True, groupName
                        ])

                return Response(status=200)
            else:
                return Response(status=400)

        
        @app.route("/reset", methods=["GET"])
        def resetHandler():
            [clientname, password] = list(request.headers.get('Authorization').split(':'))

            authorized = (clientname in app.config['CLIENTS'].keys() and app.config['CLIENTS'][clientname][0] == password)
            isReady = (app.config['CONNECTIONS'] == app.config['EXISTINGCONNECTIONS'])

            if authorized and isReady:
                app.config['EXISTINGCONNECTIONS'] = 0
                app.config['CLIENTS'] = {}
                app.config['GROUPS'] = {}
                    
                return Response(status=200)
            else:
                return Response(status=400)
        
        @app.route("/listen", methods=['GET'])
        def listenHandler():
            [clientname, password] = list(request.headers.get('Authorization').split(':'))

            def event_stream():
                clientQueue: Queue = app.config['CLIENTS'][clientname][-1]
                while True:
                    try:
                        messages = json.dumps(clientQueue.get(block=False))
                    except Empty as e:
                        messages = 'no messages'
                    yield f'data: {messages}\n\n'
                    time.sleep(0.25)
            
            authorized = (clientname in app.config['CLIENTS'].keys() and app.config['CLIENTS'][clientname][0] == password)
            isReady = (app.config['CONNECTIONS'] == app.config['EXISTINGCONNECTIONS'])
            
            if authorized and isReady:
                return Response(event_stream(), status=200)
            else:
                return Response(status=403)
        
        return app


class Client:
    url: str = None
    name: str = None
    password: str = None
    initialized: int = None
    __stop_listening: bool = None

    def __init__(self, url, name, password):
        self.__stop_listening = False
        self.url = str(url)
        self.name = str(name)
        self.password = str(password)

        self.__validate()
        self.__initialize()
    
    def __validate(self):
        if ':' in self.name or ':' in self.password:
            raise Exception(
                "The name and password parameters cannot have a colon!"
            )

    def __initialize(self):
        init_url = self.url + "initialize"

        headers = {
            'Authorization': f'{self.name}:{self.password}'
        }

        while True:
            response = requests.get(init_url, headers=headers)
            if response.status_code != 200:
                raise Exception(
                    "The client could not be initialized!"
                )
            
            responseList = response.text.split('\n\n')
            responseList = [json.loads(responseList[i]) for i in range(0, len(responseList))]
            if responseList[-1]['message'] == 'ready':
                break

            
        


    def sendMessage(self, recipient, message):
        send_url = self.url + "sendmessage"

        headers = {
            'Authorization': f'{self.name}:{self.password}'
        }
        postData = {
            "recipient": str(recipient),
            "message": str(message),
        }

        response = requests.post(
            send_url, json=postData, headers=headers)
        if response.status_code == 200:
            return 0  # Clean exit
        else:
            return 1  # Error and exit

    def sendGroupMessage(self, groupName: str, message: str):
        send_url = self.url + "sendGroupMessage"

        headers = {
            'Authorization': f'{self.name}:{self.password}'
        }

        postData = {
            "message": str(message),
            "groupName": str(groupName)
        }

        response = requests.post(send_url, json=postData, headers=headers)
        if response.status_code == 400:
            return 1 # Error and exit
        else:
            return 0 # Clean exit


    def startListening(self, onMessage=None):
        if onMessage == None:
            raise Exception("The onMessage parameter of this function cannot be none. This parameter must also be a function")
        listen_url = self.url + 'listen'
        session = requests.Session()

        headers = {
            'Authorization': f'{self.name}:{self.password}'
        }
        
        def listen() -> None:
            response = session.get(listen_url, headers=headers, stream=True)
            count = 0
            buffer = ''
            for content in response.iter_content(decode_unicode=True):
                if self.__stop_listening == True:
                    return
                buffer += str(content)
                if str(content) == '\n':
                    if count > 0:
                        clean_buffer = buffer.replace('data: ', '')
                        clean_buffer = (clean_buffer[::-1].replace('\n\n', ''))[::-1]
                        if clean_buffer != 'no messages':
                            message_data = json.loads(clean_buffer)
                            
                            if len(message_data) < 4:
                                group_name = None
                            else:
                                group_name = message_data[3]

                            message_object = Message(
                                author=message_data[0],
                                content=message_data[1],
                                is_group_message=message_data[2],
                                group_name=group_name
                            )
                            onMessage(message_object)

                        buffer = ''
                        count = 0

                        
                    else:
                        count += 1
                

        
        listener_thread = Thread(target=listen)
        listener_thread.start()

 
    
    def resetServer(self) -> int:
        reset_url = self.url + "reset"

        headers = {
            'Authorization': f'{self.name}:{self.password}'
        }

        self.stopListening()
        response = requests.get(reset_url, headers=headers)

        if response.status_code == 200:
            return 0 # Clean exit
        else:
            return 1 # Error and exit
    
    def stopListening(self):
        self.__stop_listening = True
    
    
    def reinitialize(self):
        self.__initialize()


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


class Message:
    author: str = None
    content: str = None
    is_group_message: bool = None
    group_name: str = None
    def __init__(self, author, content, is_group_message, group_name=None):
        self.author = author
        self.content = content
        self.is_group_message = is_group_message
        self.group_name = group_name
