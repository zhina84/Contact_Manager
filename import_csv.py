import sqlite3
import csv

DB_NAME = "contacts.db"

def import_csv():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        with open('contacts.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    name = row[0].strip()
                    email = row[1].strip()
                    phone = row[2].strip()
                    city = ""          
                    group = "سایر"     
                    
                    c.execute('''
                        INSERT INTO contacts (name, email, phone, city, group)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (name, email, phone, city, group))
        conn.commit()
        print(" داده‌های فایل contacts.csv با موفقیت به دیتابیس اضافه شدند.")
    except FileNotFoundError:
        print(" فایل contacts.csv پیدا نشد. لطفاً فایل را در مسیر صحیح قرار دهید.")
    except Exception as e:
        print(f" خطا: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import_csv()
