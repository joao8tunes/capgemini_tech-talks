#!/usr/bin/env python
# encoding: utf-8

# Capgemini (Brazil) - www.capgemini.com/br-pt
# "People matter, results count"

import pandas as pd
import logging
import random

from src.utils import get_settings

ATTENDANCE_LIST = "attendance_list"
ATTENDANCE_LIST_COUNT = "attendance_list_count"
ATTENDANCE_LIST_REPORT = "attendance_list_report"
ATTENDANCE_LIST_DRAW_VOUCHER = "giveaway_voucher"

TYPES = (
    ATTENDANCE_LIST,
    ATTENDANCE_LIST_COUNT,
    ATTENDANCE_LIST_DRAW_VOUCHER,
    # ATTENDANCE_LIST_REPORT,
)

# TODO: fix Streamlit duplicate log bug.


def format_user_name(users_list: [str]) -> [str]:
    formatted_users_list = []

    for name in users_list:
        last_name, name = name.split(",")
        formatted_name = name.strip() + " " + last_name.strip()
        formatted_users_list.append(formatted_name)

    return formatted_users_list


def get_attendance_list(df_list: [pd.DataFrame], ignore_inactive_users: bool = True) -> pd.DataFrame:
    logging.info("Fetching the attendance list...")
    settings = get_settings()
    system_settings = settings['system']
    format_names = system_settings['format_user_names']
    attendance_list_settings = settings['spreadsheets']['attendance_list']
    name, action = attendance_list_settings['user_name'], attendance_list_settings['user_action']
    attendance_list = []

    # Iterating over list of dataframes:
    for df in df_list:
        users = df[name].drop_duplicates().tolist()

        # Ignoring users who left the meeting before it ended:
        if ignore_inactive_users:
            active_users = []

            for user in users:
                user_actions = df[df[name] == user][action].tolist()
                last_user_action = user_actions[-1]

                if last_user_action == "Joined":
                    active_users.append(user)

            attendance_list = active_users
        else:
            attendance_list.extend(users)

    # Removing duplicates from users list:
    attendance_list = list(dict.fromkeys(attendance_list))

    if format_names:
        attendance_list = format_user_name(attendance_list)

    attendance_list = sorted(attendance_list)
    df = pd.DataFrame(attendance_list, columns=[name])

    return df


def get_attendance_list_count(df_list: [pd.DataFrame], ignore_inactive_users: bool = True) -> int:
    logging.info("Fetching the attendance list count...")
    df = get_attendance_list(df_list=df_list, ignore_inactive_users=ignore_inactive_users)
    count = df.shape[0]

    return count


def giveaway_vouchers(
        df_list: [pd.DataFrame],
        number: int = 2,
        allow_duplicates: bool = False,
        ignore_inactive_users: bool = True
) -> pd.DataFrame:
    assert 1 <= number

    logging.info("Giving away vouchers to attendance list users...")
    settings = get_settings()
    attendance_list_settings = settings['spreadsheets']['attendance_list']
    name = attendance_list_settings['user_name']

    attendance_list = get_attendance_list(df_list=df_list, ignore_inactive_users=ignore_inactive_users)[name].tolist()
    attendance_list_count = len(attendance_list)
    lucky_users = []

    if not allow_duplicates and not number <= len(attendance_list):
        logging.warning(
            f"The number of winners cannot be greater than the size of the attendance list "
            f"(number <= {attendance_list_count})."
        )

    for _ in range(number):
        selected_user = random.choice(attendance_list)
        lucky_users.append(selected_user)

        if not allow_duplicates:
            attendance_list.remove(selected_user)

            if not attendance_list:
                break

    df = pd.DataFrame(lucky_users, columns=[name])

    return df
