#!/usr/bin/env node

/**
 * Check if Python server is available in development
 */

const fs = require('fs');
const path = require('path');

const serverPath = path.join(__dirname, '../../server.py');

if (!fs.existsSync(serverPath)) {
  console.error(`Error: server.py not found at ${serverPath}`);
  process.exit(1);
}

console.log('✓ server.py found');
process.exit(0);
