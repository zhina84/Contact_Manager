from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import sqlite3
import os

DB_NAME = "contacts.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # NEW group 
    c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            city TEXT,
            "group" TEXT DEFAULT 'سایر'
        )
    ''')
    # NEW CHANGE: alter existing table if "group" column is missing
    try:
        c.execute('ALTER TABLE contacts ADD COLUMN "group" TEXT DEFAULT "سایر"')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            with open("form.html", "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        elif path == "/search":
            with open("search.html", "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        elif path == "/search_results":
            query = parse_qs(parsed.query)
            search_term = query.get("q", [""])[0].strip()
            #  read group_filter from query string
            group_filter = query.get("group_filter", [""])[0].strip()

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            # NEW CHANGE: all SELECTs now include the "group" column with quotes
            if search_term and group_filter:
                c.execute('''
                    SELECT name, email, phone, city, "group" FROM contacts
                    WHERE (name LIKE ? OR email LIKE ? OR phone LIKE ? OR city LIKE ?)
                    AND "group" = ?
                ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', group_filter))
            elif search_term:
                c.execute('''
                    SELECT name, email, phone, city, "group" FROM contacts
                    WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? OR city LIKE ?
                ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            elif group_filter:
                c.execute('SELECT name, email, phone, city, "group" FROM contacts WHERE "group" = ?', (group_filter,))
            else:
                c.execute('SELECT name, email, phone, city, "group" FROM contacts')

            rows = c.fetchall()
            conn.close()

            # Build results page – NEW CHANGE: added 'Group' column in table
            html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .card { background: white; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: #4a6cf7; color: white; padding: 25px; text-align: center; }
        .header h1 { font-size: 28px; }
        .results { padding: 30px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; }
        th { background: #f0f2ff; color: #4a6cf7; }
        tr:hover { background: #f9f9ff; }
        .no-result { text-align: center; padding: 30px; color: #888; }
        .badge { background: #e0e7ff; color: #4a6cf7; padding: 4px 12px; border-radius: 20px; font-size: 12px; display: inline-block; margin-bottom: 15px; }
        .nav-links { text-align: center; margin-top: 20px; background: white; border-radius: 20px; padding: 15px; }
        .nav-links a { color: #4a6cf7; text-decoration: none; margin: 0 10px; font-weight: 500; }
        @media (max-width: 600px) { th, td { font-size: 12px; padding: 8px; } }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="header">
            <h1>🔍 Search Results</h1>
        </div>
        <div class="results">
            <div class="badge">Search term: """ + (search_term if search_term else "All contacts") + """</div>
"""
            if not rows:
                html += '<div class="no-result">❌ No contacts found.</div>'
            else:
                # NEW CHANGE: added <th>Group</th> and the extra column for group
                html += '<td><thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>City</th><th>Group</th></tr></thead><tbody>'
                for row in rows:
                    html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>"
                html += '</tbody></table>'
            html += """
        </div>
    </div>
    <div class="nav-links">
        <a href="/search">🔍 New Search</a> | <a href="/">➕ Add Contact</a>
    </div>
</div>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        if self.path == "/save":
            length = int(self.headers["Content-Length"])
            data = self.rfile.read(length).decode()
            params = parse_qs(data)

            name = params.get("name", [""])[0]
            email = params.get("email", [""])[0]
            phone = params.get("phone", [""])[0]
            city = params.get("city", [""])[0]
            # NEW CHANGE: get group from form data, default to 'سایر'
            group = params.get("group", ["سایر"])[0]

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            # NEW CHANGE:
            c.execute('''
                INSERT INTO contacts (name, email, phone, city, "group")
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, phone, city, group))
            conn.commit()
            conn.close()

            # Thank you page – NEW CHANGE: added line to display group
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .card {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 100%;
            text-align: center;
            overflow: hidden;
            animation: fadeIn 0.5s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .header {{
            background: #4caf50;
            color: white;
            padding: 30px;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .content {{
            padding: 30px;
        }}
        .info {{
            background: #f5f5f5;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            text-align: left;
        }}
        .info p {{
            margin: 10px 0;
            font-size: 16px;
            color: #333;
        }}
        .info strong {{
            color: #4a6cf7;
        }}
        .buttons {{
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 20px;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            background: #4a6cf7;
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: background 0.3s;
        }}
        .btn:hover {{
            background: #3451c9;
        }}
        .btn-secondary {{
            background: #6c757d;
        }}
        .btn-secondary:hover {{
            background: #5a6268;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>✅ Thank You!</h1>
            <p>Contact has been saved successfully</p>
        </div>
        <div class="content">
            <div class="info">
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email if email else "—"}</p>
                <p><strong>Phone:</strong> {phone if phone else "—"}</p>
                <p><strong>City:</strong> {city if city else "—"}</p>
                <!-- NEW CHANGE: display the selected group -->
                <p><strong>Group:</strong> {group}</p>
            </div>
            <div class="buttons">
                <a href="/" class="btn">➕ Add Another</a>
                <a href="/search" class="btn btn-secondary">🔍 Search</a>
            </div>
        </div>
    </div>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

if __name__ == "__main__":
    init_db()
    server = HTTPServer(("localhost", 8000), Handler)
    print("Server running at http://localhost:8000")
    server.serve_forever()