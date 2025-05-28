# backend/app/utils/csv_loader.py
import csv
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.token import Token

async def load_tokens_from_csv(csv_file_path: str = "data/tokens.csv"):
    """Load tokens from CSV file into database"""
    csv_path = Path(csv_file_path)
    if not csv_path.exists():
        print(f"CSV file not found: {csv_file_path}")
        return
    
    async with AsyncSessionLocal() as db:
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Check if token already exists
                    result = await db.execute(
                        select(Token).where(Token.symbol == row['symbol'])
                    )
                    existing_token = result.scalar_one_or_none()
                    
                    if not existing_token:
                        # Create new token
                        token = Token(
                            symbol=row['symbol'],
                            token_id=int(row['token_id']),
                            exchange=row['exchange'],
                            instrument_type=row.get('instrument_type', 'EQ'),
                            lot_size=int(row.get('lot_size', 1)),
                            tick_size=float(row.get('tick_size', 0.05)),
                            is_active=True,
                            is_tradeable=True
                        )
                        db.add(token)
                        print(f"Added token: {row['symbol']}")
                    else:
                        # Update existing token
                        existing_token.token_id = int(row['token_id'])
                        existing_token.exchange = row['exchange']
                        existing_token.instrument_type = row.get('instrument_type', 'EQ')
                        existing_token.lot_size = int(row.get('lot_size', 1))
                        existing_token.tick_size = float(row.get('tick_size', 0.05))
                        print(f"Updated token: {row['symbol']}")
                
                await db.commit()
                print("Successfully loaded tokens from CSV")
                
        except Exception as e:
            print(f"Error loading tokens from CSV: {e}")
            await db.rollback()