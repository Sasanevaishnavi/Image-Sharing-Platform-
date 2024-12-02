import sqlite3

conn = sqlite3.connect("User_data.db")
cursor = conn.cursor()

# cursor.execute("ALTER TABLE images ADD COLUMN likes INTEGER DEFAULT 0;")



cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')

print("Database and table created successfully.")

cursor.execute('''
    CREATE TABLE IF NOT EXISTS images(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NOT NULL
    )

''')
print("Images table created successfully.")

cursor.execute('''
    CREATE TABLE likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    image_id TEXT NOT NULL,
    UNIQUE(user_id, image_id) 
);
''')

cursor.execute('''
    CREATE TABLE commends(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    image_id TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (image_id) REFERENCES images (filename)
);
''')

conn.commit()
conn.close()





