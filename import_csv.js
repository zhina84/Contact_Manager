const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

const DB_NAME = 'contacts.db';
const CSV_FILE = 'contacts.csv';

const db = new sqlite3.Database(DB_NAME);

db.run(`CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  city TEXT,
  "group" TEXT
)`);

const content = fs.readFileSync(CSV_FILE, 'utf-8');
const lines = content.split(/\r?\n/);

const stmt = db.prepare(`INSERT INTO contacts (name, email, phone, city, "group") VALUES (?, ?, ?, ?, ?)`);

for (let i = 0; i < lines.length; i++) {
  const row = lines[i].trim();
  if (row === '') continue;
  const cols = row.split(',');
  if (cols.length >= 3) {
    const name = cols[0].trim();
    const email = cols[1].trim();
    const phone = cols[2].trim();
    const city = "";
    const group = "سایر";
    stmt.run(name, email, phone, city, group);
  }
}

stmt.finalize(() => {
  console.log('✅ داده‌های contacts.csv با موفقیت به دیتابیس اضافه شدند.');
  db.close();
});