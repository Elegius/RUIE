#!/usr/bin/env node
/**
 * RUIE Electron Quick Start
 * ========================
 * 
 * One-command startup after setup is complete
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const projectDir = __dirname;

console.log(`
╔════════════════════════════════════════════════════╗
║        RUIE - Electron Edition Ready!              ║
║                                                    ║
║  Starting Flask server + Electron app...          ║
╚════════════════════════════════════════════════════╝
`);

console.log('📦 Environment Check:');
console.log(`  ✓ Node.js: ${process.version}`);
console.log(`  ✓ npm: ${require('child_process').execSync('npm -v').toString().trim()}`);
console.log(`  ✓ Python: ${require('child_process').execSync('python --version 2>&1').toString().trim()}`);

console.log('\n🚀 Starting app...');
console.log('  Flask will start automatically');
console.log('  Electron window will open to http://127.0.0.1:5000\n');

// Start Electron
const electron = spawn('npm', ['start'], {
  cwd: projectDir,
  stdio: 'inherit',
  shell: process.platform === 'win32'
});

electron.on('error', (error) => {
  console.error('❌ Failed to start app:', error);
  process.exit(1);
});

electron.on('exit', (code) => {
  console.log(`\n👋 App closed (exit code: ${code})`);
  process.exit(code);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n⚠️  Shutting down...');
  electron.kill();
});
