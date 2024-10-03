from datetime import datetime

import asyncpg

from config import DATABASE_URL

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    # Создаем таблицу connections, если она не существует
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            tg_id BIGINT PRIMARY KEY NOT NULL,
            balance REAL NOT NULL DEFAULT 0.0,
            trial INTEGER NOT NULL DEFAULT 0
        )
    ''')
    # Создаем таблицу keys, если она не существует
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            tg_id BIGINT NOT NULL,
            client_id TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at BIGINT NOT NULL,
            expiry_time BIGINT NOT NULL,         
            key TEXT NOT NULL,
            server_id TEXT NOT NULL DEFAULT 'server1',  -- новое поле для идентификатора сервера
            PRIMARY KEY (tg_id, client_id)
        )
    ''')
    # Добавляем поле server_id в таблицу keys, если его нет
    try:
        await conn.execute('''
            ALTER TABLE keys
            ADD COLUMN server_id TEXT NOT NULL DEFAULT 'server1'
        ''')
    except asyncpg.exceptions.DuplicateColumnError:
        # Если поле уже существует, ничего не делаем
        pass
    await conn.close()


async def add_connection(tg_id: int, balance: float = 0.0, trial: int = 0):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        INSERT INTO connections (tg_id, balance, trial)
        VALUES ($1, $2, $3)
    ''', tg_id, balance, trial)
    await conn.close()

async def check_connection_exists(tg_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    exists = await conn.fetchval('''
        SELECT EXISTS(SELECT 1 FROM connections WHERE tg_id = $1)
    ''', tg_id)
    await conn.close()
    return exists

async def store_key(tg_id: int, client_id: str, email: str, expiry_time: int, key: str, server_id: str):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        INSERT INTO keys (tg_id, client_id, email, created_at, expiry_time, key, server_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    ''', tg_id, client_id, email, int(datetime.utcnow().timestamp() * 1000), expiry_time, key, server_id)
    await conn.close()

async def get_keys(tg_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    records = await conn.fetch('''
        SELECT client_id, email, created_at, key
        FROM keys
        WHERE tg_id = $1
    ''', tg_id)
    await conn.close()
    return records

async def get_keys_by_server(tg_id: int, server_id: str):
    conn = await asyncpg.connect(DATABASE_URL)
    records = await conn.fetch('''
        SELECT client_id, email, created_at, key
        FROM keys
        WHERE tg_id = $1 AND server_id = $2
    ''', tg_id, server_id)
    await conn.close()
    return records

async def has_active_key(tg_id: int) -> bool:
    conn = await asyncpg.connect(DATABASE_URL)
    count = await conn.fetchval("SELECT COUNT(*) FROM keys WHERE tg_id = $1", tg_id)
    await conn.close()
    return count > 0

async def get_balance(tg_id: int) -> float:
    conn = await asyncpg.connect(DATABASE_URL)
    balance = await conn.fetchval("SELECT balance FROM connections WHERE tg_id = $1", tg_id)
    await conn.close()
    return balance if balance is not None else 0.0

async def update_balance(tg_id: int, amount: float):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        UPDATE connections 
        SET balance = balance + $1 
        WHERE tg_id = $2
    ''', amount, tg_id)
    await conn.close()

async def get_trial(tg_id: int) -> int:
    conn = await asyncpg.connect(DATABASE_URL)
    trial = await conn.fetchval("SELECT trial FROM connections WHERE tg_id = $1", tg_id)
    await conn.close()
    return trial if trial is not None else 0

async def get_key_count(tg_id: int) -> int:
    conn = await asyncpg.connect(DATABASE_URL)
    count = await conn.fetchval('SELECT COUNT(*) FROM keys WHERE tg_id = $1', tg_id)
    await conn.close()
    return count if count is not None else 0

async def get_all_users(conn):
    return await conn.fetch('SELECT tg_id FROM connections')