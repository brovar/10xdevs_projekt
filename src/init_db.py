import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random

from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import (Base, CategoryModel, LogModel, OfferModel, OrderItemModel,
                    OrderModel, UserModel)
from schemas import (LogEventType, OfferStatus, OrderStatus, UserRole,
                     UserStatus)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("db-init")

# Database URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/steambay",
)
# Fallback to localhost if using local development
if (
    "postgres:5432" in DATABASE_URL
    and os.environ.get("ENVIRONMENT") != "docker"
):
    DATABASE_URL = DATABASE_URL.replace("postgres:5432", "localhost:5432")

# Create the engine
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

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

        # Create categories - expanded to 20 categories as per PRD
        categories = [
            CategoryModel(name="Action"),
            CategoryModel(name="Adventure"),
            CategoryModel(name="RPG"),
            CategoryModel(name="Strategy"),
            CategoryModel(name="Simulation"),
            CategoryModel(name="Sports"),
            CategoryModel(name="Racing"),
            CategoryModel(name="Puzzle"),
            CategoryModel(name="Indie"),
            CategoryModel(name="FPS"),
            CategoryModel(name="MMO"),
            CategoryModel(name="MOBA"),
            CategoryModel(name="Survival"),
            CategoryModel(name="Horror"),
            CategoryModel(name="Platformer"),
            CategoryModel(name="Fighting"),
            CategoryModel(name="Sandbox"),
            CategoryModel(name="Visual Novel"),
            CategoryModel(name="Card Game"),
            CategoryModel(name="Educational"),
        ]

        session.add_all(categories)
        await session.flush()

        # Create main test users (6 according to PRD - 2x Buyer, 2x Seller, 2x Admin)
        admin1 = UserModel(
            id=uuid.uuid4(),
            email="admin@steambay.com",
            password_hash=pwd_context.hash("Admin123!"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            first_name="Admin",
            last_name="User",
            created_at=datetime.now(timezone.utc) - timedelta(days=60),
        )

        admin2 = UserModel(
            id=uuid.uuid4(),
            email="admin2@steambay.com",
            password_hash=pwd_context.hash("Admin123!"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            first_name="Second",
            last_name="Administrator",
            created_at=datetime.now(timezone.utc) - timedelta(days=45),
        )

        seller1 = UserModel(
            id=uuid.uuid4(),
            email="seller@steambay.com",
            password_hash=pwd_context.hash("Seller123!"),
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            first_name="Seller",
            last_name="User",
            created_at=datetime.now(timezone.utc) - timedelta(days=55),
        )

        seller2 = UserModel(
            id=uuid.uuid4(),
            email="seller2@steambay.com",
            password_hash=pwd_context.hash("Seller123!"),
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            first_name="Second",
            last_name="Seller",
            created_at=datetime.now(timezone.utc) - timedelta(days=40),
        )

        buyer1 = UserModel(
            id=uuid.uuid4(),
            email="buyer@steambay.com",
            password_hash=pwd_context.hash("Buyer123!"),
            role=UserRole.BUYER,
            status=UserStatus.ACTIVE,
            first_name="Buyer",
            last_name="User",
            created_at=datetime.now(timezone.utc) - timedelta(days=50),
        )

        buyer2 = UserModel(
            id=uuid.uuid4(),
            email="buyer2@steambay.com",
            password_hash=pwd_context.hash("Buyer123!"),
            role=UserRole.BUYER,
            status=UserStatus.ACTIVE,
            first_name="Second",
            last_name="Buyer",
            created_at=datetime.now(timezone.utc) - timedelta(days=35),
        )

        # Create additional users - 10 more: 4 buyers, 4 sellers, 2 admins
        additional_users = []
        for i in range(1, 5):
            # Additional buyers
            additional_users.append(
                UserModel(
                    id=uuid.uuid4(),
                    email=f"buyer{i+2}@example.com",
                    password_hash=pwd_context.hash("Password10!"),
                    role=UserRole.BUYER,
                    status=UserStatus.ACTIVE,
                    first_name=f"Buyer{i+2}",
                    last_name="Example",
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(10, 30)),
                )
            )
            
            # Additional sellers
            additional_users.append(
                UserModel(
                    id=uuid.uuid4(),
                    email=f"seller{i+2}@example.com",
                    password_hash=pwd_context.hash("Password10!"),
                    role=UserRole.SELLER,
                    status=UserStatus.ACTIVE,
                    first_name=f"Seller{i+2}",
                    last_name="Example",
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(10, 30)),
                )
            )
            
        # Additional admins
        for i in range(1, 3):
            additional_users.append(
                UserModel(
                    id=uuid.uuid4(),
                    email=f"admin{i+2}@example.com",
                    password_hash=pwd_context.hash("Password10!"),
                    role=UserRole.ADMIN,
                    status=UserStatus.ACTIVE,
                    first_name=f"Admin{i+2}",
                    last_name="Example",
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(10, 30)),
                )
            )

        # Add some users with different statuses
        inactive_user = UserModel(
            id=uuid.uuid4(),
            email="inactive@example.com",
            password_hash=pwd_context.hash("Password10!"),
            role=UserRole.BUYER,
            status=UserStatus.INACTIVE,
            first_name="Inactive",
            last_name="User",
            created_at=datetime.now(timezone.utc) - timedelta(days=15),
        )
        additional_users.append(inactive_user)

        # Add all users to the session
        main_users = [admin1, admin2, seller1, seller2, buyer1, buyer2]
        all_users = main_users + additional_users
        session.add_all(all_users)
        await session.flush()

        # Get all sellers for offer creation
        sellers = [user for user in all_users if user.role == UserRole.SELLER]
        
        # Get all buyers for order creation
        buyers = [user for user in all_users if user.role == UserRole.BUYER]

        # Create sample game titles and descriptions for offers
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
            "Battle Royale Ultimate",
            "Cyberpunk Dreams",
            "Ocean Explorer",
            "Sky Pirates",
            "Wizards of the Realm",
            "Dino Hunter",
            "Robot Wars",
            "Samurai Tales",
            "Dungeon Master",
            "Space Colony",
            "Western Outlaw",
            "Farm Life Simulator",
            "Dragon Quest Legacy",
            "Superhero Chronicles",
            "Car Mechanic Pro",
            "Magic Academy",
        ]

        descriptions = [
            "An action-packed adventure across the galaxy. Discover new planets, battle alien forces, and save the universe!",
            "Embark on an epic journey through a magical realm filled with dungeons, dragons, and treasures waiting to be discovered.",
            "Feel the speed and adrenaline as you race through stunning tracks around the world in this ultimate racing experience.",
            "Challenge your mind with hundreds of intricate puzzles that will test your logic and problem-solving skills.",
            "Command a team of legendary heroes on a quest to defeat ancient evils and restore peace to the land.",
            "Build and manage your medieval kingdom, handle diplomacy, warfare, and ensure your dynasty survives through the ages.",
            "Explore the vastness of space in this immersive space simulation. Trade, fight, or discover at your own pace.",
            "Track and hunt fearsome monsters in this thrilling action game. Craft weapons and armor from your victories.",
            "Design, build, and manage the city of your dreams. Handle everything from infrastructure to citizen happiness.",
            "Survive in a world overrun by zombies. Gather resources, build defenses, and fight to stay alive.",
            "Set sail on the high seas, discover treasure islands, battle rival ships, and become the most feared pirate!",
            "Master the arts of stealth and combat as you take on the role of a skilled ninja warrior in feudal Japan.",
            "Play the market, invest wisely, and build your financial empire in this realistic stock market simulation.",
            "Manage your football team to glory. Handle transfers, tactics, and lead your team to championship victories.",
            "Drop into a massive battlefield where only one player will remain standing in this intense battle royale game.",
        ]

        # Create more offers from all sellers (about 50 total)
        offers = []
        
        for seller in sellers:
            # Each seller creates multiple offers
            num_offers = random.randint(5, 10)
            for i in range(num_offers):
                # Pick a random title and description, or generate if all used
                title_index = (len(offers) % len(game_titles))
                title = game_titles[title_index]
                if i > 0:
                    title = f"{title} - {['Premium', 'Deluxe', 'Classic', 'Ultimate', 'Special'][i % 5]} Edition"
                
                desc_index = (len(offers) % len(descriptions))
                description = descriptions[desc_index]
                
                # Pick a random category
                category_id = random.randint(1, len(categories))
                
                # Create varied price
                price = Decimal(str(round(9.99 + (random.random() * 50), 2)))
                
                # Vary the status
                status_weights = [0.6, 0.2, 0.1, 0.05, 0.05]  # active, inactive, sold, moderated, archived
                status = random.choices(
                    [
                        OfferStatus.ACTIVE,
                        OfferStatus.INACTIVE,
                        OfferStatus.SOLD,
                        OfferStatus.MODERATED,
                        OfferStatus.ARCHIVED
                    ],
                    weights=status_weights
                )[0]
                
                # Quantity - sold items have 0
                quantity = 0 if status == OfferStatus.SOLD else random.randint(1, 20)
                
                # Vary creation dates
                days_ago = random.randint(1, 40)
                created_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
                
                # Sometimes have an update date
                updated_at = None
                if random.random() > 0.7:  # 30% chance of having an update
                    updated_at = created_date + timedelta(days=random.randint(1, days_ago))
                
                offers.append(
                    OfferModel(
                        id=uuid.uuid4(),
                        seller_id=seller.id,
                        category_id=category_id,
                        title=title,
                        description=description,
                        price=price,
                        quantity=quantity,
                        status=status,
                        created_at=created_date,
                        updated_at=updated_at,
                    )
                )

        session.add_all(offers)
        await session.flush()

        # Create sample orders for all buyers
        logger.info("Creating sample orders for buyers...")
        orders = []
        order_details = []
        
        # Get active offers that can be purchased
        active_offers = [offer for offer in offers if offer.status == OfferStatus.ACTIVE and offer.quantity > 0]
        
        for buyer in buyers:
            # Each buyer has multiple orders
            num_orders = random.randint(2, 5)
            
            for i in range(num_orders):
                # Different timeframes for orders to simulate history
                days_ago = random.randint(1, 30)
                created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
                
                # Different order statuses to show variety
                order_status_weights = [0.05, 0.15, 0.25, 0.35, 0.1, 0.1]  # pending_payment, processing, shipped, delivered, cancelled, failed
                status = random.choices(
                    [
                        OrderStatus.PENDING_PAYMENT,
                        OrderStatus.PROCESSING,
                        OrderStatus.SHIPPED,
                        OrderStatus.DELIVERED,
                        OrderStatus.CANCELLED,
                        OrderStatus.FAILED
                    ],
                    weights=order_status_weights
                )[0]
                
                order_id = uuid.uuid4()
                
                # Select 1-3 offers for this order
                num_offers_in_order = random.randint(1, 3)
                if len(active_offers) > num_offers_in_order:
                    order_offers = random.sample(active_offers, num_offers_in_order)
                else:
                    order_offers = active_offers[:num_offers_in_order]
                
                # Create the order
                updated_at = None
                if status != OrderStatus.PENDING_PAYMENT:
                    updated_at = created_at + timedelta(hours=random.randint(1, 24))
                
                order = OrderModel(
                    id=order_id,
                    buyer_id=buyer.id,
                    status=status,
                    created_at=created_at,
                    updated_at=updated_at,
                )
                orders.append(order)
                
                # Store details for creating order items later
                order_details.append(
                    {"order_id": order_id, "offers": order_offers}
                )

        # Add and flush orders
        session.add_all(orders)
        await session.flush()

        # Create order items based on the orders
        order_items = []
        order_totals = {}
        
        for details in order_details:
            order_id = details["order_id"]
            order_offers = details["offers"]
            total_amount = Decimal("0.00")
            
            for offer in order_offers:
                quantity = random.randint(1, 3)  # Buy 1-3 of each item
                item_price = Decimal(str(offer.price))
                total_amount += item_price * quantity
                
                # Create order item
                order_item = OrderItemModel(
                    order_id=order_id,
                    offer_id=offer.id,
                    quantity=quantity,
                    price_at_purchase=item_price,
                    offer_title=offer.title,
                )
                order_items.append(order_item)
            
            # Store the total amount for this order
            order_totals[order_id] = total_amount

        # Add order items
        session.add_all(order_items)
        await session.flush()

        # Create logs for all events
        logs = []
        
        # User registration logs
        for user in all_users:
            log = LogModel(
                event_type=LogEventType.USER_REGISTER,
                user_id=user.id,
                ip_address="127.0.0.1",
                message=f"User account created: {user.email} with role {user.role}",
                timestamp=user.created_at,
            )
            logs.append(log)
        
        # Order-related logs
        for order in orders:
            order_id = order.id
            status = order.status
            buyer_id = order.buyer_id
            buyer = next((u for u in all_users if u.id == buyer_id), None)
            total_amount = order_totals.get(order_id, Decimal("0.00"))
            
            log_message = f"Order {order_id} created with status {status} for buyer {buyer.email if buyer else 'unknown'} with total amount {total_amount}"
            log_event_type = LogEventType.ORDER_PLACE_SUCCESS
            
            if status == OrderStatus.CANCELLED:
                log_event_type = LogEventType.ORDER_CANCELLED
            elif status == OrderStatus.FAILED:
                log_event_type = LogEventType.ORDER_PLACE_FAIL
            
            log = LogModel(
                event_type=log_event_type,
                user_id=buyer_id,
                ip_address="127.0.0.1",
                message=log_message,
                timestamp=order.created_at,
            )
            logs.append(log)
            
            # Add payment logs for completed orders
            if status in [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                payment_log = LogModel(
                    event_type=LogEventType.PAYMENT_SUCCESS,
                    user_id=buyer_id,
                    ip_address="127.0.0.1",
                    message=f"Payment successful for order {order_id}, amount: {total_amount}",
                    timestamp=order.created_at + timedelta(minutes=10),  # 10 minutes after order creation
                )
                logs.append(payment_log)
            
            # Add shipment logs for shipped/delivered orders
            if status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                ship_log = LogModel(
                    event_type=LogEventType.ORDER_STATUS_CHANGE,
                    user_id=buyer_id,
                    ip_address="127.0.0.1",
                    message=f"Order {order_id} status changed to {OrderStatus.SHIPPED}",
                    timestamp=order.created_at + timedelta(days=1),  # 1 day after order
                )
                logs.append(ship_log)
            
            # Add delivery logs for delivered orders
            if status == OrderStatus.DELIVERED:
                deliver_log = LogModel(
                    event_type=LogEventType.ORDER_STATUS_CHANGE,
                    user_id=buyer_id,
                    ip_address="127.0.0.1",
                    message=f"Order {order_id} status changed to {OrderStatus.DELIVERED}",
                    timestamp=order.created_at + timedelta(days=2),  # 2 days after order
                )
                logs.append(deliver_log)
        
        # Offer creation logs
        for offer in offers:
            log = LogModel(
                event_type=LogEventType.OFFER_CREATE,
                user_id=offer.seller_id,
                ip_address="127.0.0.1",
                message=f"Offer created: {offer.title} with price {offer.price}",
                timestamp=offer.created_at,
            )
            logs.append(log)
            
            # Add offer update logs for offers with update timestamps
            if offer.updated_at:
                update_log = LogModel(
                    event_type=LogEventType.OFFER_EDIT,
                    user_id=offer.seller_id,
                    ip_address="127.0.0.1",
                    message=f"Offer updated: {offer.title}",
                    timestamp=offer.updated_at,
                )
                logs.append(update_log)
            
            # Add status change logs for non-active offers
            if offer.status != OfferStatus.ACTIVE:
                status_log = LogModel(
                    event_type=LogEventType.OFFER_STATUS_CHANGE,
                    user_id=offer.seller_id,
                    ip_address="127.0.0.1",
                    message=f"Offer status changed to {offer.status} for offer: {offer.title}",
                    timestamp=offer.updated_at or offer.created_at + timedelta(days=1),
                )
                logs.append(status_log)
        
        # Add user login logs (simulating activity)
        for _ in range(100):  # Create 100 random login events
            random_user = random.choice(all_users)
            if random_user.status == UserStatus.ACTIVE:  # Only active users can log in
                days_ago = random.randint(1, 30)
                login_time = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(0, 23))
                
                login_log = LogModel(
                    event_type=LogEventType.USER_LOGIN,
                    user_id=random_user.id,
                    ip_address=f"192.168.1.{random.randint(1, 255)}",  # Random IP for variety
                    message=f"User login: {random_user.email}",
                    timestamp=login_time,
                )
                logs.append(login_log)
        
        # Add moderation logs
        for offer in offers:
            if offer.status == OfferStatus.MODERATED:
                # Pick a random admin to moderate
                admin = random.choice([user for user in all_users if user.role == UserRole.ADMIN])
                
                mod_log = LogModel(
                    event_type=LogEventType.OFFER_MODERATED,
                    user_id=admin.id,
                    ip_address="127.0.0.1",
                    message=f"Offer moderated: {offer.title}",
                    timestamp=offer.updated_at or offer.created_at + timedelta(days=random.randint(1, 5)),
                )
                logs.append(mod_log)

        session.add_all(logs)

        # Commit all changes
        await session.commit()

        logger.info("Test data created successfully.")
        logger.info(f"Created {len(categories)} categories.")
        logger.info(f"Created {len(all_users)} users, including 6 standard test users:")
        logger.info("  - admin@steambay.com (Admin123!)")
        logger.info("  - admin2@steambay.com (Admin123!)")
        logger.info("  - seller@steambay.com (Seller123!)")
        logger.info("  - seller2@steambay.com (Seller123!)")
        logger.info("  - buyer@steambay.com (Buyer123!)")
        logger.info("  - buyer2@steambay.com (Buyer123!)")
        logger.info(f"Created {len(offers)} offers from {len(sellers)} sellers.")
        logger.info(f"Created {len(orders)} orders for {len(buyers)} buyers.")
        logger.info(f"Created {len(logs)} log entries.")


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
