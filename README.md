# ChatHelper
High-level chat client Python API that makes sending messages between computers(using http) easy.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install chatHelper.

```bash
pip install chatHelper
```

## QuickStart

### Server

```python
from chatHelper import Server

server = Server("192.168.xx.xxx:8000", 1)
```

### Client

```python
from chatHelper import Client

client = Client("http://192.168.xx.xxx:8000/", "client1", "12345")
```

## Documentation

### Server

```python
from chatHelper import Server

server = Server(hostname: str, connections: int)
```
- hostname contains the host and the port that the server will be running on: string like "192.168.xx.xxx:8000"
-  connections is the number of connections that the server is meant to receive: integer like 2

Returns a Server object and starts the Flask server on your system

### Client

```python
from chatHelper import Client

client = Client(url: str, name: str, password: str)
```

This will initialize the client.
- The url parameter represents the url that the client should bind to(normally the url that the server is hosted on): string like "http://..."
- The name parameter is the name of the client: string like "client1"
- The password parameter is the password that the client uses to authorize itself to the server when
          getting and sending messages: string like "12345"
          
Returns a client object, and initializes it to the server.

```python
client.sendMessage(recipient: str, message: str) -> int
```
Sends a message to the recipient that is specified in the function
- recipient is the name of the client that you want to send a message to: string like "client2"
- message is the message you want to send to that client: any data type

Returns either 0(if the message was sent succesfully), or 1(error code).

```python
client.getMessage(number: int) -> Union[list, int]
```
Gets messages that were sent to the client
- number is the number of messages you want to receive: integer like 2

Returns a 2D list like this: [[sender, message], [sender, message], ...]
- sender is the string name of the client who sent the message
- message is the string message

```python
client.sendGroupMessage(groupName: str, message: str) -> int
```
Sends a message to a Group.
- groupName is the name of the group that you want to send the message to: string like "group1"
- message is the string message

Returns either 0(if the message was sent succesfully), or 1(error code).

```python
client.getGroupMessage(groupName: str, number: str) -> Union[list, int]
```
Gets a certain number of messages from the group that the client is part of
- groupName is the name of the group that you want to get the messages from: string like "group1"
- number is the number of messages you want to receive: integer like 2


### Group
```python
group = Group(url: str, name: str, clientnames: list)
```
Creates a group object so that clients send one message and have that message be sent to every client in the group, like a group chat.
- The url parameter represents the url that the group should bind to(normally the url that the server is hosted on): string like "http://...
- The name parameter is the name of the group1: string like "group1" or "myGroup"
- clientnames is a list of strings of the names of the clients that you want to have in the group: list like ["client1", "client2"]


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[Apache License 2.0](https://choosealicense.com/licenses/apache-2.0/)