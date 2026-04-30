import psycopg2
import os
import logging

DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# CONNECTION
# =========================

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# =========================
# INIT DATABASE & MIGRATION
# =========================
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Users table with updated schema
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        credits INTEGER DEFAULT 0,
        total_purchased INTEGER DEFAULT 0,
        total_used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migration: Add columns if they don't exist
    columns_to_add = [
        ("total_purchased", "INTEGER DEFAULT 0"),
        ("total_used", "INTEGER DEFAULT 0")
    ]
    
    for col_name, col_type in columns_to_add:
        cur.execute(f"""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='users' AND column_name='{col_name}') THEN
                ALTER TABLE users ADD COLUMN {col_name} {col_type};
            END IF;
        END $$;
        """)

    # Transactions table (for payments & logs)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        amount INTEGER,
        type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


# =========================
# USER FUNCTIONS
# =========================
def get_user_balance(user_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT credits FROM users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()

    if result:
        conn.close()
        return result[0]
    else:
        # Create user if not exists
        cur.execute(
            "INSERT INTO users (user_id, credits) VALUES (%s, 0)",
            (user_id,)
        )
        conn.commit()
        conn.close()
        return 0


def add_credits(user_id: int, amount: int):
    """
    Increase credits and total_purchased, then log transaction.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Insert or update credits and total_purchased
    cur.execute("""
    INSERT INTO users (user_id, credits, total_purchased)
    VALUES (%s, %s, %s)
    ON CONFLICT (user_id)
    DO UPDATE SET 
        credits = users.credits + %s,
        total_purchased = users.total_purchased + %s
    """, (user_id, amount, amount, amount, amount))

    # Log transaction
    cur.execute("""
    INSERT INTO transactions (user_id, amount, type)
    VALUES (%s, %s, %s)
    """, (user_id, amount, "credit"))

    conn.commit()
    conn.close()


def deduct_credits(user_id: int, amount: int) -> bool:
    """
    Check balance, deduct credits, increase total_used, log transaction.
    Returns True if successful, False if insufficient balance.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Check balance first
    cur.execute("SELECT credits FROM users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()

    if not result or result[0] < amount:
        conn.close()
        return False  # Not enough credits

    # Deduct credits and increase total_used
    cur.execute("""
    UPDATE users
    SET credits = credits - %s,
        total_used = total_used + %s
    WHERE user_id = %s
    """, (amount, amount, user_id))

    # Log transaction
    cur.execute("""
    INSERT INTO transactions (user_id, amount, type)
    VALUES (%s, %s, %s)
    """, (user_id, -amount, "debit"))

    conn.commit()
    conn.close()
    return True


def set_credits(user_id: int, amount: int):
    """
    Overwrite credits for a user.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO users (user_id, credits)
    VALUES (%s, %s)
    ON CONFLICT (user_id)
    DO UPDATE SET credits = %s
    """, (user_id, amount, amount))

    # Log transaction for audit trail
    cur.execute("""
    INSERT INTO transactions (user_id, amount, type)
    VALUES (%s, %s, %s)
    """, (user_id, amount, "set_admin"))

    conn.commit()
    conn.close()


# =========================
# DEBUG / TEST
# =========================
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully ✅")
