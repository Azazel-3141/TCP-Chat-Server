import datetime
import asyncio
import aioconsole
import json
from rich import print

# Console Client V1

class Client():
    """Client class for handling information about the host, port, username, and if it is connected"""
    def __init__(self):
        self.host = 'localhost' # you can change this, but your network may have closed ports or be blocked off through Vlans
        self.port = 8080 
        self.username = None
        self.writer = None
        self.reader = None
        self.connected = False
        self.logged_in = False

    async def leave(self):
        self.connected = False
        if not self.writer.is_closing():
            self.writer.close()
            await self.writer.wait_closed()

    #trys to connect to server until succesful
    async def connect(self):
        while self.connected == False:
            print('Connecting...')
            try:
                self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
                print(f"Connected to {self.writer.get_extra_info('peername')}\n")
                self.connected = True
                return
            except ConnectionRefusedError:
                continue
        
    async def login(self):
        while self.logged_in == False:
            self.username = input('Username: ')
            password = input('Password: ')
            data = (json.dumps({'username':self.username, 'password':password})+'\n').encode()
            self.writer.write(data)
            await self.writer.drain()
            self.logged_in = True
            await self.receive_data()
            await self.receive_data()

    @staticmethod
    async def get_time():
        time = datetime.datetime.now()
        return (time.strftime("%m/%d/%Y %#I:%M %p"))
    
    async def send_message(self, message):
        data = (json.dumps({'message':message})+'\n').encode()
        self.writer.write(data)
        await self.writer.drain()

    async def format_message(self, message_data):
        message = message_data['message']
        message_type = message_data['message_type']
        sender = message_data['sender']
        target = message_data['target']

        if message_type == 'public':
            if sender == self.username:
                return (f"[blue]{self.username} : [white]{message}[/white] [grey37]{await self.get_time()}")
            elif sender == 'Server':
                return (f"[yellow]{sender} : [white]{message}[/white] [grey37]{await self.get_time()}")
            elif target == self.username:
                return (f"[red]{sender} : [white]{message} [grey37]{await self.get_time()}")

        elif message_type == 'private':
            if target == 'All':
                return (f"[ [blue]{self.username}[white] -> [red]All[white] ] : {message}[/white] [grey37]{await self.get_time()}")
            elif sender == 'Server':
                return (f"[ [yellow]{sender}[white] -> [blue]{self.username}[white] ] : {message}[/white] [grey37]{await self.get_time()}")
            elif target != sender and sender != self.username:
                return (f"[ [red]{sender}[white] -> [blue]{self.username}[white] ] : {message}[/white] [grey37]{await self.get_time()}")
            elif target != self.username and sender == self.username:
                return (f"[ [blue]{self.username}[white] -> [red]{target}[white] ] : {message}[/white] [grey37]{await self.get_time()}")

    async def receive_data(self):
        data = (await self.reader.readline()).decode()
        data = json.loads(data)
        return data

    async def client_handler(self):
        while self.logged_in:
            data = await self.receive_data()

            message = await self.format_message(data)
            print(message)

    async def receive_input(self):
        while self.logged_in:
            message = (await aioconsole.ainput())

            await self.send_message(message)
    
    async def run_client(self):
        await self.connect()
        await self.login()
        recieve_message = asyncio.create_task(client.client_handler())
        send_message = asyncio.create_task(client.receive_input())
        await asyncio.gather(recieve_message, send_message)

client = Client()
try:
    asyncio.run(client.run_client())
except Exception as e:
    print('Server has been disconnected!')
