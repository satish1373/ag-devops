const express = require('express');
const router = express.Router();

// Simple user routes for demo
router.get('/profile', (req, res) => {
  res.json({
    id: 1,
    username: 'demo',
    email: 'demo@example.com'
  });
});

module.exports = router;
