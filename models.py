from sqlalchemy import Column, Integer, String, DateTime, Float
from database import Base
import datetime

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, default=datetime.datetime.utcnow)  # optional

class OptionChainData(Base):
    __tablename__ = "option_chain"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    strike_price = Column(Float)
    call_oi = Column(Integer)
    put_oi = Column(Integer)
    # add more columns as needed like call_bid_qty, put_bid_qty, last_price etc
