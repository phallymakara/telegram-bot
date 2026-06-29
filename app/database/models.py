from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Employee(Base):
    __tablename__ = "employees"

    name = Column(String, primary_key=True)
    daily_rate = Column(Float, nullable=False)
    gender = Column(String, nullable=True)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)
    header = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)


class AttendanceRecord(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    employee_name = Column(String, nullable=False)
    multiplier = Column(Float, nullable=False)
    hours = Column(Float, nullable=False)
    daily_rate = Column(Float, nullable=False)
    salary = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    gender = Column(String, nullable=True)