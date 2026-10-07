import asyncio

from src.binance import BinanceOrderBook

async def main():

    binance = BinanceOrderBook()
    symbols = ["BTCUSDT"]

    # 1. Connect
    await binance.websocket_connect()

    # 2. Subscribe
    await binance.websocket_subscribe(symbols)

    # 3. Synchronize REST snapshot + WebSocket
    await binance.initialize_local_order_book(symbols)

    print("ORDER BOOK SYNCHRONIZED")
    print(f"Last Update ID: {binance.last_update_id}")

    # 4. Process updates and display book concurrently
    await asyncio.gather(
        binance.process_local_order_book(symbols),
        binance.display_order_book(limit=10, interval=1)
    )
    
if __name__ == "__main__":
    asyncio.run(main())
