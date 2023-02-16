from UserSettings.Configuration import RunConfiguration
from lemon import api
from typing import Optional
import pandas as pd


# lemon.markets SDK: https://github.com/lemon-markets/sdk-python/

'''
# TODO: add all necessary functions
- place order -> should also update class info like orders, positions, ...
- ...
'''


class Lemon:

    def __init__(self, config: RunConfiguration) -> None:
        self.client = api.create(
            market_data_api_token=config.LM_data_key,
            trading_api_token=config.LM_trading_key,
            env=config.LM_trading_type)
        self.bank_statements = None
        self.statements = None
        self.positions = None
        self.performance = None
        self.portfolio = None
        #self.update_lemon()


    def get_bank_statements(self,
        type_: Optional[str] = None,
        from_: Optional[str] = "beginning"
    ) -> list:
        '''
        Returns a list of bank statements as BankStatement objects.
        
        Optional arguments:
            type_ (str): Type of bank statements: pay_in | pay_out | order_buy | order_sell | eod_balance | dividend |tax_refunded
            from_ (str): Filter for bank statements after a specific date. Format: "YYYY-MM-DD"
        '''
        response = self.client.trading.account.get_bank_statements(
            type = type_,
            from_ = from_)
        return response.results


    def get_statements(self,
        type_: Optional[str] = None
    ) -> list:
        '''
        Returns a list of (position) statements as Statement objects.
        A statement is a change events happening to your positions.
        
        Optional arguments:
            type_ (str): Type of bank statements: order_buy | order_sell | split | import | snx
        '''
        response = self.client.trading.positions.get_statements(
            type = type_)
        return response.results
    

    def get_positions(self,
        isin: Optional[str] = None
    ) -> list:
        '''
        Returns a list of Positions as Position objects.

        Optional arguments:
            isin (str): isin of position
        '''
        response = self.client.trading.positions.get(
            isin = isin)
        return response.results


    def get_performance(self,
        isin: Optional[str] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        sorting: Optional[str] = None
    ) -> list:
        '''
        Returns a list of Performance objects.
        
        Optional arguments:
            isin (str): isin of position
            from_ (str): ISO date string (YYYY-MM-DD)
            to (str): ISO date string (YYYY-MM-DD)
            sorting (str): sorted "asc" or "desc"
        '''
        response = self.client.trading.positions.get_performance(
            isin = isin,
            from_ = from_,
            to = to,
            sorting = sorting)
        return response.results


    def place_order(self,
        isin: str,
        side: str,
        quantity: int,
        activate = False,
        expires_at: Optional[str] = None,
        stop_price: Optional[float] = None,
        limit_price: Optional[float] = None,
        notes: Optional[str]= None,
        idempotency: Optional[str] = None
    ) -> dict:
        '''
        Place an order.
        
        Arguments:
            isin (str):
            side (str):
            quantity (int):

        Optional arguments:
            expires_at (str):
            stop_price (float):
            limit_price (float):
            notes (str):
            idempotency (str):
        '''
        order = self.client.trading.orders.create(
            isin=isin,
            side=side,
            quantity=quantity,
            expires_at=expires_at,
            stop_price=stop_price,
            limit_price=limit_price,
            notes=notes,
            idempotency=idempotency
        )
        # activate order
        order_id = order.results.id
        if activate & (order.results.status == "inactive"):
            activate_order = self.client.trading.orders.activate(order_id=order_id)
            print(activate_order)
        return {
            "order_id": order_id, 
            "order_obj": order,
            "activate_obj": activate_order
        }
        # TODO: log every order - how?
    

    def get_order(self,
        order_id: str
    ) -> list:
        ''' xxx '''
        order_status = self.client.trading.orders.get_order(order_id=order_id)
        return order_status.results


    def get_all_orders(self) -> list:
        ''' xxx '''
        # get orders
        response = self.client.trading.orders.get()
        # auto_iter: iterate over all orders of all pages
        return [order for order in response.auto_iter()]


    def cancel_order(self,
        order_id: str
    ):
        ''' xxx '''
        response = self.client.trading.orders.cancel(order_id=order_id)
        return response
        # TODO (type hint output) 


    def get_portfolio(self) -> list:
        ''' '''
        positions = []
        for pos in self.get_positions():
            positions.append(
                [pos.isin, pos.isin_title, pos.quantity, pos.buy_price_avg, pos.estimated_price_total, pos.estimated_price]
            )
        positions = pd.DataFrame(positions, columns = ["isin","title","quantity","buy_price_avg","estimated_price_total","estimated_price"])
        return positions
        # TODO: weights -> markt oder einkaufspreise? <- think about this!
        # dict with isin, weight, and portfolio value


    def update_lemon(self): # TODO
        ''' function writes account data to class '''
        self.performance = self.get_performance()
        self.bank_statements = self.get_bank_statements()
        self.statements = self.get_statements()
        self.positions = self.get_positions()
        self.portfolio = self.get_portfolio()