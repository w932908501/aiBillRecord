import streamlit as st
import pandas as pd
from utils import billRecord_agent, save_to_database, fetch_from_database

st.title('账单记录助手')

qwen_api_key = st.text_input('请输入Qwen API Key', type='password')
query = st.text_input('请输入您的消费行为描述（如：我今天吃汉堡花了30元）')

if 'data_updated' not in st.session_state:
    st.session_state['data_updated'] = False

if st.button('提交'):
    if not qwen_api_key:
        st.warning('请先输入API Key')
    elif not query:
        st.warning('请输入消费行为描述')
    else:
        try:
            response = billRecord_agent(qwen_api_key, query)
            save_to_database(response)
            st.session_state['data_updated'] = True
            st.success(f"已记录: {response}")
        except Exception as e:
            st.error(f"记录失败: {e}")

# 获取所有账单数据
def get_all_bills():
    import sqlite3
    conn = sqlite3.connect('bills.db')
    cursor = conn.cursor()
    cursor.execute('SELECT category, amount FROM bills')
    rows = cursor.fetchall()
    conn.close()
    return rows

bills = get_all_bills()

# 展示所有账单内容表格（可编辑）
import sqlite3
conn = sqlite3.connect('bills.db')
cursor = conn.cursor()
cursor.execute('SELECT id, category, amount, detail, date FROM bills')
all_rows = cursor.fetchall()
conn.close()

if all_rows:
    df_all = pd.DataFrame(all_rows, columns=['ID', '类别', '金额', '明细', '日期'])
    st.subheader('账单明细表')
    edited_df = st.data_editor(df_all, num_rows="dynamic", use_container_width=True, key="editable_table")

    # 检查被删除的行
    deleted_ids = set(df_all['ID']) - set(edited_df['ID'])
    if deleted_ids:
        for bill_id in deleted_ids:
            conn = sqlite3.connect('bills.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bills WHERE id=?', (bill_id,))
            conn.commit()
            conn.close()
        st.success('已删除选中账单！')
        st.rerun()

    # 自动保存修改：对比原始df_all和edited_df，若有变化则更新数据库
    if not edited_df.equals(df_all):
        for idx, row in edited_df.iterrows():
            bill_id = row['ID']
            category = row['类别']
            amount = row['金额']
            detail = row['明细']
            date = row['日期']
            # 更新数据库
            conn = sqlite3.connect('bills.db')
            cursor = conn.cursor()
            cursor.execute('''UPDATE bills SET category=?, amount=?, detail=?, date=? WHERE id=?''',
                           (category, amount, detail, date, bill_id))
            conn.commit()
            conn.close()
        st.success('账单明细已自动保存！')
        st.rerun()

# 统计信息展示
bills = get_all_bills()
if bills:
    df = pd.DataFrame(bills, columns=['category', 'amount'])
    summary = df.groupby('category', as_index=False)['amount'].sum()
    st.bar_chart(data=summary, x='category', y='amount')
else:
    st.info('暂无账单数据，快来添加一条吧！')
