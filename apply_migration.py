#!/usr/bin/env python3
"""Script para aplicar as mudanças no banco de dados"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'poker.db')

# Se o banco não existe, criar usando o app.py para garantir todas as colunas
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}. Creating new database with all columns...")
    from app import app, db
    with app.app_context():
        db.create_all()
    print("✅ New database created with tournament support!")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Adicionar colunas na tabela game
    print("Adding columns to game table...")
    cursor.execute("ALTER TABLE game ADD COLUMN game_type VARCHAR(20) DEFAULT 'cash' NOT NULL")
    print("✓ game_type added")
except sqlite3.OperationalError as e:
    print(f"game_type: {e}")

try:
    cursor.execute("ALTER TABLE game ADD COLUMN blind_structure TEXT")
    print("✓ blind_structure added")
except sqlite3.OperationalError as e:
    print(f"blind_structure: {e}")

try:
    cursor.execute("ALTER TABLE game ADD COLUMN blind_duration INTEGER")
    print("✓ blind_duration added")
except sqlite3.OperationalError as e:
    print(f"blind_duration: {e}")

try:
    cursor.execute("ALTER TABLE game ADD COLUMN rebuy_limit INTEGER DEFAULT 2")
    print("✓ rebuy_limit added")
except sqlite3.OperationalError as e:
    print(f"rebuy_limit: {e}")

try:
    cursor.execute("ALTER TABLE game ADD COLUMN rebuy_until_level INTEGER DEFAULT 6")
    print("✓ rebuy_until_level added")
except sqlite3.OperationalError as e:
    print(f"rebuy_until_level: {e}")

try:
    cursor.execute("ALTER TABLE game ADD COLUMN current_level INTEGER DEFAULT 1 NOT NULL")
    print("✓ current_level added")
except sqlite3.OperationalError as e:
    print(f"current_level: {e}")

# Adicionar coluna na tabela player
try:
    print("\nAdding column to player table...")
    cursor.execute("ALTER TABLE player ADD COLUMN rebuys_used INTEGER DEFAULT 0 NOT NULL")
    print("✓ rebuys_used added")
except sqlite3.OperationalError as e:
    print(f"rebuys_used: {e}")

conn.commit()
conn.close()

print("\n✅ Migration completed successfully!")
