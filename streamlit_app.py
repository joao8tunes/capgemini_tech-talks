#!/usr/bin/env python
# encoding: utf-8

# Capgemini (Brazil) - www.capgemini.com/br-pt
# "People matter, results count"

import streamlit as st
import logging
import time

from src.utils import setup_logger, load_csv, df_to_bytes
from src import operations


setup_logger(__name__)


def main() -> None:
    st.set_page_config(page_title="♤ Capgemini: I&D Tech Talks", page_icon="♠")

    st.sidebar.write('**INPUT**')

    input_files = st.sidebar.file_uploader(
        "Attendance list files",
        accept_multiple_files=True,
        type=("csv",),
        help="CSV files generated by Microsoft Teams meetings"
    )
    ignore_inactive_users = st.sidebar.checkbox(
        "Ignore inactive users",
        value=True,
        help="Ignore users not present at the time the attendance list was generated"
    )

    users_list = []
    num_vouchers = 2
    ignore_users = []
    allow_duplicates = False
    calculate_overall_uptime = False
    df_list = None
    df = None

    st.sidebar.markdown("""---""")
    st.sidebar.write('**PROCESS**')
    operation_type = st.sidebar.selectbox("Operation type", operations.TYPES)

    if operation_type == operations.ATTENDANCE_LIST:
        calculate_overall_uptime = st.sidebar.checkbox(
            "Calculate overall uptime",
            value=False,
            help="Calculates overall uptime per user (useful for multiple events)"
        )

    if input_files:
        df_list = load_csv(input_files)
        df = operations.get_attendance_list(
            df_list=df_list,
            ignore_inactive_users=ignore_inactive_users,
            calculate_overall_uptime=calculate_overall_uptime
        )

        users_list = operations.extract_users_list(df=df)

    if operation_type == operations.ATTENDANCE_LIST_DRAW_VOUCHER:
        num_vouchers = st.sidebar.slider("Number of vouchers", min_value=1, max_value=10, value=2)
        ignore_users = st.sidebar.multiselect("Ignore users", users_list, [])
        allow_duplicates = st.sidebar.checkbox("Allow duplicates winners", value=False)

    if st.sidebar.button("Run") and input_files:
        logging.debug(f"Executing operation '{operation_type}'...")

        if operation_type == operations.ATTENDANCE_LIST_COUNT:
            count = len(users_list)
            st.markdown(
                f"Following the attendance list count: <mark style='background-color: lightblue'>{count}</mark>",
                unsafe_allow_html=True
            )
        elif operation_type == operations.ATTENDANCE_LIST:
            st.write("Attendance list:")
            st.dataframe(df, use_container_width=True)
            csv = df_to_bytes(df)

            st.download_button(
                label="Download",
                data=csv,
                file_name="attendance_list.csv",
                mime="text/csv",
            )
        elif operation_type == operations.ATTENDANCE_LIST_DRAW_VOUCHER:
            # Displaying progress bar on screen:
            pbar = st.progress(0)

            for percent_complete in range(100):
                time.sleep(0.05)
                pbar.progress(percent_complete + 1)

            pbar.empty()

            # Fetching and displaying the list of winners on the screen:
            df = operations.giveaway_vouchers(
                users_list=users_list,
                number=num_vouchers,
                allow_duplicates=allow_duplicates,
                ignore_users=ignore_users
            )
            st.write("List of winners:")
            st.dataframe(df, use_container_width=True)
            csv = df_to_bytes(df)

            st.download_button(
                label="Download",
                data=csv,
                file_name="vouchers_winners.csv",
                mime="text/csv",
            )


if __name__ == '__main__':
    main()
