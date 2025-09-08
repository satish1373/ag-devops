const db = require('../models/database');

const todoController = {
  // Get all todos
  getAllTodos: (req, res) => {
    const userId = req.query.user_id || 1; // Default to demo user
    
    db.all(
      'SELECT * FROM todos WHERE user_id = ? ORDER BY created_at DESC',
      [userId],
      (err, rows) => {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        res.json(rows);
      }
    );
  },

  // Get single todo
  getTodoById: (req, res) => {
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
  },

  // Create new todo
  createTodo: (req, res) => {
    const { title, description, priority = 'medium', category = 'general', due_date } = req.body;
    const userId = req.body.user_id || 1; // Default to demo user

    if (!title) {
      return res.status(400).json({ error: 'Title is required' });
    }

    db.run(
      `INSERT INTO todos (title, description, priority, category, due_date, user_id) 
       VALUES (?, ?, ?, ?, ?, ?)`,
      [title, description, priority, category, due_date, userId],
      function(err) {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        
        // Return the created todo
        db.get('SELECT * FROM todos WHERE id = ?', [this.lastID], (err, row) => {
          if (err) {
            return res.status(500).json({ error: err.message });
          }
          res.status(201).json(row);
        });
      }
    );
  },

  // Update todo
  updateTodo: (req, res) => {
    const { id } = req.params;
    const { title, description, completed, priority, category, due_date } = req.body;

    db.run(
      `UPDATE todos 
       SET title = COALESCE(?, title),
           description = COALESCE(?, description),
           completed = COALESCE(?, completed),
           priority = COALESCE(?, priority),
           category = COALESCE(?, category),
           due_date = COALESCE(?, due_date),
           updated_at = CURRENT_TIMESTAMP
       WHERE id = ?`,
      [title, description, completed, priority, category, due_date, id],
      function(err) {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        
        if (this.changes === 0) {
          return res.status(404).json({ error: 'Todo not found' });
        }

        // Return updated todo
        db.get('SELECT * FROM todos WHERE id = ?', [id], (err, row) => {
          if (err) {
            return res.status(500).json({ error: err.message });
          }
          res.json(row);
        });
      }
    );
  },

  // Delete todo
  deleteTodo: (req, res) => {
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
  }
};

module.exports = todoController;
