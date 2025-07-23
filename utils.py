import json
import sqlite3

from langchain.chains.conversation.base import ConversationChain
from langchain_community.chat_models.tongyi import ChatTongyi
from datetime import datetime

PROMPT_TEMPLATE = """
你是一位账单记录助手，你的回应内容取决于用户的请求内容。

1. 对于用户发给你的消费行为描述，按照这样的格式回答，不要有任何额外的信息：
   {"category": "<用户消费行为的类别>","amount": <用户消费的金额>,"detail": "<用户消费行为>","date": "<消费具体日期，格式为YYYY-MM-DD>"}
例如：
   {"category": "餐饮","amount": 150.75,"detail": "吃汉堡","date": "2023-10-01"}
   
请注意，category必须从以下类别中选取：餐饮、购物、交通、住宿、日常、学习、人情、娱乐、美妆、旅游、通讯、医疗、其他。

请将所有输出作为JSON字符串返回。

你要处理的用户请求如下： 
"""

def save_to_database(data):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('bills.db')
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            amount REAL,
            detail TEXT,
            date TEXT
        )
    ''')

    # Insert the data into the table
    cursor.execute('''
        INSERT INTO bills (category, amount, detail, date)
        VALUES (?, ?, ?, ?)
    ''', (data['category'], data['amount'], data['detail'], data['date']))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def billRecord_agent(qwen_api_key, query):
    model = ChatTongyi(
        model="qwen-max",
        temperature=0,
        max_tokens=1500,
        api_key=qwen_api_key
    )

    chain = ConversationChain(llm=model)

    today_str = datetime.now().strftime("%Y-%m-%d")
    # 在用户请求前加一句“今天的日期是：xxxx-xx-xx。”
    prompt = PROMPT_TEMPLATE + f"今天的日期是：{today_str}。\n" + query

    response = chain.invoke({"input": prompt})

    response_dict = json.loads(response["response"])

    print(response_dict)

    return response_dict

def fetch_from_database():
    # Connect to SQLite database
    conn = sqlite3.connect('bills.db')
    cursor = conn.cursor()

    # Fetch all records from the bills table
    cursor.execute('SELECT * FROM bills')
    rows = cursor.fetchall()

    # Print the records
    for row in rows:
        print(row)

    # Close the connection
    conn.close()

