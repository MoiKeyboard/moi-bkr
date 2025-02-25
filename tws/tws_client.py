from ib_insync import IB, Position

class TWSClient:
    def __init__(self, host='127.0.0.1', port=7496, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()

    def connect(self):
        """Connects to IBKR TWS."""
        self.ib.connect(self.host, self.port, self.client_id)
        print("Connected to TWS.")

    def get_positions(self):
        """Fetches current positions."""
        positions = self.ib.positions()
        return [
            {
                "symbol": pos.contract.symbol,
                "quantity": pos.position,
                "avg_price": pos.avgCost
            }
            for pos in positions
        ]

    def disconnect(self):
        """Disconnects from IBKR."""
        self.ib.disconnect()
        print("Disconnected from TWS.")
