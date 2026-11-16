import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Учет оборудования школы", layout="wide")

st.title("🏫 Дэшборд учета школьного оборудования (Онлайн)")
st.markdown("Данные синхронизируются в реальном времени из облачной базы данных.")

# Подключение к Google Таблице через встроенный механизм Streamlit
@st.cache_data(ttl=60)
def load_data():
    # Streamlit может напрямую читать публичные Google Таблицы или защищенные через secrets
    url = "ВАША_ССЫЛКА_НА_GOOGLE_ТАБЛИЦУ_ИЛИ_ПОДКЛЮЧЕНИЕ"
    # Для примера используем локальный или облачный источник
    return pd.DataFrame() # Здесь настраивается подключение к вашему источнику

# Упрощенный вариант загрузки для теста:
try:
    # Загружаем данные из Google Таблицы
    df = st.connection("gsheets", type="gsheets").read(worksheet="Inventory")
except Exception as e:
    st.error(f"Ошибка подключения к базе: {e}")
    df = pd.DataFrame(columns=["category", "name", "inv_number", "status", "room", "responsible"])

if not df.empty:
    # Метрики KPI
    total = len(df)
    healthy = sum(df['status'].str.lower().str.contains("исправно", na=False))
    repair = sum(df['status'].str.lower().str.contains("рем", na=False))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Всего техники", total)
    col2.metric("Исправно", healthy)
    col3.metric("Требует ремонта", repair)

    st.divider()

    # Графики
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Техника по категориям")
        fig_cat = px.bar(df['category'].value_counts().reset_index(), x='category', y='count')
        st.plotly_chart(fig_cat, use_container_width=True)
        
    with col_g2:
        st.subheader("Состояние оборудования")
        fig_pie = px.pie(df, names='status')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Полный реестр")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Таблица пока пуста. Добавьте данные в Google Таблицу.")