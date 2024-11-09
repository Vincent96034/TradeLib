from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass, field

from .enums import OptionType


@dataclass
class Asset:
    symbol: str
    name: Optional[str] = None
    id: Optional[str] = None
    asset_type: str = "Equity"
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        self.symbol = self.symbol.upper()


@dataclass(kw_only=True)
class Equity(Asset):
    def __post_init__(self):
        super().__post_init__()
        self.asset_type = "Equity"


@dataclass(kw_only=True)
class Derivative(Asset):
    underlying: Asset

    def __post_init__(self):
        super().__post_init__()
        self.asset_type = "Derivative"


@dataclass(kw_only=True)
class Option(Derivative):
    option_type: OptionType
    strike_price: float
    expiry_date: datetime

    def __post_init__(self):
        super().__post_init__()
        self.asset_type = "Option"


@dataclass(kw_only=True)
class Crypto(Asset):
    def __post_init__(self):
        super().__post_init__()
        self.asset_type = "Crypto"
