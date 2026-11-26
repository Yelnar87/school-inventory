import json
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Учет оборудования школ",
    page_icon="🏫",
    layout="wide",
)

st.title("🏫 Дэшборд учета школьного оборудования")
st.markdown("Данные загружаются напрямую из Google Таблицы.")

# Вставьте сюда вашу ссылку на опубликованный CSV из Google Таблиц
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/ВАШ_ID/pub?gid=0&single=true&output=csv"

COLUMN_MAPPING = {
    "id школы": "school_id",
    "id": "school_id",
    "school_id": "school_id",
    "область": "region",
    "region": "region",
    "район": "district",
    "district": "district",
    "населенный пункт": "settlement",
    "населённый пункт": "settlement",
    "settlement": "settlement",
    "форма собственности": "ownership_type",
    "ownership_type": "ownership_type",
    "наименование школы": "school_name",
    "школа": "school_name",
    "school_name": "school_name",
    "контингент учащихся": "student_count",
    "контингент": "student_count",
    "student_count": "student_count",
    "категория": "category",
    "category": "category",
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
}

REQUIRED_COLS = [
    "school_id",
    "region",
    "district",
    "settlement",
    "ownership_type",
    "school_name",
    "student_count",
    "category",
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
    df = df.drop(
        columns=["name", "наименование", "модель", "responsible", "ответственный"],
        errors="ignore",
    )

    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = ""

    # Отбрасываем пустые строки по категории и инвентарному номеру
    df = df[
        (df["category"].str.strip() != "") | (df["inv_number"].str.strip() != "")
    ].copy()
    return df


df = load_from_google_sheets(GOOGLE_SHEET_CSV_URL)

if df.empty:
    st.warning(
        "Не удалось загрузить данные из Google Таблицы. "
        "Проверьте ссылку `GOOGLE_SHEET_CSV_URL`, публикацию листа в формате CSV и наличие записей."
    )
else:
    # Фильтры на боковой панели
    st.sidebar.header("Фильтры")

    regions = sorted([x for x in df["region"].unique() if str(x).strip()])
    districts = sorted([x for x in df["district"].unique() if str(x).strip()])
    settlements = sorted([x for x in df["settlement"].unique() if str(x).strip()])
    ownerships = sorted([x for x in df["ownership_type"].unique() if str(x).strip()])
    schools = sorted([x for x in df["school_name"].unique() if str(x).strip()])
    categories = sorted([x for x in df["category"].unique() if str(x).strip()])
    statuses = sorted([x for x in df["status"].unique() if str(x).strip()])
    years = sorted([x for x in df["year_of_purchase"].unique() if str(x).strip()])

    selected_regions = st.sidebar.multiselect("Область", options=regions, default=regions)
    selected_districts = st.sidebar.multiselect("Район", options=districts, default=districts)
    selected_settlements = st.sidebar.multiselect(
        "Населенный пункт", options=settlements, default=settlements
    )
    selected_ownerships = st.sidebar.multiselect(
        "Форма собственности", options=ownerships, default=ownerships
    )
    selected_schools = st.sidebar.multiselect("Школа", options=schools, default=schools)
    selected_categories = st.sidebar.multiselect(
        "Категория оборудования", options=categories, default=categories
    )
    selected_statuses = st.sidebar.multiselect("Статус", options=statuses, default=statuses)
    selected_years = st.sidebar.multiselect(
        "Год приобретения", options=years, default=years
    )

    filtered_df = df.copy()
    if selected_regions:
        filtered_df = filtered_df[filtered_df["region"].isin(selected_regions)]
    if selected_districts:
        filtered_df = filtered_df[filtered_df["district"].isin(selected_districts)]
    if selected_settlements:
        filtered_df = filtered_df[filtered_df["settlement"].isin(selected_settlements)]
    if selected_ownerships:
        filtered_df = filtered_df[filtered_df["ownership_type"].isin(selected_ownerships)]
    if selected_schools:
        filtered_df = filtered_df[filtered_df["school_name"].isin(selected_schools)]
    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
    if selected_statuses:
        filtered_df = filtered_df[filtered_df["status"].isin(selected_statuses)]
    if selected_years:
        filtered_df = filtered_df[filtered_df["year_of_purchase"].isin(selected_years)]

    # Карточки организации и контингента
    school_ids = [s.strip() for s in filtered_df["school_id"].unique() if str(s).strip()]
    school_names = [s.strip() for s in filtered_df["school_name"].unique() if str(s).strip()]
    ownership_list = [
        s.strip() for s in filtered_df["ownership_type"].unique() if str(s).strip()
    ]
    location_parts = [
        ", ".join(
            [p for p in [row["region"], row["district"], row["settlement"]] if str(p).strip()]
        )
        for _, row in filtered_df.drop_duplicates(
            subset=["school_id", "school_name", "region", "district", "settlement"]
        ).iterrows()
    ]
    location_parts = [p for p in location_parts if p]

    # Суммируем контингент по уникальным школам (school_id + school_name)
    unique_schools_df = filtered_df.copy()
    unique_schools_df["_contingent_num"] = pd.to_numeric(
        unique_schools_df["student_count"].astype(str).str.replace(" ", "", regex=False),
        errors="coerce",
    ).fillna(0)
    contingent_total = int(
        unique_schools_df.groupby(["school_id", "school_name"], dropna=False)["_contingent_num"]
        .max()
        .sum()
    )

    info_col1, info_col2, info_col3 = st.columns([2, 2, 1])
    with info_col1:
        st.info(
            f"**Школа:** {', '.join(school_names) if school_names else 'Не указано'}\n\n"
            f"**ID школы:** {', '.join(school_ids) if school_ids else '—'}"
        )
    with info_col2:
        st.info(
            f"**Локация:** {' | '.join(location_parts[:2]) if location_parts else 'Не указано'}\n\n"
            f"**Форма собственности:** {', '.join(ownership_list) if ownership_list else 'Не указано'}"
        )
    with info_col3:
        st.metric("Контингент учащихся", f"{contingent_total} чел.")

    # Показатели технического состояния
    total = len(filtered_df)
    status_series = filtered_df["status"].str.lower()
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

    # Итоговая таблица без наименования оборудования (name)
    display_columns = [
        "school_id",
        "region",
        "district",
        "settlement",
        "ownership_type",
        "school_name",
        "student_count",
        "category",
        "inv_number",
        "status",
        "room",
        "year_of_purchase",
    ]
    column_labels = {
        "school_id": "ID школы",
        "region": "Область",
        "district": "Район",
        "settlement": "Населенный пункт",
        "ownership_type": "Форма собственности",
        "school_name": "Наименование школы",
        "student_count": "Контингент учащихся",
        "category": "Категория",
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
