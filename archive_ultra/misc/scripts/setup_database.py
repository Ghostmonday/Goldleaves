#!/usr/bin/env python3
"""
Database setup script for Gold Leaves project.
This script helps set up and verify the database connection.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from core.config import settings, validate_config
from core.database import engine
from sqlalchemy import text

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connection successful!")
            print(f"PostgreSQL version: {version}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_tables():
    """Check if tables exist"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"📋 Existing tables: {', '.join(tables)}")
            else:
                print("📋 No tables found in database")
            
            if 'users' in tables:
                print("✅ Users table exists!")
                
                # Check table structure
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position
                """))
                
                print("🏗️  Users table structure:")
                for column_name, data_type, is_nullable in result.fetchall():
                    nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                    print(f"   - {column_name}: {data_type} {nullable}")
            else:
                print("⚠️  Users table not found")
            
            return tables
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return []

def main():
    print("🍃 Gold Leaves Database Setup")
    print("=" * 40)
    
    # Validate configuration
    print("🔧 Checking configuration...")
    if not validate_config():
        print("❌ Configuration validation failed")
        return False
    print("✅ Configuration valid")
    
    # Test connection
    print("\n🔗 Testing database connection...")
    if not test_connection():
        print("""
💡 To set up PostgreSQL:

1. Install PostgreSQL on your system
2. Create a database named 'goldleaves'
3. Update the DATABASE_URL in your .env file if needed
4. Current DATABASE_URL from config: 
   postgresql://postgres:postgres@localhost:5432/goldleaves

5. Run migrations:
   alembic upgrade head
        """)
        return False
    
    # Check tables
    print("\n📋 Checking database tables...")
    tables = check_tables()
    
    if 'users' not in tables:
        print("""
🚀 Next steps:
1. Run the migration to create tables:
   alembic upgrade head
        """)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
