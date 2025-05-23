import os
import psycopg2

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "587289")
DB_NAME = os.getenv("POSTGRES_DB", "aipcf")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # 문의 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS inquiries (
        id SERIAL PRIMARY KEY,
        item_no TEXT,
        status TEXT,
        count FLOAT,
        buyer_comments TEXT,
        company TEXT,
        name TEXT,
        builder_reply TEXT,
        status_for_sort TEXT
    )''')

    # 사용자 테이블 추가
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    # 사용자별 호선 권한 테이블 (향후 확장용)
    c.execute('''CREATE TABLE IF NOT EXISTS user_ships (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        ship_no TEXT
    )''')

    conn.commit()
    conn.close()

def save_to_db(item_no, status, count, buyer_comments, company, name, builder_reply, status_for_sort):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO inquiries (item_no, status, count, buyer_comments, company, name, builder_reply, status_for_sort)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
              (item_no, status, count, buyer_comments, company, name, builder_reply, status_for_sort))
    conn.commit()
    conn.close()

def update_db(row_id, item_no, company, name, status, buyer_comments, builder_reply, status_for_sort):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''UPDATE inquiries SET
        item_no=%s, company=%s, name=%s, status=%s,
        buyer_comments=%s, builder_reply=%s, status_for_sort=%s
        WHERE id=%s''',
        (item_no, company, name, status, buyer_comments, builder_reply, status_for_sort, row_id))
    conn.commit()
    conn.close()

def bulk_update_data(bulk_data):
    conn = get_db_connection()
    c = conn.cursor()
    for item in bulk_data:
        c.execute('''UPDATE inquiries SET
            item_no=%s, company=%s, name=%s, status=%s,
            buyer_comments=%s, builder_reply=%s, status_for_sort=%s
            WHERE id=%s''',
            (item['item_no'], item['company'], item['name'], item['status'],
             item['inquiry'], item['response'], item['status_for_sort'], item['id']))
    conn.commit()
    conn.close()
    
def create_user(username, password_hashed):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password_hashed.decode('utf-8')))
    conn.commit()
    conn.close()

def check_user(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    conn.close()
    if user:
        return {'id': user[0], 'username': user[1], 'password': user[2]}
    return None