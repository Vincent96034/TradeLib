import pandas as pd
from typing import Union, Optional

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetStatus
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLimitOrderRequest, TrailingStopOrderRequest

from TradeHandlerService.TradingBackends.trade_backend import TradeBackend
from TradeHandlerService.TradeData import Trade, Position


class Alpaca(TradeBackend):
    def __init__(self, AT_secret: str, AT_key: str, AT_paper: str):
        self.AT_secret = AT_secret
        self.AT_key = AT_key
        self.AT_paper = AT_paper
        self.trading_client = TradingClient(self.AT_key, self.AT_secret, paper=AT_paper)
        #self.broker_client = BrokerClient(self.AT_key, self.AT_secret)

    def get_account(self):
        return self.trading_client.get_account()
    
    def get_assets(self, active: bool=True, tradeable: bool=True):
        if active:
            asset_status = AssetStatus.ACTIVE
        else:
            asset_status = None
        search_params = GetAssetsRequest(status=asset_status)
        return self.trading_client.get_all_assets(search_params)

    def get_positions(self):
        # todo: return list of custom positions objects
        return self.trading_client.get_all_positions()
    
    def get_trades(self):
        # todo: return list of custom order objects
        return self.trading_client.get_orders()
    

    def place_order(self,
        symbol: str,
        side: str,
        quantity: Union[int, float],
        quantity_type: str,
        pf_dict: dict,
        order_type: str = "market_order",
        **kwargs,
        ) -> dict:
        #todo: input validation and check
        if quantity_type == "amount":
            qty = quantity
            notional = None
        elif quantity_type == "value":
            qty = None
            notional = quantity
        order_type_factory = {
            "market_order": self._market_order,
            "limit_order": self._limit_order,
            "stop_order": self._stop_order,
            "trailing_stop_order": self._trailing_stop_order
        }
        # todo: implement other input params
        # todo: check if enough funds are available
        order_data = order_type_factory.get(order_type)(
                symbol=symbol,
                side=side,
                qty=qty,
                notional=notional,
                time_in_force=kwargs.get("time_in_force") or TimeInForce.DAY,
                extended_hours=kwargs.get("extended_hours"),
                client_order_id=kwargs.get("client_order_id"),
                order_class=kwargs.get("order_class"),
                take_profit=kwargs.get("take_profit"),
                stop_loss=kwargs.get("stop_loss"),
                limit_price=kwargs.get("limit_price"),
                stop_price=kwargs.get("stop_price"),
                trail_price=kwargs.get("trail_price"),
                trail_percent=kwargs.get("trail_percent")
            )
        response = self.trading_client.submit_order(order_data=order_data)
        return {
            "order_id": str(response.id), 
            "order_obj": response
        }

    def place_multi_order(self):
        pass


    def _market_order(self, **kwargs):
        return MarketOrderRequest(
                        symbol=kwargs.get("symbol"),
                        qty=kwargs.get("qty"),
                        notional=kwargs.get("notional"),
                        side=self._get_side(kwargs.get("side")),
                        time_in_force=TimeInForce.DAY,
                        extended_hours=None,
                        client_order_id=None,
                        order_class=None,
                        take_profit=None,
                        stop_loss=None
                )
    
    def _limit_order(self, **kwargs):
        return LimitOrderRequest(
                        symbol=kwargs.get("symbol"),
                        qty=kwargs.get("qty"),
                        notional=kwargs.get("notional"),
                        side=self._get_side(kwargs.get("side")),
                        time_in_force=TimeInForce.DAY,
                        extended_hours=None,
                        client_order_id=None,
                        order_class=None,
                        take_profit=None,
                        stop_loss=None,
                        limit_price=kwargs.get("limit_price")
                   )

    def _stop_order(self, **kwargs):
        return StopLimitOrderRequest(
                        symbol=kwargs.get("symbol"),
                        qty=kwargs.get("qty"),
                        notional=kwargs.get("notional"),
                        side=self._get_side(kwargs.get("side")),
                        time_in_force=TimeInForce.DAY,
                        extended_hours=None,
                        client_order_id=None,
                        order_class=None,
                        take_profit=None,
                        stop_loss=None,
                        stop_price=kwargs.get("stop_price"),
                        limit_price=kwargs.get("limit_price")
                   )

    def _trailing_stop_order(self, **kwargs):
        return TrailingStopOrderRequest(
                        symbol=kwargs.get("symbol"),
                        qty=kwargs.get("qty"),
                        notional=kwargs.get("notional"),
                        side=self._get_side(kwargs.get("side")),
                        time_in_force=TimeInForce.DAY,
                        extended_hours=None,
                        client_order_id=None,
                        order_class=None,
                        take_profit=None,
                        stop_loss=None,
                        trail_price=kwargs.get("trail_price"),
                        trail_percent=kwargs.get("trail_percent")
                   )
    
    @staticmethod
    def _get_side(side: str):
        if side == "buy":
            return OrderSide.BUY
        elif side == "sell":
            return OrderSide.SELL
        else:
            raise ValueError(f"`side` must be 'buy' or 'sell', not {side}")