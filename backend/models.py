from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class OTP(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    otp = Column(String)
    expires_at = Column(DateTime)