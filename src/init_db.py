import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import text
import logging
from passlib.context import CryptContext

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import Base, UserModel, CategoryModel, OfferModel, LogModel, OrderModel, OrderItemModel
from schemas import UserRole, UserStatus, OfferStatus, LogEventType, OrderStatus

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
            "Legendary Heroes",
            "Medieval Kingdom Simulator",
            "Cosmic Odyssey",
            "Monster Hunter Extreme",
            "City Builder Pro",
            "Zombie Apocalypse",
            "Pirate Adventure",
            "Ninja Warrior",
            "Stock Market Tycoon",
            "Football Manager 2023",
            "Battle Royale Ultimate"
        ]
        
        status_variations = [
            OfferStatus.ACTIVE,
            OfferStatus.ACTIVE,
            OfferStatus.ACTIVE,
            OfferStatus.INACTIVE,
            OfferStatus.INACTIVE,
            OfferStatus.ACTIVE,
            OfferStatus.ACTIVE,
            OfferStatus.ACTIVE,
            OfferStatus.INACTIVE,
            OfferStatus.ACTIVE,
            OfferStatus.SOLD,
            OfferStatus.ACTIVE,
            OfferStatus.MODERATED,
            OfferStatus.ACTIVE,
            OfferStatus.ARCHIVED,
        ]
        
        offers = []
        for i, title in enumerate(game_titles):
            category_id = (i % len(categories)) + 1
            # Create a varied price range
            price = Decimal(str(round(19.99 + (i * 3.5), 2)))
            # Vary the quantity - sold items have 0
            quantity = 0 if status_variations[i] == OfferStatus.SOLD else (i % 10) + 1
            # Vary creation dates for realistic history
            created_date = datetime.now(timezone.utc) - timedelta(days=i*3)
            
            offers.append(
                OfferModel(
                    id=uuid.uuid4(),
                    seller_id=seller.id,
                    category_id=category_id,
                    title=title,
                    description=f"This is a sample description for {title}. Experience the ultimate digital gaming adventure with hours of engaging content. Perfect for gamers of all levels and interests!",
                    price=price,
                    quantity=quantity,
                    status=status_variations[i],
                    created_at=created_date,
                    updated_at=created_date + timedelta(days=1) if i % 3 == 0 else None
                )
            )
        
        session.add_all(offers)
        await session.flush()
        
        # Create sample orders for the buyer
        logger.info("Creating sample orders for the buyer...")
        
        # Different timeframes for orders to simulate history
        now = datetime.now(timezone.utc)
        time_frames = [
            now - timedelta(days=30),  # 1 month ago
            now - timedelta(days=21),  # 3 weeks ago
            now - timedelta(days=14),  # 2 weeks ago
            now - timedelta(days=7),   # 1 week ago
            now - timedelta(days=2),   # 2 days ago
            now - timedelta(hours=6),  # 6 hours ago
        ]
        
        # Different order statuses to show variety
        order_statuses = [
            OrderStatus.DELIVERED,   # Completed order from a month ago
            OrderStatus.SHIPPED,     # Order in transit from 3 weeks ago
            OrderStatus.PROCESSING,  # Recently processed order from 2 weeks ago
            OrderStatus.CANCELLED,   # Cancelled order from 1 week ago
            OrderStatus.FAILED,      # Failed payment from 2 days ago
            OrderStatus.PENDING_PAYMENT,  # Recent order awaiting payment
        ]
        
        # Create orders first
        orders = []
        order_totals = {}
        order_details = []
        
        # Generate order IDs and create orders first
        for i, (created_at, status) in enumerate(zip(time_frames, order_statuses)):
            order_id = uuid.uuid4()
            
            # Select offers for this order (will calculate total amount later)
            order_offers = offers[i % len(offers):(i % len(offers)) + 2]
            
            # Create the order
            order = OrderModel(
                id=order_id,
                buyer_id=buyer.id,
                status=status,
                created_at=created_at,
                updated_at=created_at + timedelta(hours=2) if status != OrderStatus.PENDING_PAYMENT else None
            )
            orders.append(order)
            
            # Store details for creating order items later
            order_details.append({
                "order_id": order_id,
                "offers": order_offers
            })
        
        # Add and flush orders first
        session.add_all(orders)
        await session.flush()
        
        # Now create order items based on the orders
        order_items = []
        for details in order_details:
            order_id = details["order_id"]
            order_offers = details["offers"]
            total_amount = Decimal('0.00')
            
            for j, offer in enumerate(order_offers):
                quantity = j + 1  # 1 or 2 items depending on position
                item_price = Decimal(str(offer.price))
                total_amount += item_price * quantity
                
                # Create order item
                order_item = OrderItemModel(
                    order_id=order_id,
                    offer_id=offer.id,
                    quantity=quantity,
                    price_at_purchase=item_price,
                    offer_title=offer.title
                )
                order_items.append(order_item)
            
            # Store the total amount for this order
            order_totals[order_id] = total_amount
        
        # Add order items now that orders are created
        session.add_all(order_items)
        await session.flush()
        
        # Create logs
        logs = []
        
        # Order-related logs
        for i, order in enumerate(orders):
            order_id = order.id
            status = order.status
            total_amount = order_totals[order_id]
            
            log_message = f"Order {order_id} created with status {status} for buyer {buyer.email} with total amount {total_amount}"
            log_event_type = LogEventType.ORDER_PLACE_SUCCESS
            
            if status == OrderStatus.CANCELLED:
                log_event_type = LogEventType.ORDER_CANCELLED
            elif status == OrderStatus.FAILED:
                log_event_type = LogEventType.ORDER_PLACE_FAIL
            
            log = LogModel(
                event_type=log_event_type,
                user_id=buyer.id,
                ip_address="127.0.0.1",
                message=log_message,
                timestamp=time_frames[i]  # Use the same timestamp as the order
            )
            logs.append(log)
        
        # User creation logs
        logs.extend([
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
        ])
        
        session.add_all(logs)
        
        # Commit all changes
        await session.commit()
        
        logger.info("Test data created successfully.")
        logger.info(f"Created {len(offers)} sample offers.")
        logger.info(f"Created {len(categories)} categories.")
        logger.info(f"Created {len(orders)} sample orders for buyer@steambay.com.")
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