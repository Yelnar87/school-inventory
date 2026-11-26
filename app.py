import json
import os
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
    "год приобретения": "year_of_purchase",
    "год приобретение": "year_of_purchase",
    "год": "year_of_purchase",
    "year_of_purchase": "year_of_purchase",
    "наименование школы": "school_name",
    "школа": "school_name",
    "school_name": "school_name",
    "контингент учащихся": "student_count",
    "контингент": "student_count",
    "student_count": "student_count",
}

REQUIRED_COLS = [
    "school_name",
    "student_count",
    "category",
    "name",
    "inv_number",
    "status",
    "room",
    "year_of_purchase",
]


@st.cache_data(ttl=15)
def load_from_google_sheets(url: str) -> pd.DataFrame:
    if not url or "ВАШ_ID" in url:
        return pd.DataFrame()

    df = pd.read_csv(url, dtype=str).fillna("")
    df.columns = [str(col).strip().lower() for col in df.columns]
    df = df.rename(columns=COLUMN_MAPPING)
    df = df.drop(columns=["responsible", "ответственный"], errors="ignore")

    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = ""

    # Убираем пустые строки по наименованию техники
    df = df[df["name"].str.strip() != ""].copy()
    return df


df = load_from_google_sheets(GOOGLE_SHEET_CSV_URL)

if df.empty:
    st.warning(
        "Не удалось загрузить данные из Google Таблицы. "
        "Проверьте ссылку `GOOGLE_SHEET_CSV_URL`, публикацию листа в формате CSV и наличие записей."
    )
else:
    # Отдельные сведения об организации и контингенте
    school_names = [s.strip() for s in df["school_name"].unique() if str(s).strip()]
    school_title = ", ".join(school_names) if school_names else "Не указано"

    contingent_series = pd.to_numeric(
        df["student_count"].astype(str).str.replace(" ", "", regex=False),
        errors="coerce",
    ).dropna()
    contingent_total = int(contingent_series.max()) if not contingent_series.empty else 0

    info_col1, info_col2 = st.columns([2, 1])
    with info_col1:
        st.info(f"**Наименование школы:** {school_title}")
    with info_col2:
        st.metric("Контингент учащихся", f"{contingent_total} чел.")

    # Показатели технического состояния
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

    # Фильтры на боковой панели
    st.sidebar.header("Фильтры")
    categories = sorted([c for c in df["category"].unique() if str(c).strip()])
    statuses = sorted([s for s in df["status"].unique() if str(s).strip()])
    years = sorted([y for y in df["year_of_purchase"].unique() if str(y).strip()])

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
    selected_years = st.sidebar.multiselect(
        "Год приобретения",
        options=years,
        default=years,
    )

    filtered_df = df.copy()
    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
    if selected_statuses:
        filtered_df = filtered_df[filtered_df["status"].isin(selected_statuses)]
    if selected_years:
        filtered_df = filtered_df[filtered_df["year_of_purchase"].isin(selected_years)]

    # Графики
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Распределение по категориям")
        if not filtered_df.empty and filtered_df["category"].str.strip().any():
            cat_counts = filtered_df["category"].value_counts().reset_index()
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
        st.subheader("Распределение по году приобретения")
        if not filtered_df.empty and filtered_df["year_of_purchase"].str.strip().any():
            year_counts = (
                filtered_df["year_of_purchase"]
                .value_counts()
                .reset_index()
                .sort_values("year_of_purchase")
            )
            year_counts.columns = ["year_of_purchase", "count"]
            fig_year = px.bar(
                year_counts,
                x="year_of_purchase",
                y="count",
                labels={"year_of_purchase": "Год приобретения", "count": "Количество"},
                template="plotly_white",
            )
            st.plotly_chart(fig_year, use_container_width=True)
        else:
            st.info("Нет данных для графика по годам приобретения.")

    st.divider()

    # Таблица без поля ответственного
    display_columns = [
        "category",
        "name",
        "inv_number",
        "status",
        "room",
        "year_of_purchase",
    ]
    column_labels = {
        "category": "Категория",
        "name": "Наименование",
        "inv_number": "Инвентарный номер",
        "status": "Статус",
        "room": "Кабинет",
        "year_of_purchase": "Год приобретения",
    }

    st.subheader("Реестр оборудования")
    st.dataframe(
        filtered_df[display_columns].rename(columns=column_labels),
        use_container_width=True,
        hide_index=True,
    )
