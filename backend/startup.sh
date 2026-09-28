#!/bin/bash
# Start the database initialization in the background
echo "Initializing database tables..."
python -c "
import asyncio
from sqlalchemy import text
from app.models import user, conversation, knowledge, document
from app.core.database import engine, Base

async def init_db():
    print('Connecting to database and creating tables...')
    async with engine.begin() as conn:
        # 启用 pgvector 扩展
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        await conn.run_sync(Base.metadata.create_all)
    print('Database tables created successfully!')

asyncio.run(init_db())
"

echo "Starting the application..."
# Start the main application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4