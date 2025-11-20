import sqlite3
import random

def create_dummy_data():
    # Connect to (or create) the database file
    conn = sqlite3.connect('salaries.db')
    cursor = conn.cursor()

    # 1. Create the table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compensation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT,
        level_code TEXT,
        level_name TEXT,
        location TEXT,
        total_comp INTEGER,
        base_salary INTEGER,
        stock_grant INTEGER,
        bonus INTEGER,
        yoe INTEGER
    )
    ''')

    # 2. Generate Dummy Data
    companies = [
        ('Google', ['L3', 'L4', 'L5', 'L6', 'L7']),
        ('Meta', ['E3', 'E4', 'E5', 'E6', 'E7']),
        ('Amazon', ['L4', 'L5', 'L6', 'L7', 'L8']),
        ('Microsoft', ['59', '60', '61', '62', '63']),
        ('Apple', ['ICT3', 'ICT4', 'ICT5', 'ICT6', 'ICT7'])
    ]
    
    locations = ['Seattle, WA', 'San Francisco, CA', 'New York, NY', 'Austin, TX', 'Remote']

    data_rows = []
    
    # Generate 200 random records
    for _ in range(200):
        name = ""
        comp_info = random.choice(companies)
        company = comp_info[0]
        level = random.choice(comp_info[1])
        loc = random.choice(locations)
        yoe = random.randint(0, 15)
        
        # Simple logic to make numbers somewhat realistic based on level index
        level_idx = comp_info[1].index(level)
        base_mult = 120000 + (level_idx * 40000)
        
        base = int(base_mult * random.uniform(0.9, 1.2))
        stock = int(base * random.uniform(0.2, 0.8) * (level_idx + 1))
        bonus = int(base * 0.15)
        total = base + stock + bonus

        data_rows.append((company, level, "Software Engineer", loc, total, base, stock, bonus, yoe, name))

    # 3. Insert data
    cursor.executemany('''
    INSERT INTO compensation (company, level_code, level_name, location, total_comp, base_salary, stock_grant, bonus, yoe, name)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data_rows)

    conn.commit()
    conn.close()
    print("✅ database 'salaries.db' created successfully with 200 records.")

if __name__ == "__main__":
    create_dummy_data()