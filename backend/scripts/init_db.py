#!/usr/bin/env python
"""
Database initialization script.
Creates all tables in the database.
"""

import asyncio
from app.core.database import init_db

async def main():
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())