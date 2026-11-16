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

# Функция загрузки данных
@st.cache_data(ttl=10)
def load_data():
    # 1. Проверяем, есть ли реальный файл с данными
    if os.path.exists("inventory_data.json"):
        try:
            with open("inventory_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return pd.DataFrame(data)
        except Exception:
            pass
    
    # 2. Если файла нет, используем демонстрационные данные для мгновенного запуска
    sample_data = [
        {"category": "Компьютер", "name": "ПК HP ProDesk 400", "inv_number": "10124501", "status": "исправно", "room": "Каб. 301", "responsible": "Иванов И.И."},
        {"category": "Компьютер", "name": "ПК Lenovo ThinkCentre", "inv_number": "10124502", "status": "требует ремонта", "room": "Каб. 302", "responsible": "Петров В.С."},
        {"category": "Ноутбук", "name": "Lenovo IdeaPad", "inv_number": "10124550", "status": "исправно", "room": "Библиотека", "responsible": "Сидорова М.И."},
        {"category": "Ноутбук", "name": "ASUS ExpertBook", "inv_number": "10124551", "status": "исправно", "room": "Каб. 210", "responsible": "Смирнов А.П."},
        {"category": "Интерактивная доска", "name": "IntelliBoard 75\"", "inv_number": "10124601", "status": "исправно", "room": "Каб. 204", "responsible": "Васильева Е.В."},
        {"category": "Интерактивная доска", "name": "Smart Board", "inv_number": "10124602", "status": "требует ремонта", "room": "Каб. 315", "responsible": "Моргунов П.И."},
        {"category": "Проектор", "name": "Epson EB-X49", "inv_number": "10124701", "status": "списание", "room": "Актовый зал", "responsible": "Козлов Д.П."}
    ]
    return pd.DataFrame(sample_data)

df = load_data()

# Расчет ключевых метрик
total = len(df)
healthy = sum(df['status'].str.lower().str.contains("исправно", na=False))
repair = sum(df['status'].str.lower().str.contains("рем", na=False))
writeoff = sum(df['status'].str.lower().str.contains("спис", na=False))
k_isp = (healthy / total * 100) if total > 0 else 0

# Блок KPI метрик
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Всего техники", total)
col2.metric("Исправно", healthy)
col3.metric("Ремонт", repair)
col4.metric("Списание", writeoff)
col5.metric("Коэф. исправности", f"{k_isp:.1f}%")

st.divider()

# Графики
col_g1, col_g2 = st.columns(2)
with col_g1:
    st.subheader("📊 Техника по категориям")
    cat_counts = df['category'].value_counts().reset_index()
    cat_counts.columns = ['category', 'count']
    fig_cat = px.bar(cat_counts, x='category', y='count', template='plotly_white')
    st.plotly_chart(fig_cat, use_container_width=True)
    
with col_g2:
    st.subheader("🎯 Состояние оборудования")
    fig_pie = px.pie(df, names='status', hole=0.4, template='plotly_white')
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()
st.subheader("📋 Полный реестр техники")
st.dataframe(df, use_container_width=True)
