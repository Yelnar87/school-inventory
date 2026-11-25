import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Учет оборудования школы — Павлодар",
    page_icon="🏫",
    layout="wide",
)

st.title("🏫 Дэшборд учета школьного оборудования")
st.markdown("Данные загружаются напрямую из Google Таблицы.")

# Вставьте сюда вашу ссылку на опубликованный CSV из Google Таблиц
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR2nE_fxZPQFUOD35nafGfvuEMLjwLz2hxPJ_f4xLecJ_LDKT-J6KZkQRpBcyePmjVKN5yh8g7e_5lP/pub?gid=0&single=true&output=csv"

# Приведение возможных русских/английских названий столбцов к единому виду
COLUMN_MAPPING = {
    "категория": "category",
    "category": "category",
    "наименование": "name",
    "модель": "name",
    "name": "name",
    "инвентарный номер": "inv_number",
    "инв. номер": "inv_number",
    "inv_number": "inv_number",
    "статус": "status",
    "состояние": "status",
    "status": "status",
    "кабинет": "room",
    "room": "room",
    "ответственный": "responsible",
    "responsible": "responsible",
}


@st.cache_data(ttl=15)
def load_from_google_sheets(url: str) -> pd.DataFrame:
    if not url or "ВАШ_ID" in url:
        return pd.DataFrame()

    df = pd.read_csv(url, dtype=str).fillna("")
    df.columns = [str(col).strip().lower() for col in df.columns]
    df = df.rename(columns=COLUMN_MAPPING)

    for col in ["category", "name", "inv_number", "status", "room", "responsible"]:
        if col not in df.columns:
            df[col] = ""

    # Убираем полностью пустые строки
    df = df[df["name"].str.strip() != ""].copy()
    return df


df = load_from_google_sheets(GOOGLE_SHEET_CSV_URL)

if df.empty:
    st.warning(
        "Не удалось загрузить данные из Google Таблицы. "
        "Проверьте, что ссылка в `GOOGLE_SHEET_CSV_URL` вставлена корректно, "
        "таблица опубликована в формате CSV и в ней есть строки с оборудованием."
    )
else:
    total = len(df)
    status_series = df["status"].str.lower()
    healthy = int(status_series.str.contains("исправ", na=False).sum())
    repair = int(status_series.str.contains("рем", na=False).sum())
    writeoff = int(status_series.str.contains("спис", na=False).sum())
    k_isp = (healthy / total * 100) if total > 0 else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Всего единиц", total)
    col2.metric("Исправно", healthy)
    col3.metric("Требуют ремонта", repair)
    col4.metric("Подлежат списанию", writeoff)
    col5.metric("Коэф. исправности", f"{k_isp:.1f}%")

    st.divider()

    st.sidebar.header("Фильтры")
    categories = sorted([c for c in df["category"].unique() if str(c).strip()])
    statuses = sorted([s for s in df["status"].unique() if str(s).strip()])

    selected_categories = st.sidebar.multiselect(
        "Категория оборудования",
        options=categories,
        default=categories,
    )
    selected_statuses = st.sidebar.multiselect(
        "Статус",
        options=statuses,
        default=statuses,
    )

    filtered_df = df.copy()
    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
    if selected_statuses:
        filtered_df = filtered_df[filtered_df["status"].isin(selected_statuses)]

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Распределение по категориям")
        if not filtered_df.empty and filtered_df["category"].str.strip().any():
            cat_counts = (
                filtered_df["category"]
                .value_counts()
                .reset_index()
            )
            cat_counts.columns = ["category", "count"]
            fig_cat = px.bar(
                cat_counts,
                x="category",
                y="count",
                labels={"category": "Категория", "count": "Количество"},
                template="plotly_white",
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Нет данных для графика по категориям.")

    with col_g2:
        st.subheader("Состояние оборудования")
        if not filtered_df.empty and filtered_df["status"].str.strip().any():
            fig_pie = px.pie(
                filtered_df,
                names="status",
                hole=0.4,
                template="plotly_white",
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Нет данных для графика по статусам.")

    st.divider()
    st.subheader("Реестр оборудования из Google Таблицы")
    st.dataframe(filtered_df, use_container_width=True)
