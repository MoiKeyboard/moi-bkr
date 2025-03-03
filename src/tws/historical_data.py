from datetime import datetime, timedelta
from ib_insync import util
import pandas as pd

class HistoricalData:
    def __init__(self, tws_client, **kwargs):
        """
        Initialize with an existing TWS client
        
        Args:
            tws_client: An instance of TWSClient that's already connected
            
        Optional kwargs:
            default_exchange (str): Default exchange to use (default 'SMART')
            default_currency (str): Default currency to use (default 'USD')
            default_duration (str): Default time duration (default '1 Y')
            default_bar_size (str): Default bar size (default '1 day')
            default_what_to_show (str): Default data type (default 'TRADES')
            default_use_rth (bool): Default regular trading hours setting (default True)
        """
        self.tws_client = tws_client
        self.default_exchange = kwargs.get('default_exchange', 'SMART')
        self.default_currency = kwargs.get('default_currency', 'USD')
        self.default_duration = kwargs.get('default_duration', '1 Y')
        self.default_bar_size = kwargs.get('default_bar_size', '1 day')
        self.default_what_to_show = kwargs.get('default_what_to_show', 'TRADES')
        self.default_use_rth = kwargs.get('default_use_rth', True)
        
    def get_historical_data(self, contract, **kwargs):
        """
        Fetch historical data for the specified contract
        
        Args:
            contract: IB contract object (Stock, Future, Option, etc.)
            
        Optional kwargs:
            duration (str): Time duration to fetch (default from init)
            bar_size (str): Size of bars (default from init)
            what_to_show (str): Type of data (default from init)
            use_rth (bool): Use regular trading hours only (default from init)
            end_datetime (str): End date/time of data (default: now)
            
        Returns:
            DataFrame with historical data
        """
        # Use default values if parameters not specified
        duration = kwargs.get('duration', self.default_duration)
        bar_size = kwargs.get('bar_size', self.default_bar_size)
        what_to_show = kwargs.get('what_to_show', self.default_what_to_show)
        use_rth = kwargs.get('use_rth', self.default_use_rth)
        end_datetime = kwargs.get('end_datetime', '')
        
        # Make sure the contract is qualified
        self.tws_client.ib.qualifyContracts(contract)
        
        # Request historical data
        bars = self.tws_client.ib.reqHistoricalData(
            contract=contract,
            endDateTime=end_datetime,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=use_rth,
            formatDate=1
        )
        
        # Convert to DataFrame
        if bars:
            df = util.df(bars)
            
            # Standardize column names to match required format
            df_formatted = pd.DataFrame()
            df_formatted['Date'] = pd.to_datetime(df['date'])
            df_formatted['Open'] = df['open']
            df_formatted['High'] = df['high']
            df_formatted['Low'] = df['low']
            df_formatted['Close'] = df['close']
            df_formatted['Volume'] = df['volume']
            
            return df_formatted
        else:
            return pd.DataFrame()  # Return empty DataFrame if no data is found

    def save_historical_data(self, contract, filename, **kwargs):
        """
        Fetch historical data and save it to a CSV file
        
        Args:
            contract: IB contract object (Stock, Future, Option, etc.)
            filename (str): Path to save the CSV file
        """
        df = self.get_historical_data(contract, **kwargs)
        if not df.empty:
            df.to_csv(filename, index=False)
            print(f"Saved historical data to {filename}")
        else:
            print("No data found to save.")