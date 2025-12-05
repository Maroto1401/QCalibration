# SQLAlchemy model placeholder for Job
from sqlalchemy import Column, Integer, String, JSON
from .user import Base

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    status = Column(String, default='pending')
    metadata = Column(JSON)
