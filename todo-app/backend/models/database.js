const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, '../database/todos.db');
const db = new sqlite3.Database(dbPath);

// Initialize database tables
db.serialize(() => {
  // Users table
  db.run(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Todos table
  db.run(`
    CREATE TABLE IF NOT EXISTS todos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      description TEXT,
      completed BOOLEAN DEFAULT 0,
      priority TEXT DEFAULT 'medium',
      category TEXT DEFAULT 'general',
      due_date DATETIME,
      user_id INTEGER,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    )
  `);

  // Insert sample data
  db.run(`
    INSERT OR IGNORE INTO users (id, username, email, password_hash) 
    VALUES (1, 'demo', 'demo@example.com', '$2a$10$sample.hash.here')
  `);

  db.run(`
    INSERT OR IGNORE INTO todos (title, description, completed, priority, user_id) 
    VALUES 
    ('Welcome to Todo App', 'This is your first todo item', 0, 'high', 1),
    ('Learn React', 'Study React components and hooks', 1, 'medium', 1),
    ('Build API', 'Create REST API endpoints', 0, 'high', 1)
  `);
});

module.exports = db;