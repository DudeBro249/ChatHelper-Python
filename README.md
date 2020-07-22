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
You can find the documentation for this package [here](https://github.com/DudeBro249/ChatHelper-Python/wiki)


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[Apache License 2.0](https://choosealicense.com/licenses/apache-2.0/)