from __future__ import annotations

from UserSettings.Configuration import RunConfiguration
from lemon import api
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

import logging
logger = logging.getLogger(__name__)


# lemon.markets SDK: https://github.com/lemon-markets/sdk-python/


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
        self.portfolio_value = None
        self.update_lemon()


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


    def get_statements(self) -> list:
        '''
        Returns a list of (position) statements as Statement objects.
        A statement is a change events happening to your positions.
        
        Optional arguments:
            type_ (str): Type of bank statements: order_buy | order_sell | split | import | snx
        '''
        response = self.client.trading.positions.get_statements()
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
        return {
            "order_id": order_id, 
            "order_obj": order,
            "activate_obj": activate_order
        }
    

    def place_order_v2(self,
        isin: str,
        side: str,
        activate = False,
        **kwargs,
    ) -> dict:
        '''
        Place an order.
        
        Arguments:
            isin (str):
            side (str):
            quantity (int): Number of stocks to sell/buy.
            or order_amount (int): Total amount of order. (Example: 10€ -> 100000)

        Optional arguments:
            expires_at (str):
            stop_price (float):
            limit_price (float):
            notes (str):
            idempotency (str):
        '''
        order_amount = kwargs.get("order_amount")
        order_quantity = kwargs.get("quantity")
        if (order_amount == None) & (order_quantity == None):
            raise Exception("Please specify order_amount or quantity.")
        
        if (order_amount != None) & (order_quantity == None):
            # calulate quantity from value
            latest_price = self.get_latest_data(isin = isin)
            estimated_price = (latest_price.b + latest_price.a)/2
            _quantity = int(Decimal(order_amount/estimated_price).quantize(0, ROUND_HALF_UP))
        else:
            _quantity = None 
     
        order = self.client.trading.orders.create(
            isin=isin,
            side=side,
            quantity=_quantity or kwargs.get("quantity"),
            expires_at=kwargs.get("expires_at"),
            stop_price=kwargs.get("stop_price"),
            limit_price=kwargs.get("limit_price"),
            notes=kwargs.get("notes"),
            idempotency=kwargs.get("idempotency")
        )
        # activate order
        order_id = order.results.id
        if activate & (order.results.status == "inactive"):
            activate_order = self.client.trading.orders.activate(order_id=order_id)
        logger.info(f"Order {order_id} placed.")
        return {
            "order_id": order_id, 
            "order_obj": order,
            "activate_obj": activate_order
        }
    

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


    def get_portfolio(self) -> list:
        ''' '''
        positions = []
        for pos in self.get_positions():
            positions.append(
                [pos.isin, pos.isin_title, pos.quantity, pos.buy_price_avg, pos.estimated_price_total, pos.estimated_price]
            )
        # TODO: implement with numpy (vectors, ...)?
        positions = pd.DataFrame(positions, columns = ["isin","title","quantity","buy_price_avg","estimated_price_total","estimated_price"])
        pf_value = positions["estimated_price_total"].sum()
        positions["w"] = positions["estimated_price_total"] / pf_value
        portfolio = dict(zip(positions["isin"], positions["w"]))

        self.portfolio = portfolio
        self.portfolio_value = pf_value
        return portfolio, pf_value
        # dict with isin, weight, and portfolio value


    def place_multi_order(self,
        order_list: list,
        activate: bool = True,
    ) -> None:
        ''' convenience function to create multiple orders from list of dics ''' 
        for order in order_list:
            if (order.get("isin") == None) | \
                (order.get("side") == None) | \
                ((order.get("order_amount") == None) & (order.get("quantity") == None)):
                logger.warn(f"Order not placed, because of missing arguments!")
                continue

            order_response = self.place_order_v2(
                isin=order.get("isin"),
                side=order.get("side"),
                activate=activate or order.get("activate"),
                order_amount=order.get("order_amount"),
                quantity=order.get("quantity"),
                expires_at=order.get("expires_at"),
                stop_price=order.get("stop_price"),
                limit_price=order.get("limit_price"),
                notes=order.get("notes"),
                idempotency=order.get("idempotency")
            )
        logger.info(f"Created {len(order_list)} orders.")


    def get_latest_data(self, isin: str, **kwargs):
        ''' get market data for isin '''
        # get latest quotes
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




    def update_lemon(self): # TODO
        ''' function writes account data to class '''
        self.performance = self.get_performance()
        self.bank_statements = self.get_bank_statements()
        self.statements = self.get_statements()
        self.positions = self.get_positions()
        self.get_portfolio()
        logger.info(f"Updated Lemon object attributes.")