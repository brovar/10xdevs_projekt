from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from logging import Logger
from typing import Optional, Tuple, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import func

from models import LogModel
from schemas import LogEventType, LogDTO

class LogService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def create_log(
        self,
        event_type: LogEventType,
        message: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> LogModel:
        """
        Create a new log entry in the database
        
        Args:
            event_type: Type of event from LogEventType enum
            message: Log message
            user_id: Optional UUID of the user
            ip_address: Optional IP address
            
        Returns:
            Created Log record
        """
        log = LogModel(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            message=message,
            timestamp=datetime.utcnow()
        )
        self.db_session.add(log)
        
        # Don't commit here, let the caller handle transaction
        return log 

    async def get_logs(
        self,
        page: int = 1,
        limit: int = 100,
        event_type: Optional[LogEventType] = None,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[LogDTO], int, int]:
        """
        Retrieve a paginated list of logs with optional filters.
        """
        # Validate pagination parameters
        if page < 1:
            raise ValueError("Page must be a positive integer")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        if start_date and end_date and end_date < start_date:
            raise ValueError("End date must be after start date")

        # Build base queries
        count_query = select(func.count()).select_from(LogModel)
        data_query = select(LogModel)
        filters = []
        if event_type:
            filters.append(LogModel.event_type == event_type)
        if user_id:
            filters.append(LogModel.user_id == user_id)
        if ip_address:
            filters.append(LogModel.ip_address == ip_address)
        if start_date:
            filters.append(LogModel.timestamp >= start_date)
        if end_date:
            filters.append(LogModel.timestamp <= end_date)
        if filters:
            for cond in filters:
                count_query = count_query.where(cond)
                data_query = data_query.where(cond)

        # Get total count
        total = (await self.db_session.execute(count_query)).scalar() or 0
        pages = (total + limit - 1) // limit if total > 0 else 1

        # Apply ordering and pagination
        offset = (page - 1) * limit
        data_query = (
            data_query.order_by(LogModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db_session.execute(data_query)
        logs = result.scalars().all()

        # Map to DTO
        items = [
            LogDTO(
                id=ln.id,
                event_type=ln.event_type,
                user_id=ln.user_id,
                ip_address=ln.ip_address,
                message=ln.message,
                timestamp=ln.timestamp
            )
            for ln in logs
        ]
        return items, total, pages 