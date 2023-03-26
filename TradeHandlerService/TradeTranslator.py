from TradeHandlerService.LemonClass import Lemon
from UserSettings.Configuration import RunConfiguration
import pandas as pd



class TradeHandler:

    def __init__(self, config: RunConfiguration, lemon: Lemon):
        self.config = config
        self.lemon = lemon
        self.rebalance_frame = None
        self.trade_instructions = None


    def create_rebalance_frame(self, w_new: dict, add_value: float = 0) -> pd.DataFrame:
        '''
        Rebalances the portfolio based on the old and new weights and the current portfolio value.

        Parameters:
        w_new (dict): A dictionary containing the new (target) weights of each asset in the portfolio.
        add_value (float, optional): An optional parameter to add to the total value of the portfolio. Defaults to 0.

        Returns:
        pd.DataFrame: A Pandas DataFrame containing the rebalanced weights, the absolute old and new values for each asset,
        and the change in value for each asset.
        '''
        # pandas df for old portfolio
        pf, pf_value = self.lemon.get_portfolio()
        w_old_df = pd.DataFrame.from_dict(pf, orient = "index")
        w_old_df.rename(columns = {"w": "w_old"}, inplace = True)
        # pandas df for new (target portfolio)
        w_new_df = pd.DataFrame.from_dict(w_new, orient = "index")
        w_new_df.rename(columns = {0: "w_new"}, inplace = True)
        
        df = pd.concat([w_old_df, w_new_df], axis=1).fillna(0)
        df["abs_old"] = df.loc[:,"w_old"] * pf_value
        df["abs_new"] = df.loc[:,"w_new"] * pf_value + add_value
        df["delta"] = df.loc[:,"abs_new"] - df.loc[:,"abs_old"]
        # TODO: change types to int
        self.rebalance_frame = df
        return df
        

    def create_trade_instructions(self):
        '''
        Generates a list of trade instructions based on the rebalance DataFrame.

        Returns:
        list: A list of dictionaries containing the ISIN, side ("buy" or "sell"), and order amount for each trade.
        '''
        df = self.rebalance_frame
        # Input validation
        if not isinstance(df, pd.DataFrame):
            raise TypeError("rebalance_frame must be a Pandas DataFrame")
        if not all(col in df.columns for col in ["delta"]):
            raise ValueError("rebalance_frame must contain a 'delta' column")

        # Calculate absolute values
        df["abs_delta"] = df["delta"].abs()
        trade_instructions = [{"isin": index, "side": "buy" if row["delta"] > 0 else "sell", "quantity": abs(row["delta"]), "quantity_type": "value"} \
                                for index, row in df.iterrows()]
        
        self.trade_instructions = trade_instructions
        return trade_instructions