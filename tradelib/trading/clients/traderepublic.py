from typing import List, Dict, Any, Optional

from pytr.account import login
from tradelib.trading.clients.base import TradeBackend
from tradelib.model import (
    Position,
    Asset,
    Order,
    Deposit,
    Trade,
    Interest,
    Dividend,
    Equity,
    Fund,
    QuantityMode,
    OrderStatus,
    OrderType,
    OrderSide,
)
from tradelib.model.order import CashFlow
from tradelib.utils import find_in_env, setup_logger

logger = setup_logger(__name__)


LEGAL_TYPE_MAP = {"STOCK": Equity, "FUND": Fund}

EVENT_TYPE_MAP = {
    "ORDER_EXECUTED": Trade,
    "TRADE_INVOICE": Trade,
    "REFERRAL_FIRST_TRADE_EXECUTED_INVITEE": Deposit,
    "CREDIT": Dividend,
    "PAYMENT_INBOUND": Deposit,
    "PAYMENT_INBOUND_APPLE_PAY": Deposit,
    "PAYMENT_INBOUND_CREDIT_CARD": Deposit,
    "PAYMENT_INBOUND_SEPA_DIRECT_DEBIT": Deposit,
    "PAYMENT_OUTBOUND": Deposit,
    "INTEREST_PAYOUT": Interest,
    "INTEREST_PAYOUT_CREATED": Interest,
    "SAVINGS_PLAN_EXECUTED": Trade,
    "SAVINGS_PLAN_INVOICE_CREATED": Trade,
    "INCOMING_TRANSFER_DELEGATION": Deposit,
    "ssp_corporate_action_invoice_cash": Dividend,
}

ORDER_STATUS_MAP = {
    "EXECUTED": OrderStatus.FILLED,
    "REJECTED": OrderStatus.REJECTED,
    "CANCELED": OrderStatus.CANCELED,
    "PENDING": OrderStatus.PENDING,
}

ORDER_TYPE_MAP = {
    "Verkauf": OrderType.MARKET,
    "Limit Kauf": OrderType.LIMIT,
    "Limit Verkauf": OrderType.LIMIT,
    "NOT_FOUND": OrderType.MARKET,  # defaults
    "MARKET": OrderType.MARKET,  # defaults
}

KNOWN_DETAIL_SECTIONS = [
    "Übersicht",
    "Performance",
    "Transaktion",
    "Dokumente",
    "",
]

ORDER_SIDE_MAP = {
    "Kauf": OrderSide.BUY,
    "Verkauf": OrderSide.SELL,
    "Limit Kauf": OrderSide.BUY,
    "Limit Verkauf": OrderSide.SELL,
}


class TradeRepublic(TradeBackend):
    """Base class for trading backends. Includes all necessary methods."""

    def __init__(
        self, phone_no: Optional[str] = None, pin: Optional[str] = None, **kwargs
    ):
        """Initialize TradeRepublic client."""
        if not phone_no:
            phone_no = find_in_env("tr_phone_no")
        if not pin:
            pin = find_in_env("tr_pin")
        self.trading_client = login(phone_no=phone_no, pin=pin, web=True)

    def get_account(self, **kwargs) -> Dict[str, Any]:
        """Get account information."""
        raise NotImplementedError("`get_account` is not implemented.")

    async def get_cash(self, **kwargs) -> float:
        """Get cash balance of trading account."""
        response = await self._send_and_receive(self.trading_client.cash)
        logger.debug(f"response: {response}")
        return float(response[0]["amount"])

    async def get_positions(self, **kwargs) -> List[Position]:
        """Get all positions of trading account."""
        response = await self._send_and_receive(self.trading_client.compact_portfolio)
        logger.debug(f"response: {response}")
        positions = []
        for pos in response["positions"]:
            logger.debug(f"position: {pos}")
            asset = await self.get_asset(isin=pos["instrumentId"])
            positions.append(
                Position(
                    asset=asset,
                    quantity=pos["netSize"],
                    average_price=float(pos["averageBuyIn"]),
                    metadata=pos,
                )
            )
        return positions

    def get_orders(self, **kwargs) -> List[Order]:
        """Get all trades of trading account."""
        raise NotImplementedError("`get_orders` is not implemented.")

    async def get_asset(self, isin: str) -> Asset:
        response = await self._send_and_receive(
            self.trading_client.instrument_details, isin=isin
        )
        return self._create_asset(response)

    async def get_trades(self, **kwargs) -> List[Trade]:
        """Get all trades of trading account."""
        trades = []
        timeline = await self._get_timeline()
        for event_raw in timeline.values():
            if event_raw is None:
                logger.warning("Found empty event. Skipping.")
                continue
            event = self._parse_event(event_raw)
            logger.debug(f"Processing event: {event}")
            TradeCls = event["eventType"]
            logger.debug(f"Trade: {Trade.__name__}")
            if self._is_cashflow(event["eventType"]):
                trades.append(
                    TradeCls(
                        amount=event["amount"],
                        timestamp=event["timestamp"],
                        id=event["id"],
                        metadata=event,
                    )
                )
            else:
                detail_raw = await self._send_and_receive(
                    self.trading_client.timeline_detail_v2, timeline_id=event["id"]
                )
                logger.debug(f"detail raw: {detail_raw}")
                detail = self._parse_detail(detail_raw)
                logger.debug(f"isin: {detail["isin"]}")
                asset = await self.get_asset(detail["isin"])
                order = Order(
                    asset=asset,
                    quantity=detail["shares"],
                    order_side=detail["order_side"],
                    quantity_mode=QuantityMode.SHARES,
                    id=event["id"],
                    status=event["status"],
                    order_type=detail["order_type"],
                    stop_price=detail["price"]
                    if detail["order_type"] in [OrderType.STOP, OrderType.STOP_LIMIT]
                    else None,
                    limit_price=detail["price"]
                    if detail["order_type"] in [OrderType.LIMIT, OrderType.STOP_LIMIT]
                    else None,
                    trailing_price=None,
                    trailing_percent=None,
                    timestamp=event["timestamp"],
                    metadata=event,
                )
                trades.append(
                    TradeCls(
                        order=order,
                        execution_price=detail["price"],
                        execution_quantity=detail["shares"],
                        quantity_mode=QuantityMode.SHARES,
                        id=event["id"],
                        timestamp=event["timestamp"],
                        fees=detail["fees"] + detail["tax"],
                        metadata={
                            "notional": abs(event["amount"]),
                            "shares": detail["shares"],
                            "total": detail["total"],
                        },
                    )
                )
        return trades

    def place_order(self, order: Order | Dict[str, Any], **kwargs) -> Order:
        """Place an order."""
        raise NotImplementedError("`place_order` is not implemented.")

    def cancel_order(self, order_id: str, **kwargs) -> Order:
        """Cancel an order."""
        raise NotImplementedError("`cancel_order` is not implemented.")

    def place_bulk_orders(self, orders: List[Order | Dict[str, Any]]) -> List[Order]:
        """Place multiple orders."""
        raise NotImplementedError("`place_multi_order` is not implemented.")

    def cancel_bulk_orders(self, order_ids: List[str]) -> List[Order]:
        """Cancel multiple orders."""
        raise NotImplementedError("`cancel_multi_order` is not implemented.")

    def get_order_status(self, order_id: str, **kwargs) -> Order:
        """Get status of an order."""
        raise NotImplementedError("`get_order_status` is not implemented.")

    def get_tradeable_assets(self, **kwargs) -> List[Asset]:
        """Get all tradeable assets."""
        raise NotImplementedError("`tradeable_assets` is not implemented.")

    def _create_asset(self, response: dict) -> Asset:
        return Asset(
            symbol=response.get("homeSymbol", response.get("isin", None)),
            name=response.get("name", None),
            id=response.get("isin", None),
            asset_type=LEGAL_TYPE_MAP.get(response.get("legalTypeId", "STOCK")),
            metadata=response,
        )

    async def _send_and_receive(self, func, **kwargs) -> Any:
        """Send a request and receive a response."""
        logger.debug(f"sending request: {func.__name__}")
        await func(**kwargs)
        sub_id, _, response = await self.trading_client.recv()
        logger.debug(f"received response for id={sub_id}: {response}")
        await self.trading_client.unsubscribe(sub_id)
        logger.debug(f"unsubscribed from id={sub_id}")
        return response

    async def _custom_timeline_transactions(self, after=None, before=None):
        return await self.trading_client.subscribe(
            {"type": "timelineTransactions", "after": after, "before": before}
        )

    async def _get_timeline(self):
        timeline = {}
        # get first batch (no `after` cursor)
        await self.trading_client.timeline_transactions()
        sub_id, _, response = await self.trading_client.recv()
        after = response["cursors"].get("after", None)

        for event in response["items"]:
            event["source"] = "timelineTransaction"
            timeline[event["id"]] = event

        while after:
            await self.trading_client.timeline_transactions(after=after)
            sub_id, _, response = await self.trading_client.recv()
            after = response["cursors"].get("after", None)

            for event in response["items"]:
                event["source"] = "timelineTransaction"
                timeline[event["id"]] = event

        await self.trading_client.unsubscribe(sub_id)
        return timeline

    @staticmethod
    def _is_cashflow(event_type: object) -> bool:
        """Check if the event type is a CashFlow."""
        return issubclass(event_type, CashFlow)

    @staticmethod
    def _tr_to_float(s: Any) -> float:
        if isinstance(s, (float, int, bool)):
            return float(s)
        if not s:
            return None
        # Remove any non-numeric characters except for ','
        cleaned_str = "".join(c for c in s if c.isdigit() or c in {","})
        # Replace ',' with '.' to handle decimal points correctly
        cleaned_str = cleaned_str.replace(",", ".")
        try:
            return float(cleaned_str)
        except Exception as e:
            logger.warning(
                f"[{e}] Could not convert string `{s}` to float. Returning `0.0`"
            )
            return 0.0

    def _parse_event(self, event_raw: dict) -> dict:
        logger.debug(f"event_raw: {event_raw}")
        if event_raw.get("action", {}) is None:
            event_raw["action"] = {}
        event = {
            "id": event_raw["id"],
            "timestamp": event_raw["timestamp"],
            "title": event_raw["title"],
            "badge": event_raw["badge"],
            "subtitle": event_raw["subtitle"],
            "amount": float(event_raw["amount"]["value"]),
            "subAmount": event_raw["subAmount"],
            "status": ORDER_STATUS_MAP.get(event_raw["status"], OrderStatus.PENDING),
            "timelineDetail": event_raw.get("action", {}).get("payload", None),
            "eventType": EVENT_TYPE_MAP.get(event_raw["eventType"], None),
            "source": event_raw["source"],
        }
        if event["eventType"] is None:
            logger.warning(
                f"Could not find matching event type for {event['eventType']}. Using "
                f"`Trade` instead. Consider opening an issue:\n event: {event}."
            )
            event["eventType"] = Trade
        return event

    def _parse_detail_sections(self, sections: list):
        """Creates a dict with each section where the key is the "title" key in each
        section and value is the "data" key in each section.
        """
        parsed = {section["title"]: section for section in sections}
        if sections[0]["title"] not in KNOWN_DETAIL_SECTIONS:
            parsed["Message"] = parsed.pop(sections[0]["title"])

        if "Transaktion" in parsed:
            data = parsed["Transaktion"]["data"]
            if isinstance(data, list):
                try:
                    parsed["Transaktion"] = {
                        item["title"]: item["detail"]["text"] for item in data
                    }
                except Exception as e:
                    print(f"Error parsing Transaktion section: {e}.")
                    parsed["Transaktion"] = data

        if "Übersicht" in parsed:
            data = parsed["Übersicht"]["data"]
            if isinstance(data, list):
                try:
                    parsed["Übersicht"] = {
                        item["title"]: item["detail"] for item in data
                    }
                except Exception as e:
                    print(f"Error parsing Übersicht section: {e}.")
                    parsed["Übersicht"] = data

        if "Performance" in parsed:
            data = parsed["Performance"]["data"]
            if isinstance(data, list):
                try:
                    parsed["Performance"] = {
                        item["title"]: item["detail"]["text"] for item in data
                    }
                except Exception as e:
                    print(f"Error parsing Performance section: {e}.")
                    parsed["Performance"] = data

        if "Message" in parsed:
            data = parsed["Message"]["data"]
            try:
                isin = parsed["Message"]["action"]["payload"]
            except Exception as e:
                print(f"Error parsing ISIN: {e}.")
                isin = None
            data["instrumentDetail"] = isin
            parsed["Message"] = data

        return parsed

    def _parse_detail(self, detail: dict) -> dict:
        logger.debug(f"found {len(detail.get("sections", []))} sections")
        sections = self._parse_detail_sections(detail.get("sections", []))

        isin = sections.get("Message", {}).get("instrumentDetail", None)

        _order_type = (
            sections.get("Übersicht", {}).get("Orderart", {}).get("text", "NOT_FOUND")
        )
        order_type = ORDER_TYPE_MAP.get(_order_type, None)
        if not order_type:
            logger.warning(
                f"Could not find matching order type for {isin}: {order_type}. Using "
                f"`MARKET` instead. Consider opening an issue:\n isin: {isin}, "
                f"order_type: {order_type}, response: {detail}"
            )
            order_type = OrderType.MARKET

        order_side = ORDER_SIDE_MAP.get(_order_type, None)
        if not order_side:
            if "verkauf" in _order_type.lower():
                order_side = OrderSide.SELL
            elif "kauf" in _order_type.lower():
                order_side = OrderSide.BUY
            else:
                order_side = OrderSide.BUY
            logger.warning(
                f"Could not find matching order side for {isin}: {order_side}. Trying to "
                f"guess from order type: {_order_type} or defauling to `BUY`. Consider "
                f"opening an issue:\n isin: {isin}, order_side: {order_side}, "
            )

        shares = sections.get("Transaktion", {}).get("Anteile", None)
        transactions = sections.get("Transaktion")
        # For savings plans, there is no `Aktienkurs`, but `Anteilspreis`
        price = transactions.get("Aktienkurs", transactions.get("Anteilspreis", None))
        fees = sections.get("Transaktion", {}).get("Gebühr", None)
        tax = sections.get("Transaktion", {}).get("Steuern", None)
        total = sections.get("Transaktion", {}).get("Gesamt", None)
        if not fees:
            fees = 0.0
            logger.debug(f"Could not find fees for {isin} ({order_type}).")
        if not tax:
            tax = 0.0
            logger.debug(f"Could not find tax for {isin} ({order_type}).")
        if not price:
            raise ValueError(
                f"Could not find price data for {isin}. 'Tranksaktion': "
                f"{sections.get("Transaktion")}."
            )

        detail = {
            "isin": isin,
            "order_type": order_type,
            "order_side": order_side,
            "price": self._tr_to_float(price),
            "shares": self._tr_to_float(shares),
            "fees": self._tr_to_float(fees),
            "tax": self._tr_to_float(tax),
            "total": self._tr_to_float(total),
        }
        return detail
