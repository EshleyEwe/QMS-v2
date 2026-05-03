import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar

st.set_page_config(page_title="Delay Tracker", layout="wide")

st.title("📊 Delay & Calendar Tracker")

uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    required_cols = ["Status", "Created Date", "End Date", "Dev Date"]
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
    else:
        for col in required_cols:
            if "Date" in col:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        today = pd.to_datetime(datetime.today().date())

        def get_status(row):
            status = row.get("Status")
            created = row.get("Created Date")
            end = row.get("End Date")
            dev = row.get("Dev Date")

            if status == "Develop":
                if pd.isna(end) and pd.notna(created):
                    if created + pd.Timedelta(days=14) < today:
                        return "Issue"
                    else:
                        return ""

            if status == "Develop" and pd.notna(end):
                if today > end:
                    return "Overdue"

            if status == "Develop" and pd.notna(dev):
                if today > dev:
                    return "Late"

            if status in ["Testing", "Verify"] and pd.notna(dev):
                if dev >= today:
                    return "On Time"

            return "On Track"

        df["Delay Status"] = df.apply(get_status, axis=1)

        def calc_days(row):
            end = row.get("End Date")
            dev = row.get("Dev Date")

            if row["Delay Status"] == "Overdue" and pd.notna(end):
                return (today - end).days

            if row["Delay Status"] == "Late" and pd.notna(dev):
                return (today - dev).days

            if pd.notna(dev):
                return (dev - today).days

            return None

        df["Days"] = df.apply(calc_days, axis=1)

        priority_order = {
            "Overdue": 1,
            "Late": 2,
            "Issue": 3,
            "On Time": 4,
            "On Track": 5,
            "": 6
        }

        df["Priority"] = df["Delay Status"].map(priority_order)
        df = df.sort_values(by=["Priority", "Days"], ascending=[True, False])

        tab1, tab2 = st.tabs(["📊 Dashboard", "📅 Calendar"])

        with tab1:
            st.subheader("📊 Key Metrics")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", len(df))
            col2.metric("Overdue ❌", (df["Delay Status"] == "Overdue").sum())
            col3.metric("Late ⚠️", (df["Delay Status"] == "Late").sum())
            col4.metric("Issue 🔵", (df["Delay Status"] == "Issue").sum())

            col5, col6, col7 = st.columns(3)
            col5.metric("On Time ✅", (df["Delay Status"] == "On Time").sum())
            col6.metric("On Track", (df["Delay Status"] == "On Track").sum())
            col7.metric("Blank", (df["Delay Status"] == "").sum())

            status_filter = st.multiselect(
                "Select Status",
                options=df["Delay Status"].unique(),
                default=df["Delay Status"].unique()
            )

            filtered_df = df[df["Delay Status"].isin(status_filter)]

            def highlight_status(row):
                status = row["Delay Status"]
                if status == "Overdue":
                    return ["background-color: #ff4d4d"] * len(row)
                elif status == "Late":
                    return ["background-color: #ffa64d"] * len(row)
                elif status == "Issue":
                    return ["background-color: #66ccff"] * len(row)
                elif status == "On Time":
                    return ["background-color: #85e085"] * len(row)
                elif status == "":
                    return ["background-color: #f2f2f2"] * len(row)
                else:
                    return [""] * len(row)

            styled_df = filtered_df.style.apply(highlight_status, axis=1)
            st.subheader("📋 Detailed Data")
            st.write(styled_df)

            st.download_button(
                "⬇️ Download Result",
                filtered_df.to_csv(index=False),
                file_name="delay_result.csv",
                mime="text/csv"
            )

        with tab2:
            st.subheader("📅 Calendar View")

            events = []
            for _, row in df.iterrows():
                if pd.notna(row.get("Dev Date")):
                    status = row["Delay Status"]
                    color = {
                        "Overdue": "#ff4d4d",
                        "Late": "#ffa64d",
                        "Issue": "#66ccff",
                        "On Time": "#85e085",
                        "On Track": "#cccccc",
                        "": "#f2f2f2"
                    }.get(status, "#cccccc")

                    events.append({
                        "title": f"{row.get('Status')} | {status}",
                        "start": row["Dev Date"].strftime("%Y-%m-%d"),
                        "color": color
                    })

            calendar(events=events, options={"initialView": "dayGridMonth", "height": 700})
