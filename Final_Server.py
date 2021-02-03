from simple_websocket_server import WebSocketServer, WebSocket
import asyncio
import websockets
import threading
import time
import requests
import os

API_KEY = os.getenv('API_KEY')

pages = 0
CHECK_PROCENT = 20

keywords = [
    "] Baby Yeti",
    "Dragon Claw",
    "Aspect of the Dragons",
    "Mana Flux",
    "Storm's Helmet",
    "Storm's Chestplate",
    "Storm's Leggings",
    "Storm's Boots",
    "Necron's Helmet",
    "Necron's Chestplate",
    "Necron's Leggings",
    "Necron's Boots",
    "Superior Dragon Helmet",
    "Superior Dragon Chestplate",
    "Superior Dragon Leggings",
    "Superior Dragon Boots",
    "Adaptive Helm",
    "Adaptive Chestplate",
    "Adaptive Leggings",
    "Adaptive Boots",
    "Pigman Sword",
    "] Parrot",
    "Shadow Assassin Helmet",
    "Shadow Assassin Chestplate",
    "Shadow Assassin Leggings",
    "Shadow Assassin Boots"
]

connections = []
duplicates = []
new_dupes = []

class Handler(threading.Thread):
    def getName(self, uuid):
        data = requests.get("https://sessionserver.mojang.com/session/minecraft/profile/" + uuid).json()
        return data["name"]

    def getItems(self, keyword, PAGES):
        items = []
        for page in PAGES:
            for pageItem in page:
                if keyword in pageItem['item_name']:
                    if 'bin' in pageItem and pageItem['bin'] == True:
                        items.append(pageItem)  
        return items

    def CheckPrice(self, keyword, PAGES):
        items = self.getItems(keyword, PAGES)
        lowest_price = 9999999999
        lowest_price_2 = 1
        lowest_item = {}
        prices = []
        for item in items:
            price = item['starting_bid']
            prices.append(price)
            if price < lowest_price:
                lowest_item = item
                lowest_price_2 = lowest_price
                lowest_price = price
            elif price < lowest_price_2:
                lowest_price_2 = price
        procent = 100-(lowest_price / lowest_price_2 * 100)
        if procent >= CHECK_PROCENT:
            global duplicates
            global new_dupes
            if duplicates.includes(lowest_item['auctioneer']):
                return False
            else:
                return lowest_item
            new_dupes.append(lowest_item['auctioneer'])
        else:
            return False

    async def LoadData(self):
        PAGES = []
        pageData = requests.get('https://api.hypixel.net/skyblock/auctions?page=0&key=' + API_KEY).json()
        PAGES.append(pageData['auctions'])
        pages = pageData['totalPages']
        for iPage in range(pages):
            if iPage % 5 == 0:
                for ws in connections:
                    ws.send_message("IDLE")
            try:
                PAGES.append(requests.get('https://api.hypixel.net/skyblock/auctions?page=' + str(iPage) + '&key=' + API_KEY).json()['auctions'])
            except:
                print("There was a problem while fetching the data, is the Hypixel Service down?")
        for keyword in keywords:
            getItem = self.CheckPrice(keyword, PAGES)
            if getItem != False:
                get_name = self.getName(getItem['auctioneer'])
                if len(connections) == 0:
                    print("No Connections")
                    return
                print(getItem)
                for ws in connections:
                    ws.send_message("ADD " + getItem['item_name'].replace(" ", "_") + " " + get_name + " " + getItem['tier'] + " " + str(getItem['starting_bid']) + " " + getItem['item_lore'].replace(" ", "_"))
    def run(self):
        while True:
            if len(connections) > 0:
                global duplicates
                global new_dupes
                duplicates = new_dupes
                new_dupes = []
                asyncio.run(self.LoadData())
            
            

class Server(WebSocket):
    def handle(self):
        self.send_message(self.data)

    def connected(self):
        print(self.address, 'connected')
        connections.append(self)

    def handle_close(self):
        print(self.address, 'closed')
        connections.remove(self)

print("Listening on PORT " + os.getenv('PORT') + " ...")
handler = Handler()
handler.start()
server = WebSocketServer("", os.getenv('PORT'), Server)
server.serve_forever()
    


