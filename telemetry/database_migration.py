#!/usr/bin/env python3
"""
Database Migration Script for Enhanced Duration Tracking

Migrates existing telemetry database to support duration tracking, session management,
and enhanced analytics capabilities while preserving all existing data.
"""

import sqlite3
import os
import uuid
from datetime import datetime
from typing import Optional
import json

class DatabaseMigrator:
    """Handles database schema migrations for duration tracking enhancements."""
    
    def __init__(self, db_path: str = "database/telemetry.db"):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def migrate(self) -> bool:
        """
        Perform complete migration to enhanced duration tracking schema.
        Returns True if migration successful, False otherwise.
        """
        try:
            # Step 1: Create backup
            print(f"Creating backup: {self.backup_path}")
            self._create_backup()
            
            # Step 2: Check current schema version
            schema_version = self._get_schema_version()
            print(f"Current schema version: {schema_version}")
            
            # Step 3: Apply migrations based on current version
            if schema_version < 1:
                print("Applying migration v1: Adding duration tracking columns...")
                self._migrate_to_v1()
            
            if schema_version < 2:
                print("Applying migration v2: Enhanced monitoring sessions...")
                self._migrate_to_v2()
            
            if schema_version < 3:
                print("Applying migration v3: Domain events and indexes...")
                self._migrate_to_v3()
            
            # Step 4: Update schema version
            self._set_schema_version(3)
            
            print("✅ Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print(f"Restoring from backup: {self.backup_path}")
            self._restore_backup()
            return False
    
    def _create_backup(self):
        """Create a backup of the current database."""
        if os.path.exists(self.db_path):
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
    
    def _restore_backup(self):
        """Restore database from backup."""
        if os.path.exists(self.backup_path):
            import shutil
            shutil.copy2(self.backup_path, self.db_path)
    
    def _get_schema_version(self) -> int:
        """Get current schema version from database."""
        if not os.path.exists(self.db_path):
            return 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if schema_version table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='schema_version'
                """)
                
                if cursor.fetchone() is None:
                    # No schema_version table = version 0
                    return 0
                
                cursor.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1")
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except sqlite3.Error:
            return 0
    
    def _set_schema_version(self, version: int):
        """Set the current schema version in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create schema_version table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER NOT NULL,
                    migration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            
            # Insert new version record
            cursor.execute("""
                INSERT INTO schema_version (version, description)
                VALUES (?, ?)
            """, (version, f"Enhanced duration tracking schema v{version}"))
            
            conn.commit()
    
    def _migrate_to_v1(self):
        """Migration v1: Add duration tracking columns to telemetry_events."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if columns already exist
            cursor.execute("PRAGMA table_info(telemetry_events)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Add duration_seconds column if it doesn't exist
            if 'duration_seconds' not in columns:
                cursor.execute("ALTER TABLE telemetry_events ADD COLUMN duration_seconds REAL")
                print("  ✅ Added duration_seconds column")
            
            # Add session_id column if it doesn't exist
            if 'session_id' not in columns:
                cursor.execute("ALTER TABLE telemetry_events ADD COLUMN session_id TEXT")
                print("  ✅ Added session_id column")
            
            conn.commit()
    
    def _migrate_to_v2(self):
        """Migration v2: Enhanced monitoring sessions with duration fields."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if monitoring_sessions table exists and get its structure
            cursor.execute("PRAGMA table_info(monitoring_sessions)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # Check if we need to add new duration columns
            duration_columns = [
                'session_id', 'total_runtime_seconds', 'total_idle_seconds',
                'total_active_seconds', 'total_run_command_seconds', 'total_pause_seconds'
            ]
            
            columns_to_add = [col for col in duration_columns if col not in existing_columns]
            
            if columns_to_add:
                # Need to recreate table with new schema
                print("  🔄 Recreating monitoring_sessions table with enhanced schema...")
                
                # Backup existing data
                cursor.execute("SELECT * FROM monitoring_sessions")
                existing_data = cursor.fetchall()
                
                # Drop old table
                cursor.execute("DROP TABLE monitoring_sessions")
                
                # Create new table with enhanced schema
                cursor.execute("""
                    CREATE TABLE monitoring_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        session_start DATETIME NOT NULL,
                        session_end DATETIME,
                        total_runtime_seconds REAL DEFAULT 0,
                        total_idle_seconds REAL DEFAULT 0,
                        total_active_seconds REAL DEFAULT 0,
                        total_run_command_seconds REAL DEFAULT 0,
                        total_pause_seconds REAL DEFAULT 0,
                        total_events INTEGER DEFAULT 0,
                        config_snapshot TEXT
                    )
                """)
                
                # Migrate existing data with generated session IDs
                for row in existing_data:
                    session_id = str(uuid.uuid4())
                    # Map old columns to new schema (id, session_start, session_end, total_events, config_snapshot)
                    cursor.execute("""
                        INSERT INTO monitoring_sessions 
                        (session_id, session_start, session_end, total_events, config_snapshot)
                        VALUES (?, ?, ?, ?, ?)
                    """, (session_id, row[1], row[2], row[3] if len(row) > 3 else 0, row[4] if len(row) > 4 else None))
                
                print("  ✅ Enhanced monitoring_sessions table created and data migrated")
            
            conn.commit()
    
    def _migrate_to_v3(self):
        """Migration v3: Domain events table and performance indexes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create domain_events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS domain_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aggregate_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER NOT NULL
                )
            """)
            print("  ✅ Created domain_events table")
            
            # Create performance indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_telemetry_events_timestamp ON telemetry_events(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_telemetry_events_type ON telemetry_events(event_type)",
                "CREATE INDEX IF NOT EXISTS idx_telemetry_events_state ON telemetry_events(state)",
                "CREATE INDEX IF NOT EXISTS idx_telemetry_events_session_id ON telemetry_events(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_telemetry_events_duration ON telemetry_events(duration_seconds)",
                "CREATE INDEX IF NOT EXISTS idx_monitoring_sessions_session_id ON monitoring_sessions(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_monitoring_sessions_start ON monitoring_sessions(session_start)",
                "CREATE INDEX IF NOT EXISTS idx_domain_events_aggregate ON domain_events(aggregate_id)",
                "CREATE INDEX IF NOT EXISTS idx_domain_events_type ON domain_events(event_type)",
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            print("  ✅ Created performance indexes")
            conn.commit()

def run_migration(db_path: str = "database/telemetry.db") -> bool:
    """
    Convenience function to run the database migration.
    
    Args:
        db_path: Path to the SQLite database file
    
    Returns:
        True if migration successful, False otherwise
    """
    migrator = DatabaseMigrator(db_path)
    return migrator.migrate()

if __name__ == "__main__":
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/telemetry.db"
    print(f"Running database migration for: {db_path}")
    
    success = run_migration(db_path)
    if success:
        print("\n🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Migration failed!")
        sys.exit(1) 