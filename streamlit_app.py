import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

class FinanceTracker:
    def __init__(self):
        if 'transactions' not in st.session_state:
            st.session_state['transactions'] = pd.DataFrame(
                columns=['日期', '類別', '金額', '類型', '備註']
            )
            st.session_state['transactions']['日期'] = pd.to_datetime(st.session_state['transactions']['日期'])
        
        if 'categories' not in st.session_state:
            st.session_state['categories'] = [
                '餐飲', '交通', '娛樂', '醫療', '教育', 
                '購物', '房租', '水電瓦斯', '旅行', '其他'
            ]
        if 'budget' not in st.session_state:
            st.session_state['budget'] = 0.0

    def add_transaction_sidebar(self):
        st.sidebar.header("新增交易")
        
        with st.sidebar.form(key='add_transaction_form'):
            date = st.date_input("日期", datetime.date.today())
            category = st.selectbox("類別", st.session_state['categories'])
            amount = st.number_input("金額", min_value=0.01, step=0.01)
            transaction_type = st.radio("類型", ('收入', '支出'))
            note = st.text_area("備註", "", height=100)
            submit_transaction = st.form_submit_button(label='新增交易')

        if submit_transaction:
            self._add_transaction(date, category, amount, transaction_type, note)

    def manage_categories_sidebar(self):
        st.sidebar.header("管理類別")
        
        with st.sidebar.form(key='manage_categories_form'):
            new_category = st.text_input("新增類別")
            delete_category = st.selectbox(
                "刪除類別", 
                [''] + st.session_state['categories'],
                index=0
            )
            submit_category = st.form_submit_button(label='更新類別')

        if submit_category:
            self._update_categories(new_category, delete_category)

    def display_transactions(self):
        st.subheader("交易紀錄")
        
        if not st.session_state['transactions'].empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_type = st.multiselect(
                    "篩選類型",
                    ['收入', '支出'],
                    default=['收入', '支出']
                )
            with col2:
                filter_category = st.multiselect(
                    "篩選類別",
                    st.session_state['categories'],
                    default=st.session_state['categories']
                )
            with col3:
                sort_by = st.selectbox(
                    "排序方式",
                    ['日期 (新到舊)', '日期 (舊到新)', '金額 (高到低)', '金額 (低到高)']
                )

            df = st.session_state['transactions']
            df = df[df['類型'].isin(filter_type)]
            df = df[df['類別'].isin(filter_category)]
            
            if sort_by == '日期 (新到舊)':
                df = df.sort_values('日期', ascending=False)
            elif sort_by == '日期 (舊到新)':
                df = df.sort_values('日期', ascending=True)
            elif sort_by == '金額 (高到低)':
                df = df.sort_values('金額', ascending=False)
            else:
                df = df.sort_values('金額', ascending=True)

            st.dataframe(df, use_container_width=True)
        else:
            st.info("目前尚無交易紀錄。")

    def generate_report(self):
        st.subheader("財務報表")
        
        if not st.session_state['transactions'].empty:
            transactions = st.session_state['transactions']
            expenses = transactions[transactions['類型'] == '支出']['金額'].sum()
            incomes = transactions[transactions['類型'] == '收入']['金額'].sum()
            net_balance = incomes - expenses

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("總收入", f"${incomes:,.2f}")
            with col2:
                st.metric("總支出", f"${expenses:,.2f}")
            with col3:
                st.metric("收支結餘", f"${net_balance:,.2f}", 
                         delta=f"${net_balance:,.2f}")

            tab1, tab2 = st.tabs(["支出分析", "收入分析"])
            
            with tab1:
                self._plot_expense_analysis()
            
            with tab2:
                self._plot_income_analysis()
        else:
            st.info("目前無法生成報表，因為尚無交易紀錄。")

    def set_budget(self):
        st.subheader("預算管理")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_budget = st.number_input(
                "設定每月預算",
                min_value=0.0,
                step=100.0,
                value=float(st.session_state['budget'])
            )
            st.session_state['budget'] = new_budget

        if not st.session_state['transactions'].empty:
            current_month = pd.to_datetime(datetime.date.today().replace(day=1))
            month_expenses = st.session_state['transactions'][
                (st.session_state['transactions']['類型'] == '支出') &
                (st.session_state['transactions']['日期'] >= current_month)
            ]['金額'].sum()

            with col2:
                progress = min(month_expenses / new_budget * 100, 100) if new_budget > 0 else 0
                st.progress(progress / 100)
                st.write(f"本月支出: ${month_expenses:,.2f} / ${new_budget:,.2f}")

            if month_expenses > new_budget:
                st.warning(f"⚠️ 注意：您已超出預算 ${month_expenses - new_budget:,.2f}！")
            else:
                st.success(f"✅ 您尚在預算內。剩餘金額: ${new_budget - month_expenses:,.2f}")

    def query_transactions(self):
        st.subheader("交易查詢")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "開始日期",
                datetime.date.today() - datetime.timedelta(days=30)
            )
        with col2:
            end_date = st.date_input("結束日期", datetime.date.today())

        if start_date <= end_date:
            self._show_filtered_transactions(start_date, end_date)
        else:
            st.error("開始日期不能晚於結束日期！")

    def _add_transaction(self, date, category, amount, transaction_type, note):
        new_transaction = pd.DataFrame({
            '日期': [pd.to_datetime(date)],  # Convert to pandas datetime
            '類別': [category],
            '金額': [amount],
            '類型': [transaction_type],
            '備註': [note]
        })
        st.session_state['transactions'] = pd.concat(
            [st.session_state['transactions'], new_transaction],
            ignore_index=True
        )
        st.success("✅ 交易新增成功！")

    def _update_categories(self, new_category: str, delete_category: str):
        if new_category and new_category not in st.session_state['categories']:
            st.session_state['categories'].append(new_category)
            st.success(f"✅ 類別 '{new_category}' 新增成功！")
        
        if delete_category:
            st.session_state['categories'].remove(delete_category)
            st.success(f"✅ 類別 '{delete_category}' 刪除成功！")

    def _plot_expense_analysis(self):
        transactions = st.session_state['transactions']
        expenses = transactions[transactions['類型'] == '支出']
        
        if not expenses.empty:
            # Category pie chart
            fig_pie = px.pie(
                expenses,
                values='金額',
                names='類別',
                title='支出類別分布'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # Time series chart
            daily_expenses = expenses.groupby('日期')['金額'].sum().reset_index()
            fig_line = px.line(
                daily_expenses,
                x='日期',
                y='金額',
                title='每日支出趨勢'
            )
            st.plotly_chart(fig_line, use_container_width=True)

    def _plot_income_analysis(self):
        transactions = st.session_state['transactions']
        incomes = transactions[transactions['類型'] == '收入']
        
        if not incomes.empty:
            # Category pie chart
            fig_pie = px.pie(
                incomes,
                values='金額',
                names='類別',
                title='收入來源分布'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # Time series chart
            daily_incomes = incomes.groupby('日期')['金額'].sum().reset_index()
            fig_line = px.line(
                daily_incomes,
                x='日期',
                y='金額',
                title='每日收入趨勢'
            )
            st.plotly_chart(fig_line, use_container_width=True)

    def _show_filtered_transactions(self, start_date: datetime.date, end_date: datetime.date):
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        
        filtered_transactions = st.session_state['transactions'][
            (st.session_state['transactions']['日期'] >= start_datetime) &
            (st.session_state['transactions']['日期'] <= end_datetime)
        ]

        if not filtered_transactions.empty:
            st.write(f"查詢期間: {start_date} 至 {end_date}")
            
            income = filtered_transactions[
                filtered_transactions['類型'] == '收入'
            ]['金額'].sum()
            expense = filtered_transactions[
                filtered_transactions['類型'] == '支出'
            ]['金額'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("期間收入", f"${income:,.2f}")
            with col2:
                st.metric("期間支出", f"${expense:,.2f}")
            with col3:
                st.metric("期間結餘", f"${income - expense:,.2f}")
            
            st.dataframe(filtered_transactions, use_container_width=True)
        else:
            st.info("此區間內無交易紀錄。")

def main():
    st.set_page_config(
        page_title="個人記帳程式",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("💰 個人記帳程式")
    
    tracker = FinanceTracker()
    
    # Sidebar
    tracker.add_transaction_sidebar()
    tracker.manage_categories_sidebar()
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["交易紀錄", "報表", "預算", "查詢區間"])
    
    with tab1:
        tracker.display_transactions()
    with tab2:
        tracker.generate_report()
    with tab3:
        tracker.set_budget()
    with tab4:
        tracker.query_transactions()

if __name__ == "__main__":
    main()
