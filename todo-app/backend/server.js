const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const { v4: uuidv4 } = require('uuid');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Database setup
const dbPath = path.join(__dirname, 'todos.db');
const db = new sqlite3.Database(dbPath);

// Create todos table
db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS todos (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      description TEXT,
      completed BOOLEAN DEFAULT 0,
      priority TEXT DEFAULT 'medium',
      category TEXT DEFAULT 'general',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Insert sample data
  db.run(`
    INSERT OR IGNORE INTO todos (id, title, description, completed, priority) 
    VALUES 
    ('1', 'Welcome to Todo App', 'This is your first todo item', 0, 'high'),
    ('2', 'Try adding a new todo', 'Click the + button to add a todo', 0, 'medium'),
    ('3', 'Mark todos as complete', 'Click the checkbox to complete tasks', 1, 'low')
  `);
});

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Get all todos
app.get('/api/todos', (req, res) => {
  db.all('SELECT * FROM todos ORDER BY created_at DESC', (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// Get single todo
app.get('/api/todos/:id', (req, res) => {
  const { id } = req.params;
  db.get('SELECT * FROM todos WHERE id = ?', [id], (err, row) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    if (!row) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json(row);
  });
});

// Create new todo
app.post('/api/todos', (req, res) => {
  const { title, description, priority = 'medium', category = 'general' } = req.body;
  
  if (!title) {
    return res.status(400).json({ error: 'Title is required' });
  }

  const id = uuidv4();
  const now = new Date().toISOString();

  db.run(
    `INSERT INTO todos (id, title, description, priority, category, created_at, updated_at) 
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [id, title, description, priority, category, now, now],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      db.get('SELECT * FROM todos WHERE id = ?', [id], (err, row) => {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        res.status(201).json(row);
      });
    }
  );
});

// Update todo
app.put('/api/todos/:id', (req, res) => {
  const { id } = req.params;
  const { title, description, completed, priority, category } = req.body;
  const now = new Date().toISOString();

  db.run(
    `UPDATE todos 
     SET title = COALESCE(?, title),
         description = COALESCE(?, description),
         completed = COALESCE(?, completed),
         priority = COALESCE(?, priority),
         category = COALESCE(?, category),
         updated_at = ?
     WHERE id = ?`,
    [title, description, completed, priority, category, now, id],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      if (this.changes === 0) {
        return res.status(404).json({ error: 'Todo not found' });
      }

      db.get('SELECT * FROM todos WHERE id = ?', [id], (err, row) => {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        res.json(row);
      });
    }
  );
});

// Delete todo
app.delete('/api/todos/:id', (req, res) => {
  const { id } = req.params;

  db.run('DELETE FROM todos WHERE id = ?', [id], function(err) {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    if (this.changes === 0) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    
    res.json({ message: 'Todo deleted successfully' });
  });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
