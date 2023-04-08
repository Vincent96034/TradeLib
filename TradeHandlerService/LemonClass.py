import pandas as pd
from lemon import api
from typing import Optional, Union
from decimal import Decimal, ROUND_HALF_UP

from UserSettings.Configuration import RunConfiguration
from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class Lemon:
    """ A wrapper class for accessing the LemonMarkets API, using the
    lemon.markets SDK: https://github.com/lemon-markets/sdk-python/

    Args:
        config (RunConfiguration): A RunConfiguration object containing the required
            API keys and configuration details for the LemonMarkets account.

    Attributes:
        client (lemon.markets.api.LemonMarkets): An API client for accessing LemonMarkets.
        bank_statements (list): A list of bank statements as BankStatement objects.
        statements (list): A list of position statements as Statement objects.
        positions (list): A list of Positions as Position objects.
        performance (list): A list of Performance objects.
        portfolio (list): A list of Portfolio objects.
        portfolio_value (float): The total value of the portfolio.
    """
    def __init__(self, config: RunConfiguration) -> None:
        self.config = config
        self.client = api.create(
            market_data_api_token=config.LM_data_key,
            trading_api_token=config.LM_trading_key,
            env=config.LM_trading_type)
        self.bank_statements = None
        self.statements = None
        self.positions = None
        self.performance = None
        self.portfolio = None
        self.portfolio_value = None
        self.account = None
        self.update_lemon()


    def get_bank_statements(self,
        type_: Optional[str] = None,
        from_: Optional[str] = "beginning"
        ) -> list:
        """Returns a list of bank statements as BankStatement objects.
    
        Args:
            type_ (Optional[str]): Type of bank statements. Defaults to None.
                Can be one of the following:
                    - "pay_in"
                    - "pay_out"
                    - "order_buy"
                    - "order_sell"
                    - "eod_balance"
                    - "dividend"
                    - "tax_refunded"
            from_ (Optional[str]): Filter for bank statements after a specific date.
                Format: "YYYY-MM-DD". Defaults to "beginning".
        
        Returns:
            list: A list of BankStatement objects.
        """
        response = self.client.trading.account.get_bank_statements(
            type = type_,
            from_ = from_)
        self.bank_statements = response.results
        return response.results


    def get_statements(self) -> list:
        """ Returns a list of position statements as Statement objects.
        A statement is a change event that occurs to your positions.
        
        Returns:
            list: A list of Statement objects.
        """
        response = self.client.trading.positions.get_statements()
        self.statements = response.results
        return response.results
    

    def get_positions(self,
        isin: Optional[str] = None
        ) -> list:
        """ Returns a list of Positions as Position objects.

        Args:
            isin (Optional[str], optional): isin of position. Defaults to None.

        Returns:
            list: A list of Position objects.
        """
        response = self.client.trading.positions.get(
            isin = isin)
        self.positions = response.results
        return response.results


    def get_performance(self,
        isin: Optional[str] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        sorting: Optional[str] = None
        ) -> list:
        """ Returns a list of Performance objects.
    
        Args:
            isin (Optional[str]): The ISIN of the position. Defaults to None.
            from_ (Optional[str]): The starting date (ISO format: "YYYY-MM-DD") for the performance data.
                Defaults to None.
            to (Optional[str]): The ending date (ISO format: "YYYY-MM-DD") for the performance data.
                Defaults to None.
            sorting (Optional[str]): The sorting order for the performance data.
                Valid values are "asc" and "desc". Defaults to None.
        
        Returns:
            list: A list of Performance objects.
        """
        response = self.client.trading.positions.get_performance(
            isin = isin,
            from_ = from_,
            to = to,
            sorting = sorting)
        self.performance = response.results
        return response.results
    

    def place_order(self,
        isin: str,
        side: str,
        quantity: Union[int, float],
        quantity_type: str,
        activate = False,
        **kwargs,
        ) -> dict:
        """ Places a trading order for a given ISIN with the specified side and quantity.

        Args:
            isin (str): The ISIN of the security to trade.
            side (str): The side of the trade, either "buy" or "sell".
            quantity (Union[int, float]): The quantity to trade.
            quantity_type (str): The type of quantity, either "amount" (number of stocks)
                or "value".
            activate (bool, optional): Whether to activate the order immediately. Defaults to False.
            **kwargs: Additional keyword arguments to pass to the order creation method.

        Returns:
            dict: A dictionary containing the order ID, order object, and whether the order
                was activated.

        Warnings:
            If the requested order quantity exceeds the available quantity of a security in
                the portfolio, the function will adjust the order quantity to the maximum
                available amount and log a warning.
            If the requested order quantity is less than or equal to zero, the function will
                dismiss the order and log a warning.

        Notes:
            If the `quantity_type` argument is "value", the function will convert the quantity
                from a monetary value to a number of stocks using the `value_to_amount` method.
        """
        # input validation
        if not isinstance(isin, str):
            raise TypeError("'isin' must be an string.")
        if not side in ["buy", "sell"]:
            raise ValueError("'side' must be either 'buy' or 'sell'.")
        if not isinstance(quantity, (float, int)):
            raise TypeError("'quantity' must be an float or integer.")
        if quantity < 0:
            raise ValueError("'quantity' must be a positive number.")
        if quantity_type not in ["amount", "value"]:
            raise ValueError("'quantity_type' must be either 'amount' or 'value'.")
        
        if quantity_type == "amount":
            order_amount = quantity
        else: # transform value to number of stocks
            order_amount = self.value_to_amount(isin=isin, side=side, value=quantity)

        if side == "sell": # check if portfolio holds enough of stock
            amount_available = self.portfolio.get(isin)["quantity"]
            if order_amount > amount_available:
                logger.warning(f"""Order quantity {order_amount} of {isin} exceeds available amount {amount_available}.
                    Order quantity will be adjusted to maximum available amount.""")
                order_amount = amount_available

        if order_amount <= 0:
            logger.warning(f"""Order quantity {order_amount} of {isin} is less than or equal to zero. 
                Order will be dismissed.""")
            return

        order = self.client.trading.orders.create(
            isin=isin,
            side=side,
            quantity=order_amount,
            expires_at=kwargs.get("expires_at"),
            stop_price=kwargs.get("stop_price"),
            limit_price=kwargs.get("limit_price"),
            notes=kwargs.get("notes"),
            idempotency=kwargs.get("idempotency")
        )
        # activate order
        order_id = order.results.id
        if activate and (order.results.status == "inactive"):
            activate_order = self.client.trading.orders.activate(order_id=order_id)
        logger.info(f"Order {order_id} placed{' and activated' if activate else ''}.")
        return {
            "order_id": order_id, 
            "order_obj": order,
            "activated": activate_order if activate else activate
        }
    

    def get_order(self,
        order_id: str
        ) -> list:
        """ Retrieves the status of a trading order with the specified order ID.

        Args:
            order_id (str): The ID of the trading order to retrieve.

        Returns:
            list: A list containing the order status.
        """
        order_status = self.client.trading.orders.get_order(order_id=order_id)
        return order_status.results


    def get_all_orders(self) -> list:
        """ Retrieves all trading orders placed by the user.

        Returns:
            list: A list containing the order objects for all placed orders.
        """
        response = self.client.trading.orders.get()
        # auto_iter: iterate over all orders of all pages
        return [order for order in response.auto_iter()]


    def cancel_order(self, order_id: str):
        """ Cancels a trading order with the specified order ID.

        Args:
            order_id (str): The ID of the trading order to cancel.
        """
        response = self.client.trading.orders.cancel(order_id=order_id)
        return response


    def get_portfolio(self) -> list:
        """ Retrieves the user's portfolio and its total value.

        Returns:
            Tuple[Dict[str, Dict[str, float]], float]: A tuple containing a dictionary
                with the user's portfolio where each key is an ISIN and the value is a
                dictionary with the keys "quantity", "buy_price_avg", "estimated_price_total",
                "estimated_price", and "w", and the total value of the portfolio.
        """
        positions = []
        for pos in self.get_positions():
            positions.append(
                [pos.isin, pos.quantity, pos.buy_price_avg, pos.estimated_price_total, pos.estimated_price]
            )
        positions = pd.DataFrame(positions, columns = ["isin","quantity","buy_price_avg","estimated_price_total","estimated_price"])
        pf_value = positions["estimated_price_total"].sum()
        positions["w"] = positions["estimated_price_total"] / pf_value
        portfolio = positions.set_index(["isin"]).to_dict(orient="index")

        self.portfolio = portfolio
        self.portfolio_value = pf_value
        return portfolio, pf_value


    def place_multi_order(self,
        order_list: list,
        activate: bool = True,
        ) -> dict:
        """ Creates multiple orders from a list of dictionaries.

        Args:
            order_list (list): A list of dictionaries, where each dictionary represents an order.
                Each order dictionary must contain the following keys: 'isin' (str), 'side' (str),
                'quantity' (float), 'quantity_type' (str).
            activate (bool, optional): Whether to activate the orders immediately after placing them.
                Defaults to True.

        Returns:
            dict: A dictionary containing the order ID, order object, and activation object.

        Raises:
            ValueError: If any of the orders in the list is missing a required key.
        """
        # Input validation
        order_responses = []
        for order in order_list:
            for key in ["isin", "side", "quantity", "quantity_type"]:
                if key not in order:
                    raise ValueError(f"Required key '{key}' is missing.")

            order_response = self.place_order(
                isin=order.get("isin"),
                side=order.get("side"),
                quantity=order.get("quantity"),
                quantity_type=order.get("quantity_type"),
                activate=activate or order.get("activate"),
                expires_at=order.get("expires_at"),
                stop_price=order.get("stop_price"),
                limit_price=order.get("limit_price"),
                notes=order.get("notes"),
                idempotency=order.get("idempotency")
            )
            order_responses.append(order_response)
        logger.info(f"Created {len([x for x in order_responses if x is not None])} orders.")
        return order_responses


    def get_latest_data(self, isin: str, **kwargs):
        """ Retrieves the latest market data for a given ISIN.

        Args:
            isin (str): The ISIN to retrieve the market data for.
            **kwargs: Additional optional parameters:
                - mic (str): The market identifier code to retrieve the market data for.
                - decimals (bool): Whether to return decimal values in the response.
                - epoch (bool): Whether to return timestamps in epoch format in the response.
                - sorting (str): The sorting order for the returned data.
                    Possible values are 'asc' or 'desc'.
                - limit (int): The maximum number of results to return.
                - page (int): The page number of the results to return.

        Returns:
            If the response contains a single result, returns a dictionary with the market
                data for the specified ISIN.
            If the response contains multiple results, returns a list of dictionaries, each
                containing the market data for a different timestamp.
        """
        response = self.client.market_data.quotes.get_latest(
            isin=isin,
            mic = kwargs.get("mic"),
            decimals = True or kwargs.get("decimals"),
            epoch = kwargs.get("epoch"),
            sorting = kwargs.get("sorting"),
            limit = kwargs.get("limit"),
            page = kwargs.get("page")
        )
        if len(response.results) == 1:
            return response.results[0]
        else:
            return response.results
        

    def value_to_amount(self, isin: str, side: str, value: Union[int, float]) -> int:
        """ Converts a value to the corresponding amount of stocks.

        Args:
            isin (str): The International Securities Identification Number (ISIN) of the stock.
            side (str): The transaction side, either "buy" or "sell".
            value (Union[int, float]): The value to convert to the corresponding amount of stocks.

        Returns:
            int: The amount of stocks that correspond to the given value.
        """
        quote_obj = self.get_latest_data(isin = isin)
        price = quote_obj.a if side == "buy" else quote_obj.b # ask or bid
        return int(Decimal(value/self.convert_to_hcents(price)).quantize(0, ROUND_HALF_UP))


    @staticmethod
    def convert_to_hcents(amount: float) -> int:
        """ Converts a currency amount to an integer value in hundreths of a cent.
        Example: 123.45 -> 1234500

        Args:
        amount (float): The amount of currency to convert.

        Returns:
        int: The converted amount in hundreths of a cent.
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a float or int value.")
        return int(amount * 10_000)


    def update_lemon(self):
        """
        Updates account data of Lemon object by calling the following methods:
        - get_performance
        - get_bank_statements
        - get_statements
        - get_positions
        - get_portfolio

        Returns: None
        """
        self.get_performance()
        self.get_bank_statements()
        self.get_statements()
        self.get_positions()
        self.get_portfolio()
        logger.info(f"Updated Lemon object attributes.")


    def init_account(self):
        self.account = LemonAccount(config = self.config)




class LemonAccount(Lemon):
    def __init__(self, config: RunConfiguration):
        super().__init__(config)

    def test(self):
        return self.config