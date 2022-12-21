#!/usr/bin/env python
# encoding: utf-8

# Capgemini (Brazil) - www.capgemini.com/br-pt
# "People matter, results count"

from streamlit.runtime.uploaded_file_manager import UploadedFile
from datetime import datetime
from typing import Union
import streamlit as st
import pandas as pd
import coloredlogs
import logging
import yaml
import sys
import os


LOG_LEVELS = ("NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

LOGGER = logging.getLogger(__name__)


def get_settings() -> dict:
    """
    Import application settings from YAML-based file.

    Returns
    -------
    settings: dict
        Application settings.
    """
    # Loading YAML-based settings file:
    this_dir_path = os.path.abspath(os.path.join(os.path.realpath(__file__), os.pardir))
    settings_filepath = os.path.join(*[this_dir_path, "assets", "settings.yml"])
    settings = read_yaml(settings_filepath)

    return settings


def read_yaml(filepath: str) -> dict:
    """
    Read YAML-based file content.

    Parameters
    ----------
    filepath: str
        YAML-based filepath.

    Returns
    -------
    content: dict
        Content from YAML-based file.
    """
    with open(filepath, mode="rt", encoding="utf-8") as file:
        content = yaml.safe_load(file)

    return content


def load_csv(path: Union[str, UploadedFile], **kwargs) -> [pd.DataFrame]:
    csv_input_settings = get_settings()['system']['csv']['input']
    sep, encoding = csv_input_settings['sep'], csv_input_settings['encoding']
    df_list = []

    if isinstance(path, list):  # Reading files from 'streamlit' UI.
        for file in path:
            if file is not None:
                try:
                    df = pd.read_csv(filepath_or_buffer=file, sep=sep, encoding=encoding, **kwargs)
                    df_list.append(df)
                except Exception as e:
                    logging.error(f"Failed to read CSV file '{file.name}': {e}")
    else:
        abs_path = os.path.abspath(path)

        if os.path.isdir(abs_path):
            for filepath in os.listdir(abs_path):
                abs_filepath = os.path.join(abs_path, filepath)

                if os.path.isfile(abs_filepath):
                    try:
                        df = pd.read_csv(filepath_or_buffer=abs_filepath, sep=sep, encoding=encoding, **kwargs)
                        df_list.append(df)
                    except Exception as e:
                        logging.error(f"Failed to read CSV file '{abs_filepath}': {e}")
        else:
            try:
                df = pd.read_csv(filepath_or_buffer=abs_path, sep=sep, encoding=encoding, **kwargs)
                df_list.append(df)
            except Exception as e:
                logging.error(f"Failed to read CSV file '{abs_path}': {e}")

    return df_list


def save_csv(df: pd.DataFrame, path: str, **kwargs) -> None:
    csv_output_settings = get_settings()['system']['csv']['output']
    sep, encoding = csv_output_settings['sep'], csv_output_settings['encoding']
    abs_path = os.path.abspath(path)

    if os.path.isdir(abs_path):
        os.makedirs(abs_path, exist_ok=True)
        abs_filepath = os.path.join(abs_path, "output.csv")
        df.to_csv(path_or_buf=abs_filepath, sep=sep, encoding=encoding, **kwargs)
    else:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        df.to_csv(path_or_buf=abs_path, sep=sep, encoding=encoding, **kwargs)


@st.cache
def df_to_bytes(df: pd.DataFrame, **kwargs) -> bytes:
    csv_output_settings = get_settings()['system']['csv']['output']
    sep, encoding = csv_output_settings['sep'], csv_output_settings['encoding']

    return df.to_csv(sep=sep, encoding=encoding, index=False, **kwargs).encode(encoding)


def setup_logger(
        name: str,
        log_filepath: str = None,
        mode: str = "a",
        primary_level: str = "DEBUG",
        secondary_level: str = "CRITICAL",
        secondary_modules: [str] = ("azure", "urllib3", "msal")
) -> logging.Logger:
    """
    Define default logger.

    Parameters
    ----------
    name: str
        Module name.
    log_filepath: str
        Log filepath.
    mode: str
        Log file open mode.
    primary_level: str
        Primary log level.
    secondary_level: str
        Secondary log level.
    secondary_modules: [str]
        Secondary modules to filter.

    Returns
    -------
    logger: logging.Logger
        Logger.
    """
    assert primary_level in LOG_LEVELS, f"log level '{primary_level}' not recognized."
    assert secondary_level in LOG_LEVELS, f"log level '{secondary_level}' not recognized."

    # Setting-up the application logging:
    logging_handlers = [logging.StreamHandler(sys.stdout)]

    if log_filepath:
        logging_handlers.append(logging.FileHandler(log_filepath, mode=mode))

    logging.basicConfig(
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=primary_level,
        handlers=logging_handlers
    )

    logger = logging.getLogger(name=name)
    coloredlogs.install(level=primary_level, logger=logger, isatty=True)

    # Suppressing warnings not sent by `logging` module:
    if secondary_level in ("ERROR", "CRITICAL"):
        os.environ["PYTHONWARNINGS"] = "ignore"

    # Filtering secondary logs:
    for module in secondary_modules:
        secondary_logger = logging.getLogger(module)
        secondary_logger.setLevel(secondary_level)

    return logger


def sting_to_time(string: str, format: str = "%H:%M") -> datetime.time:
    dt_time = datetime.strptime(string, format).time()

    return dt_time


def time_to_string(dt_time: datetime.time, format: str = "%H:%M") -> str:
    string = dt_time.strftime(format)

    return string
