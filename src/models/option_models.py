from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class OptionData(BaseModel):
    openInterest: int
    changeinOpenInterest: int
    pchangeinOpenInterest: float
    totalTradedVolume: int
    impliedVolatility: float
    lastPrice: float
    change: float
    pChange: float
    totalBuyQuantity: int
    totalSellQuantity: int
    bidQty: int
    bidprice: float
    askQty: int
    askPrice: float

class OptionStrike(BaseModel):
    strikePrice: float
    expiryDate: str
    CE: Optional[OptionData] = None
    PE: Optional[OptionData] = None

class OptionChainRecords(BaseModel):
    expiryDates: List[str]
    data: List[OptionStrike]
    strikePrices: List[float]
    underlyingValue: float

class OptionChainResponse(BaseModel):
    records: OptionChainRecords
    filtered: dict

class OptionChainRequest(BaseModel):
    symbol: str = "RELIANCE"

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    timestamp: datetime = datetime.now()

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    service: str
    version: str

class Strike(BaseModel):
    strikePrice: float
    expiryDate: str
    underlying: str
    identifier: str
    openInterest: int
    changeinOpenInterest: int
    pchangeinOpenInterest: float
    totalTradedVolume: int
    impliedVolatility: float
    lastPrice: float
    change: float
    pChange: float
    totalBuyQuantity: int
    totalSellQuantity: int
    bidQty: int
    bidprice: float
    askQty: int
    askPrice: float
    underlyingValue: float
    type: str  # "PE" or "CE"
    # Greeks
    delta: Optional[float] = None
    theta: Optional[float] = None
    gamma: Optional[float] = None
    vega: Optional[float] = None
    # Lot size
    lotSize: Optional[int] = None
    # Analytics fields
    strikeGap: Optional[float] = None
    strikeGapPercentage: Optional[float] = None
    premiumPercentage: Optional[float] = None

class VolatileOptionsResponse(BaseModel):
    success: bool
    message: str
    data: List[Strike]
    timestamp: datetime = datetime.now()

class FnoStock(BaseModel):
    symbol: str
    companyName: str
    lotSize: int

class FnoStocksResponse(BaseModel):
    success: bool
    message: str
    data: List[FnoStock]
    total: int
    timestamp: datetime = datetime.now()
