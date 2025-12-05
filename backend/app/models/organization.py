# SQLAlchemy model placeholder for Organization
from sqlalchemy import Column, Integer, String
from .user import Base

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
