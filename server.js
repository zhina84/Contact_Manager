const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;
const DATA_FILE = path.join(__dirname, 'contacts.json');

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

//  با React 
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', 'http://localhost:3001');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  res.header('Access-Control-Allow-Methods', 'GET, POST, DELETE, PUT');
  next();
});


// مقداردهی اولیه فایل JSON
if (!fs.existsSync(DATA_FILE)) {
  fs.writeFileSync(DATA_FILE, JSON.stringify([], null, 2));
}

function readContacts() {
  const data = fs.readFileSync(DATA_FILE, 'utf8');
  return JSON.parse(data);
}

function writeContacts(contacts) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(contacts, null, 2));
}

// دریافت همه مخاطبین (GET) 
app.get('/api/contacts', (req, res) => {
  const contacts = readContacts();
  res.json(contacts);
});


//  افزودن مخاطب جدید (POST) 
app.post('/api/contacts', (req, res) => {
  const { name, email, phone, city, group } = req.body;
  if (!name || name.trim() === '') {
    return res.status(400).json({ error: 'نام الزامی است' });
  }
  const contacts = readContacts();
  const newContact = {
    id: Date.now(),
    name: name.trim(),
    email: email?.trim() || '',
    phone: phone?.trim() || '',
    city: city?.trim() || '',
    group: group || 'سایر'
  };
  contacts.push(newContact);
  writeContacts(contacts);
  res.status(201).json(newContact);
});


//  API: جستجو 
app.get('/api/contacts/search', (req, res) => {
  const keyword = (req.query.q || '').trim().toLowerCase();
  const groupFilter = req.query.group_filter || '';
  let contacts = readContacts();
  
  if (keyword) {
    contacts = contacts.filter(c => 
      c.name.toLowerCase().includes(keyword) ||
      c.email.toLowerCase().includes(keyword) ||
      c.phone.includes(keyword) ||
      c.city.toLowerCase().includes(keyword)
    );
  }
  if (groupFilter) {
    contacts = contacts.filter(c => c.group === groupFilter);
  }
  res.json(contacts);
});



app.get('/', (req, res) => {
  let html = fs.readFileSync(path.join(__dirname, 'form.html'), 'utf8');
  if (req.query.success === '1') {
    html = html.replace('</body>', `<script>window.onload=()=>{let m=document.createElement('div');m.innerText='✅ مخاطب با موفقیت اضافه شد.';m.style.background='#4caf50';m.style.color='white';m.style.padding='10px';m.style.borderRadius='8px';m.style.marginBottom='15px';document.querySelector('.form-container').prepend(m);setTimeout(()=>m.remove(),3000);}</script></body>`);
  }
  res.send(html);
});

app.get('/search', (req, res) => {
  res.sendFile(path.join(__dirname, 'search.html'));
});

app.post('/save', (req, res) => {
  const { name, email, phone, city, group } = req.body;
  if (!name || name.trim() === '') return res.send('نام الزامی است. <a href="/">بازگشت</a>');
  const contacts = readContacts();
  const newContact = {
    id: Date.now(),
    name: name.trim(),
    email: email?.trim() || '',
    phone: phone?.trim() || '',
    city: city?.trim() || '',
    group: group || 'سایر'
  };
  contacts.push(newContact);
  writeContacts(contacts);
  res.redirect('/?success=1');
});

app.get('/search_results', (req, res) => {
  const keyword = (req.query.q || '').trim();
  const groupFilter = req.query.group_filter || '';
  let contacts = readContacts();
  if (keyword) {
    const kw = keyword.toLowerCase();
    contacts = contacts.filter(c => 
      c.name.toLowerCase().includes(kw) ||
      c.email.toLowerCase().includes(kw) ||
      c.phone.includes(kw) ||
      c.city.toLowerCase().includes(kw)
    );
  }
  if (groupFilter) {
    contacts = contacts.filter(c => c.group === groupFilter);
  }

  let rowsHtml = contacts.length === 0 ? '<p>❌ هیچ مخاطبی یافت نشد.</p>' : `
    <table style="width:100%; border-collapse:collapse;">
      <tr style="background:#f0f0f0;"><th>نام</th><th>ایمیل</th><th>تلفن</th><th>شهر</th><th>گروه</th></tr>
      ${contacts.map(c => `
        <tr style="border-bottom:1px solid #eee;">
          <td style="padding:8px;">${escapeHtml(c.name)}</td>
          <td>${escapeHtml(c.email)}</td>
          <td>${escapeHtml(c.phone)}</td>
          <td>${escapeHtml(c.city)}</td>
          <td>${escapeHtml(c.group)}</td>
        </tr>
      `).join('')}
    </table>
  `;

  const resultPage = `
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>نتایج جستجو</title>
    <style>body{font-family:sans-serif; background:linear-gradient(135deg,#667eea,#764ba2); padding:20px} .card{background:white; border-radius:20px; max-width:800px; margin:auto; padding:20px}</style>
    </head><body><div class="card"><h2>نتایج جستجو (${contacts.length} مخاطب)</h2>${rowsHtml}<br><a href="/search">جستجوی جدید</a> | <a href="/">افزودن مخاطب</a></div></body></html>`;
  res.send(resultPage);
});


function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[m]);
}

app.listen(PORT, () => console.log(`✅ Server running at http://localhost:${PORT}`));