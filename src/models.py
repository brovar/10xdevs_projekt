from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, Text, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Index

import uuid
from typing import Optional
from datetime import datetime

from schemas import UserRole, UserStatus, LogEventType, OfferStatus, OrderStatus, TransactionStatus

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

class LogModel(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(SQLEnum(LogEventType), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class CategoryModel(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

class OfferModel(Base):
    __tablename__ = "offers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(precision=10, scale=2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    image_filename = Column(String(255), nullable=True)
    status = Column(SQLEnum(OfferStatus), nullable=False, default=OfferStatus.INACTIVE, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Indeksy złożone dla szybszego wyszukiwania
    __table_args__ = (
        Index('ix_offers_seller_status', 'seller_id', 'status'),
        Index('ix_offers_status_quantity', 'status', 'quantity'),
    )

class OrderModel(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING_PAYMENT, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Indeks dla szybszego filtrowania po statusie i dacie
    __table_args__ = (
        Index('ix_orders_buyer_id_status', 'buyer_id', 'status'),
        Index('ix_orders_created_at', 'created_at'),
    )

class OrderItemModel(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Numeric(precision=10, scale=2), nullable=False)
    offer_title = Column(String(255), nullable=False)
    
    # Indeks dla szybszego wyszukiwania
    __table_args__ = (
        Index('ix_order_items_order_id', 'order_id'),
    )

class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    status = Column(SQLEnum(TransactionStatus), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) 