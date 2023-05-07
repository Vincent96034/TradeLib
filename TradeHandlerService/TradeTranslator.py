import pandas as pd
from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class TradeHandler:
    """A class to handle portfolio rebalancing and generate trade instructions.

    Attributes:
        rebalance_frame (pd.DataFrame): A Pandas DataFrame containing the
            rebalanced weights, the absolute old and new values for each asset,
            and the change in value for each asset.
        trade_instructions (list): A list of dictionaries containing the ISIN,
            side ("buy" or "sell"), and order amount for each trade.

    Methods:
        create_rebalance_frame: Rebalances the portfolio based on the old and
            new weights and the current portfolio value.
        create_trade_instructions: Generates a list of trade instructions based
            on the rebalance DataFrame.
    """

    def __init__(self):
        self.rebalance_frame = None
        self.trade_instructions = None

    def create_rebalance_frame(self,
                               portfolio_dict: dict,
                               portfolio_value: float,
                               w_new: dict,
                               add_value: float = 0
                               ) -> pd.DataFrame:
        """Rebalances the portfolio based on the old and new weights and the
        current portfolio value.

        Args:
            portfolio_dict (dict): A dictionary containing the weights of each
                asset in the portfolio.
            portfolio_value (float): The current portfolio value.
            w_new (dict): A dictionary containing the new (target) weights of
                each asset in the portfolio.
            add_value (float, optional): An optional parameter to add to the
                total value of the portfolio. Defaults to 0.

        Returns:
            pd.DataFrame: A Pandas DataFrame containing the rebalanced weights,
            the absolute old and new values for each asset, and the change in
            value for each asset.
        """
        # pandas df for old portfolio
        w_old_df = pd.DataFrame.from_dict(portfolio_dict, orient="index")
        w_old_df.rename(columns={"w": "w_old"}, inplace=True)
        w_old_df["asset_id"] = w_old_df.index
        w_old_df.set_index("symbol", inplace=True)
        # pandas df for new (target portfolio)
        w_new_df = pd.DataFrame.from_dict(w_new, orient="index", columns=["w_new"])
        df = pd.concat([w_old_df, w_new_df], axis=1).fillna(0)
        df["abs_old"] = df.loc[:, "w_old"] * portfolio_value
        df["abs_new"] = df.loc[:, "w_new"] * (portfolio_value + add_value)
        df["delta"] = df.loc[:, "abs_new"] - df.loc[:, "abs_old"]
        self.rebalance_frame = df
        return df

    def create_trade_instructions(self):
        """Generates a list of trade instructions based on the rebalance
        DataFrame.

        Returns:
        list: A list of dictionaries containing the trade instructions for each
            asset. Each dictionary contains the following keys: 
                - symbol (str): 
                - side (str): The side of the trade, either "buy" or "sell"
                - quantity (float): The quantity of the asset to trade
                - quantity_type (str): The quantity type value
        Raises:
        TypeError: If the `rebalance_frame` attribute is not a Pandas
            DataFrame.
        ValueError: If the `rebalance_frame` does not contain a 'delta' column.
        """
        df = self.rebalance_frame
        # Input validation
        if not isinstance(df, pd.DataFrame):
            raise TypeError("rebalance_frame must be a Pandas DataFrame")
        if not all(col in df.columns for col in ["delta"]):
            raise ValueError("rebalance_frame must contain a 'delta' column")

        # Calculate absolute values
        df["abs_delta"] = df["delta"].abs()
        trade_instructions = [{"symbol": index,
                               "side": "buy" if row["delta"] > 0 else "sell",
                               "quantity": abs(row["delta"]),
                               "quantity_type": "value"} for index, row in df.iterrows()]

        self.trade_instructions = trade_instructions
        return trade_instructions
