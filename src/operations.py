#!/usr/bin/env python
# encoding: utf-8

# Capgemini (Brazil) - www.capgemini.com/br-pt
# "People matter, results count"

from datetime import datetime
import pandas as pd
import logging
import random
import math

from src.handlers import find_string
from src.utils import get_settings

ATTENDANCE_LIST = "attendance_list"
ATTENDANCE_LIST_COUNT = "attendance_list_count"
ATTENDANCE_LIST_DRAW_VOUCHER = "giveaway_voucher"

TYPES = (
    ATTENDANCE_LIST,
    ATTENDANCE_LIST_COUNT,
    ATTENDANCE_LIST_DRAW_VOUCHER,
)

CSV_HEADER_DEFAULT = ["Full Name", "User Action", "Timestamp"]
TRANSLATIONS = {
    'header': {
        'Full Name': "Full Name",
        'Nome Completo': "Full Name",
        'User Action': "User Action",
        'Atividade': "User Action",
        'Timestamp': "Timestamp",
        'Carimbo de data/hora': "Timestamp"
    },
    'users_actions': {
        'Joined': "Joined",
        'Ingressou': "Joined",
        'Joined before': "Joined before",
        'Entrou antes de': "Joined before",
        'Left': "Left",
        'Saiu': "Left",
    }
}


def translate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    def translate_header_column(string: str) -> str:
        translation = TRANSLATIONS['header'][string]

        return translation

    if not df.columns[0] in ["Full Name", "Nome Completo"]:
        new_header = ["Full Name", "User Action", "Timestamp"]
        df.loc[len(df)] = list(df.columns)
    else:
        new_header = list(map(translate_header_column, list(df.columns)))

    df = df.set_axis(new_header, axis=1)
    df['User Action'] = df['User Action'].map(TRANSLATIONS['users_actions']).fillna(TRANSLATIONS['users_actions'])

    return df


def format_user_name(user_name: str) -> str:
    # TODO: add more languages, since this function only supports English and Portuguese.

    if "," in user_name:
        last_name, name = user_name.split(",")
        formatted_name = name.strip() + " " + last_name.strip()
    else:
        formatted_name = user_name

    return formatted_name


def left_before_event_starts(user_actions: pd.Series, timestamps: pd.Series, start_time: str, end_time: str) -> bool:
    event_date = timestamps.iloc[0].date()
    event_start_time = pd.to_datetime(f"{event_date} {start_time}", infer_datetime_format=True, errors="coerce")
    event_end_time = pd.to_datetime(f"{event_date} {end_time}", infer_datetime_format=True, errors="coerce")

    left_before = True if user_actions.iloc[-1] == "Left" and timestamps.iloc[-1] < event_start_time else False

    return left_before


def coerce_time_slot(action_timestamp: datetime, start_time: str, end_time: str) -> datetime:
    event_date = action_timestamp.date()
    event_start_time = pd.to_datetime(f"{event_date} {start_time}", infer_datetime_format=True, errors="coerce")
    event_end_time = pd.to_datetime(f"{event_date} {end_time}", infer_datetime_format=True, errors="coerce")

    if action_timestamp < event_start_time:
        new_action_timestamp = event_start_time
    elif action_timestamp > event_end_time:
        new_action_timestamp = event_end_time
    else:
        new_action_timestamp = action_timestamp

    return new_action_timestamp


def ignore_time_slot(action_timestamp: datetime, start_time: str, end_time: str) -> datetime:
    event_date = action_timestamp.date()
    event_start_time = pd.to_datetime(f"{event_date} {start_time}", infer_datetime_format=True, errors="coerce")
    event_end_time = pd.to_datetime(f"{event_date} {end_time}", infer_datetime_format=True, errors="coerce")

    new_action_timestamp = action_timestamp if event_start_time <= action_timestamp <= event_end_time else None

    return new_action_timestamp


def get_attendance_list(
        df_list: [pd.DataFrame],
        ignore_inactive_users: bool = True,
        calculate_overall_uptime: bool = False
) -> pd.DataFrame:
    logging.info("Fetching the attendance list...")
    settings = get_settings()
    system_settings = settings['system']
    format_names = system_settings['format_user_names']
    event_settings = settings['spreadsheets']['event']
    check_user_name = event_settings['check_user_name']
    check_user_name_similarity = event_settings['check_user_name_similarity']
    check_time_slot = event_settings['check_time_slot']
    event_start_time = event_settings['start_time']
    event_end_time = event_settings['end_time']
    attendance_list_settings = settings['spreadsheets']['attendance_list']
    col_name = attendance_list_settings['user_name']
    col_action = attendance_list_settings['user_action']
    col_timestamp = attendance_list_settings['timestamp']
    col_date = attendance_list_settings['date']
    col_duration = attendance_list_settings['duration']
    col_attendance = attendance_list_settings['attendance']
    attendance_list = []

    # Iterating over list of dataframes:
    for df in df_list:
        df = translate_dataframe(df)
        df[col_name] = df[col_name].str.upper()
        df[col_timestamp] = pd.to_datetime(df[col_timestamp], infer_datetime_format=True, errors="coerce")
        df = df.dropna(how="any").sort_values(by=[col_action])
        users = df[col_name].unique().tolist()
        active_users = []

        # Ignoring users who left the meeting before it ended:
        if ignore_inactive_users:
            for user in users:
                user_actions = df[df[col_name] == user][col_action].tolist()
                last_user_action = user_actions[-1]

                if last_user_action.startswith("Joined"):
                    active_users.append(user)
        else:
            active_users = users

        df = df[df[col_name].isin(active_users)]
        attendance_list.append(df[[col_name, col_action, col_timestamp]])

    df = pd.concat(attendance_list)
    df[col_date] = df[col_timestamp].dt.date
    df[col_duration] = 0

    if format_names:
        df[col_name] = df[col_name].apply(format_user_name)

    all_users = df[col_name].unique().tolist()

    # Validating usernames, to ensure that users who sign in through different Teams accounts that possibly have
    # different names, are identified as being the same user:
    if check_user_name:
        all_users = sorted(all_users, key=len, reverse=True)
        user_remap = {all_users[0]: all_users[0]}

        for user in all_users[1:]:
            names_list = list(user_remap.keys())
            match, similarity = find_string(user, names_list, fuzzy_method="partial_token_sort_ratio")
            user_remap[user] = match if similarity >= check_user_name_similarity else user

        df[col_name] = df[col_name].map(user_remap)
        all_users = df[col_name].unique().tolist()

    # Validating users actions regarding the events' time slot. If the user left before the event started,
    # ignore their actions; otherwise, adjust the input/output timestamps to the event's previous defined time slot:
    if check_time_slot:
        dates = df[col_date].unique().tolist()

        for date in dates:
            df_date = df[df[col_date] == date]
            users = df_date[col_name].unique().tolist()

            for user in users:
                df_user = df_date[df_date[col_name] == user]
                user_actions, timestamps = df_user[col_action], df_user[col_timestamp]

                user_did_not_participate = left_before_event_starts(
                    user_actions=user_actions,
                    timestamps=timestamps,
                    start_time=event_start_time,
                    end_time=event_end_time
                )

                # Checking if the last user action is in the event time slot, otherwise, ignore it:
                if user_did_not_participate:
                    df.loc[(df[col_date] == date) & (df[col_name] == user), col_timestamp].apply(
                        lambda t: ignore_time_slot(t, event_start_time, event_end_time)
                    )
                else:
                    df.loc[(df[col_date] == date) & (df[col_name] == user), col_timestamp].apply(
                        lambda t: coerce_time_slot(t, event_start_time, event_end_time)
                    )

    # Dropping duplicate rows, keeping the first occurrence:
    df = df.dropna(how="any").drop_duplicates(subset=[col_name, col_timestamp], keep="first")

    for user in all_users:
        df_user = df[df[col_name] == user]
        user_dates = df_user[col_date].unique().tolist()

        for date in user_dates:
            start_time = pd.to_datetime(f"{date} {event_start_time}", infer_datetime_format=True, errors="coerce")
            end_time = pd.to_datetime(f"{date} {event_end_time}", infer_datetime_format=True, errors="coerce")
            df_user_actions = df_user[df_user[col_date] == date]

            duration_sec = 0
            last_action, last_action_timestamp = None, None
            cur_action, cur_action_timestamp = None, None

            for i, row in df_user_actions.iterrows():
                cur_action, cur_action_timestamp = row[col_action], row[col_timestamp]

                if not last_action:
                    last_action, last_action_timestamp = cur_action, cur_action_timestamp
                    continue

                if cur_action == "Left":
                    duration_sec += (cur_action_timestamp - last_action_timestamp).seconds
                    last_action = None

            if last_action:
                duration_sec += (cur_action_timestamp - last_action_timestamp).seconds

            if cur_action != "Left":
                remaining_duration = (end_time - cur_action_timestamp).seconds
                duration_sec += remaining_duration

            duration = duration_sec / 60
            df.loc[(df[col_name] == user) & (df[col_date] == date), col_duration] = math.ceil(duration)

    if calculate_overall_uptime:
        for user in all_users:
            df.loc[(df[col_name] == user), col_duration] = math.ceil(df[df[col_name] == user][col_duration].sum())
            df.loc[(df[col_name] == user), col_attendance] = df[df[col_name] == user][col_duration].count()

        df = df[[col_name, col_attendance, col_duration]].drop_duplicates()
        df[col_attendance] = df[col_attendance].astype(df[col_duration].iloc[0].dtype)
        df = df.sort_values(by=[col_attendance, col_duration], ascending=False).reset_index(drop=True)
    else:
        df = df[[col_name, col_date, col_duration]].drop_duplicates()
        df = df.sort_values(by=[col_date, col_duration], ascending=False).reset_index(drop=True)

    return df


def extract_users_list(df: pd.DataFrame, sort_names: bool = True) -> [str]:
    settings = get_settings()
    attendance_list_settings = settings['spreadsheets']['attendance_list']
    name = attendance_list_settings['user_name']
    users_list = sorted(df[name].unique().tolist()) if sort_names else df[name].unique().tolist()

    return users_list


def giveaway_vouchers(
        users_list: [str],
        number: int = 2,
        allow_duplicates: bool = False,
        ignore_users: [str] = None
) -> pd.DataFrame:
    assert 1 <= number

    logging.info("Giving away vouchers to attendance list users...")
    settings = get_settings()
    attendance_list_settings = settings['spreadsheets']['attendance_list']
    name = attendance_list_settings['user_name']

    if ignore_users:
        users_list = [user for user in users_list if user not in ignore_users]

    attendance_list_count = len(users_list)
    lucky_users = []

    if not allow_duplicates and not number <= attendance_list_count:
        logging.warning(
            f"The number of winners cannot be greater than the size of the attendance list "
            f"(number <= {attendance_list_count})."
        )

    for _ in range(number):
        selected_user = random.choice(users_list)
        lucky_users.append(selected_user)

        if not allow_duplicates:
            users_list.remove(selected_user)

            if not users_list:
                break

    df = pd.DataFrame(lucky_users, columns=[name])

    return df
