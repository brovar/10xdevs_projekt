import asyncio
import os
import sys
from datetime import datetime, timezone
import uuid

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import text
import logging
from passlib.context import CryptContext

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import Base, UserModel, CategoryModel, OfferModel, LogModel
from schemas import UserRole, UserStatus, OfferStatus, LogEventType

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("db-init")

# Database URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@postgres:5432/steambay"
)
# Fallback to localhost if using local development
if "postgres:5432" in DATABASE_URL and os.environ.get("ENVIRONMENT") != "docker":
    DATABASE_URL = DATABASE_URL.replace("postgres:5432", "localhost:5432")

# Create the engine
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        # Drop tables if they exist (clean start)
        if os.environ.get("RESET_DB") == "true":
            logger.info("Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
        
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables created successfully.")

async def check_database():
    """Check if the database exists and is accessible."""
    try:
        logger.info(f"Checking database connection: {DATABASE_URL}")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info(f"Database connection successful: {result.scalar()}")
        return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False

async def create_test_data():
    """Create test data for development."""
    logger.info("Creating test data...")
    
    async with async_session_maker() as session:
        # Check if data already exists (simple check for users)
        result = await session.execute(select(UserModel))
        if result.scalars().first():
            logger.info("Data already exists. Skipping test data creation.")
            return

        # Create test users
        admin = UserModel(
            id=uuid.uuid4(),
            email="admin@steambay.com",
            password_hash=pwd_context.hash("Admin123!"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            first_name="Admin",
            last_name="User",
            created_at=datetime.now(timezone.utc)
        )
        
        seller = UserModel(
            id=uuid.uuid4(),
            email="seller@steambay.com",
            password_hash=pwd_context.hash("Seller123!"),
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            first_name="Seller",
            last_name="User",
            created_at=datetime.now(timezone.utc)
        )
        
        buyer = UserModel(
            id=uuid.uuid4(),
            email="buyer@steambay.com",
            password_hash=pwd_context.hash("Buyer123!"),
            role=UserRole.BUYER,
            status=UserStatus.ACTIVE,
            first_name="Buyer",
            last_name="User",
            created_at=datetime.now(timezone.utc)
        )
        
        session.add_all([admin, seller, buyer])
        await session.flush()
        
        # Create categories
        categories = [
            CategoryModel(name="Action"),
            CategoryModel(name="Adventure"),
            CategoryModel(name="RPG"),
            CategoryModel(name="Strategy"),
            CategoryModel(name="Simulation"),
            CategoryModel(name="Sports"),
            CategoryModel(name="Racing"),
            CategoryModel(name="Puzzle"),
            CategoryModel(name="Indie")
        ]
        
        session.add_all(categories)
        await session.flush()
        
        # Create sample offers from the seller
        game_titles = [
            "Space Explorer 2", 
            "Fantasy Quest III", 
            "Racing Championship", 
            "Puzzle Master", 
            "Legendary Heroes"
        ]
        
        offers = []
        for i, title in enumerate(game_titles):
            category_id = (i % len(categories)) + 1
            offers.append(
                OfferModel(
                    id=uuid.uuid4(),
                    seller_id=seller.id,
                    category_id=category_id,
                    title=title,
                    description=f"This is a sample description for {title}. Experience the ultimate digital gaming adventure!",
                    price=29.99 + (i * 5),
                    quantity=10,
                    status=OfferStatus.ACTIVE,
                    created_at=datetime.now(timezone.utc)
                )
            )
        
        session.add_all(offers)
        
        # Create some logs for demonstration
        logs = [
            LogModel(
                event_type=LogEventType.USER_REGISTER,
                user_id=admin.id,
                ip_address="127.0.0.1",
                message="Admin account created",
                timestamp=datetime.now(timezone.utc)
            ),
            LogModel(
                event_type=LogEventType.USER_REGISTER,
                user_id=seller.id,
                ip_address="127.0.0.1",
                message="Seller account created",
                timestamp=datetime.now(timezone.utc)
            ),
            LogModel(
                event_type=LogEventType.USER_REGISTER,
                user_id=buyer.id,
                ip_address="127.0.0.1",
                message="Buyer account created",
                timestamp=datetime.now(timezone.utc)
            ),
        ]
        
        session.add_all(logs)
        
        # Commit all changes
        await session.commit()
        
        logger.info("Test data created successfully.")
        logger.info(f"Created {len(offers)} sample offers.")
        logger.info(f"Created {len(categories)} categories.")
        logger.info(f"Created test users: admin@steambay.com, seller@steambay.com, buyer@steambay.com (Password for all: matching role + 123!)")

async def main():
    """Main function to initialize the database."""
    # Check database connection
    if not await check_database():
        logger.error("Database connection failed. Exiting.")
        return
    
    # Create tables
    await create_tables()
    
    # Create test data if in development mode
    if os.environ.get("ENVIRONMENT", "development") != "production":
        await create_test_data()
    
    logger.info("Database initialization complete.")

if __name__ == "__main__":
    asyncio.run(main()) 