import json
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Учет оборудования школы",
    page_icon="🏫",
    layout="wide"
)

st.title("🏫 Дэшборд учета школьного оборудования")
st.markdown("Интерактивная панель мониторинга парка техники.")

# Функция загрузки данных (проверяет локальный файл JSON или облако)
@st.cache_data(ttl=10)
def load_data():
    # Если есть локальный файл от консольной программы — читаем его для теста
    if os.path.exists("inventory_data.json"):
        try:
            with open("inventory_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return pd.DataFrame(data)
        except Exception:
            pass
            
    # Заглушка, если данных нет вообще
    return pd.DataFrame(columns=["category", "name", "inv_number", "status", "room", "responsible"])

df = load_data()

if df.empty:
    st.warning("⚠️ База данных пока пуста. Добавьте оборудование через консольную программу или создайте файл `inventory_data.json`.")
else:
    # KPI Метрики
    total = len(df)
    healthy = sum(df['status'].str.lower().str.contains("исправно", na=False))
    repair = sum(df['status'].str.lower().str.contains("рем", na=False))
    writeoff = sum(df['status'].str.lower().str.contains("спис", na=False))
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего техники", total)
    col2.metric("Исправно", healthy)
    col3.metric("Требует ремонта", repair)
    col4.metric("Списание", writeoff)

    st.divider()

    # Графики
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Техника по категориям")
        if 'category' in df.columns and not df['category'].dropna().empty:
            cat_counts = df['category'].value_counts().reset_index()
            cat_counts.columns = ['category', 'count']
            fig_cat = px.bar(cat_counts, x='category', y='count', template='plotly_white')
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Нет данных по категориям.")
        
    with col_g2:
        st.subheader("🎯 Состояние оборудования")
        if 'status' in df.columns and not df['status'].dropna().empty:
            fig_pie = px.pie(df, names='status', hole=0.4, template='plotly_white')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Нет данных по статусам.")

    st.divider()
    st.subheader("📋 Полный реестр техники")
    st.dataframe(df, use_container_width=True)