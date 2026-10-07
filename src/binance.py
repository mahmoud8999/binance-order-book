import requests
import logging
import json
import config
import asyncio
import websockets
from websockets.exceptions import ConnectionClosed

class BinanceOrderBook:
    def __init__(self):
        self.uri = config.BINANCE_URI
        self.url = config.BINANCE_URL
        self.websocket = None
        self.bids = {}
        self.asks = {}
        self.last_update_id = None
        self.buffer = []
        self.receiver_task = None
        self.logger = logging.getLogger(__name__)
    
    async def rest_connect(self, symbol):
    
        results = {}
    
        params = {
            "symbol": symbol.upper(),
            "limit": config.DEPTH_LIMIT
        }
        
        try:
            response = await asyncio.to_thread(
                requests.get,
                config.BINANCE_URL,
                params=params
            )
            
            response.raise_for_status()
            
            data = response.json()
                        
            results["lastUpdateId"] = data["lastUpdateId"]
            results["bids"] = data["bids"]
            results["asks"] = data["asks"]
            
            return results
        
        except Exception as error:
            print(f"REST error: {error}")
        
    async def websocket_connect(self):
    
        retry_delay = config.RETRY_DELAY
    
        while True:
            try:
                self.logger.info("Connecting to Binance Websocket")
                self.websocket = await websockets.connect(
                    self.uri,
                    ping_interval = config.PING_INTERVAL,
                    ping_timeout = config.PING_TIMEOUT
                )
                self.logger.info("Connected to Binance Websocket")
                print("CONNECTED")
                return
            except Exception as error:
                self.websocket = None
                self.logger.info(f"Binance WebSocket Connection Failed: {error}")
                self.logger.info(f"Retrying in {retry_delay} seconds")
                print(f"RETRYING TO CONNECT IN {retry_delay} SECONDS")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, config.MAX_RETRY_DELAY)
                
    async def websocket_receive(self):
        async for message in self.websocket:
            yield message
    
    async def websocket_receive_updates(self):
        async for message in self.websocket_receive():
            data = json.loads(message)
            
            if data.get("e") == "depthUpdate":
                self.buffer.append(data)
                
    async def initialize_local_order_book(self, symbols):
        
        if self.receiver_task is None or self.receiver_task.done():
            self.receiver_task = asyncio.create_task(
                self.websocket_receive_updates()
            )
        
        snapshot = await self.rest_connect(symbols[0])
        
        rest_lastUpdatedID = snapshot["lastUpdateId"]
        rest_bids = snapshot["bids"]
        rest_asks = snapshot["asks"]
        
        synchronized_index = None
        needed_update = rest_lastUpdatedID + 1
        
        while synchronized_index is None:
            
            for index, update in enumerate(self.buffer):
                websocket_first = update["U"]
                websocket_last = update["u"]
                
                if websocket_last < needed_update:
                    continue
                elif websocket_first <= needed_update <= websocket_last:
                    synchronized_index = index
                    self.bids = dict(rest_bids)
                    self.asks = dict(rest_asks)
                    break
                elif websocket_first > needed_update:
                    snapshot = await self.rest_connect(symbols[0])
                
                    rest_lastUpdatedID = snapshot["lastUpdateId"]
                    rest_bids = snapshot["bids"]
                    rest_asks = snapshot["asks"]
                
                    needed_update = rest_lastUpdatedID + 1
                    break
            
            if synchronized_index is None:
                await asyncio.sleep(0.1)
                
        synchronized_update = self.buffer[synchronized_index]
        
        self.update_local_order_book(synchronized_update)
        
        del self.buffer[:synchronized_index + 1]
                
    def update_local_order_book(self, update):
        
        bids_updates = update["b"]
        asks_updates = update["a"]
        
        for bid_price, bid_quantity in bids_updates:
            if float(bid_quantity) == 0:
                self.bids.pop(bid_price, None)
            else:
                self.bids[bid_price] = bid_quantity
                
        for ask_price, ask_quantity in asks_updates:
            if float(ask_quantity) == 0:
                self.asks.pop(ask_price, None)
            else:
                self.asks[ask_price] = ask_quantity 
        
        self.last_update_id = update["u"]
        
    async def process_local_order_book(self, symbols):

        while True:
            if not self.buffer:
                await asyncio.sleep(0.1)
                continue

            update = self.buffer.pop(0)

            if update["u"] < self.last_update_id + 1:
                continue

            elif update["U"] <= self.last_update_id + 1 <= update["u"]:
                self.update_local_order_book(update)

                #print(
                #    f"UPDATED | U: {update['U']} | "
                #    f"u: {update['u']} | "
                #    f"last_update_id: {self.last_update_id}"
                #)

            else:
                print("GAP DETECTED - RESYNCHRONIZING")
                await self.initialize_local_order_book(symbols)
    
    def print_order_book(self, limit=10):

        top_bids = sorted(
            self.bids.items(),
            key=lambda item: float(item[0]),
            reverse=True
        )[:limit]

        top_asks = sorted(
            self.asks.items(),
            key=lambda item: float(item[0])
        )[:limit]

        # Clear terminal and move cursor to top-left
        print("\033[2J\033[H", end="")

        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                    BTCUSDT ORDER BOOK                        ║")
        print("╠═══════════════════════════════╦═══════════════════════════════╣")
        print("║             BIDS              ║             ASKS              ║")
        print("╠═══════════════╦═══════════════╬═══════════════╦═══════════════╣")
        print("║     PRICE     ║   QUANTITY    ║     PRICE     ║   QUANTITY    ║")
        print("╠═══════════════╬═══════════════╬═══════════════╬═══════════════╣")

        for i in range(limit):

            bid_price, bid_quantity = top_bids[i]
            ask_price, ask_quantity = top_asks[i]

            print(
                f"║ {float(bid_price):>13.2f} "
                f"║ {float(bid_quantity):>13.6f} "
                f"║ {float(ask_price):>13.2f} "
                f"║ {float(ask_quantity):>13.6f} ║"
        )

        print("╚═══════════════╩═══════════════╩═══════════════╩═══════════════╝")

        if top_bids and top_asks:
            best_bid = float(top_bids[0][0])
            best_ask = float(top_asks[0][0])
            spread = best_ask - best_bid

            print()
            print(
                f"Best Bid: {best_bid:.2f}  │  "
                f"Best Ask: {best_ask:.2f}  │  "
                f"Spread: {spread:.2f}  │  "
                f"Update ID: {self.last_update_id}"
            )
            
    async def display_order_book(self, limit=10, interval=1):

        while True:
            self.print_order_book(limit)
            await asyncio.sleep(interval)
            
    async def websocket_subscribe(self, symbols):
        
        if self.websocket is None:
            return
            
        streams = [
            f"{symbol.lower()}@depth@100ms"
            for symbol in symbols
        ]
        
        subscribe = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": 1
        }
        
        try:
            await self.websocket.send(json.dumps(subscribe))
            print("SUBSCRIPTION SENT")
        except ConnectionClosed:
            self.logger.warning(
                "Cannot subscribe: WebSocket connection is closed."
            )
        
    async def websocket_unsubscribe(self, symbols):
        
        if self.websocket is None:
            return
            
        streams = [
            f"{symbol.lower()}@depth@100ms"
            for symbol in symbols
        ]
        
        unsubscribe = {
            "method": "UNSUBSCRIBE",
            "params": streams,
            "id": 2
        }
        
        try:
            await self.websocket.send(json.dumps(unsubscribe))
            print("UNSUBSCRIBE SENT")
        except ConnectionClosed:
            self.logger.warning(
                "Cannot unsubscribe: WebSocket connection is closed."
            )
                
    async def websocket_disconnect(self):
        if self.websocket is None:
            return
            
        await self.websocket.close(code=1000, reason="User closed connection")
        self.websocket = None
        print("DISCONNECTED")
