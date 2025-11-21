import sqlite3
import pandas as pd
import re
import uuid

def create_dummy_data():
    # Connect to (or create) the database file
    conn = sqlite3.connect('salaries.db')
    cursor = conn.cursor()

    # 1. Re-create the table to update schema
    cursor.execute('DROP TABLE IF EXISTS compensation')
    
    cursor.execute('''
    CREATE TABLE compensation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash_id TEXT,
        company TEXT,
        level_code TEXT,
        title TEXT,
        location TEXT,
        total_comp INTEGER,
        base_salary INTEGER,
        stock_grant INTEGER,
        bonus INTEGER,
        yoe INTEGER
    )
    ''')

    # 2. Read new data from Excel
    excel_file = "2025 MSFT Rewards Data.xlsx"
    try:
        df = pd.read_excel(excel_file)
        print(f"📖 Read {len(df)} rows from {excel_file}")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        conn.close()
        return

    data_rows = []
    
    for _, row in df.iterrows():
        company = "Microsoft"
        hash_id = uuid.uuid4().hex
        
        # Level Code
        level_code = str(row.get('Level (your new level if promoted)', ''))
        if level_code == 'nan': level_code = ''
        
        # Level Name / Role
        title = str(row.get('Role', ''))
        if title == 'nan': title = ''

        # Location
        location = str(row.get('Location/Currency', ''))
        if location == 'nan': location = ''

        # Financials (Handle NaNs and convert to int)
        def parse_money(val):
            try:
                return int(float(val)) if pd.notnull(val) else 0
            except:
                return 0

        base_salary = parse_money(row.get('New Base Pay'))
        stock_grant = parse_money(row.get('Stock Award Amount'))
        bonus = parse_money(row.get('Bonus Amount'))
        total_comp = base_salary + stock_grant + bonus

        # YOE Parsing
        yoe_str = str(row.get('Total Years of Experience', '0'))
        # Extract first number found
        yoe_match = re.search(r'\d+', yoe_str)
        yoe = int(yoe_match.group()) if yoe_match else 0

        data_rows.append((hash_id, company, level_code, title, location, total_comp, base_salary, stock_grant, bonus, yoe))

    # 3. Add Manual Data (China Tech Companies)
    manual_data = [
        ("字节跳动", "1-2", "工程师", 420000),
        ("字节跳动", "2-1", "资深工程师", 620000),
        ("字节跳动", "2-2", "专家", 1070000),
        ("字节跳动", "3-1", "高级专家", 1745000),
        ("字节跳动", "3-2", "资深专家", 2750000),
        ("字节跳动", "4-1", "——", 4885000),
        ("腾讯", "6", "——", 505000),
        ("腾讯", "7", "工程师", 470000),
        ("腾讯", "8", "工程师", 505000),
        ("腾讯", "9", "工程师", 685000),
        ("腾讯", "10", "工程师/副组长", 1010000),
        ("腾讯", "11", "组长", 1555000),
        ("腾讯", "12", "专家/副总监", 2580000),
        ("腾讯", "13", "专家/总监", "——"),
        ("腾讯", "14", "——", "——"),
        ("阿里巴巴", "P5", "工程师", 445000),
        ("阿里巴巴", "P6", "高级工程师", 560000),
        ("阿里巴巴", "P7", "专家/经理", 1045000),
        ("阿里巴巴", "P8", "高级专家/资深经理", 2050000),
        ("阿里巴巴", "P9", "资深专家/总监", 3350000),
        ("阿里巴巴", "P10", "研究员/资深总监", "——"),
        ("百度", "T4", "高级工程师", 440000),
        ("百度", "T5", "资深工程师", 595000),
        ("百度", "T6", "技术专家", 830000),
        ("百度", "T7", "高级专家", 1560000),
        ("百度", "T8", "——", 2515000),
        ("百度", "T9", "研究员", 3735000),
        ("百度", "T10", "——", "——"),
        ("美团", "L6", "——", 465000),
        ("美团", "L7", "——", 625000),
        ("美团", "L8", "——", 1050000),
        ("美团", "L9", "——", 2990000),
        ("美团", "L10", "——", 4880000),
        ("华为", "13", "——", 235000),
        ("华为", "14", "——", 360000),
        ("华为", "15", "——", 435000),
        ("华为", "16", "——", 610000),
        ("华为", "17", "——", 850000),
        ("华为", "18", "——", 1310000),
        ("华为", "19", "——", "——"),
        ("华为", "20", "——", 2785000),
        ("拼多多", "员工", "员工", 885000),
        ("拼多多", "小组长", "小组长", 1740000),
        ("拼多多", "二级主管", "二级主管", "——"),
        ("拼多多", "一级主管", "一级主管", "——"),
        ("京东", "T4", "——", 385000),
        ("京东", "T5", "——", 480000),
        ("京东", "T6", "——", 635000),
        ("京东", "T7", "——", 855000),
        ("京东", "T8", "——", 1120000),
        ("京东", "T9", "——", 1195000),
        ("京东", "T10", "——", "——")
    ]

    print(f"🇨🇳 Processing {len(manual_data)} manual records for China...")

    for item in manual_data:
        company, level_code, title, comp_val = item
        hash_id = uuid.uuid4().hex
        location = "China (CNY)"
        
        # Parse compensation
        total_comp = 0
        if isinstance(comp_val, (int, float)):
            total_comp = int(comp_val)
        
        # Clean up level name
        if title == "——":
            title = ""

        # Other fields are unknown
        base_salary = 0
        stock_grant = 0
        bonus = 0
        yoe = 0

        data_rows.append((hash_id, company, level_code, title, location, total_comp, base_salary, stock_grant, bonus, yoe))

    # 4. Insert data
    cursor.executemany('''
    INSERT INTO compensation (hash_id, company, level_code, title, location, total_comp, base_salary, stock_grant, bonus, yoe)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data_rows)

    conn.commit()
    conn.close()
    print(f"✅ database 'salaries.db' updated successfully with {len(data_rows)} records.")

if __name__ == "__main__":
    create_dummy_data()