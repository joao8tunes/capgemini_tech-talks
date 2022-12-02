# Capgemini: I&D Tech Talks

TODO

## 1. Requirements

Following the minimum system requirements to execute the scripts:

- **Processor:** 2 Cores, 32-Bit, 1.4 GHz
- **Memory:** 1 GB RAM
- **Storage:** 50 MB free space
- **OS:** Linux, Windows, macOS

Before using the auditing tool, you must install its requirements by executing the following commands\*:

```console
user@host:~$ cd id-tech-talks\
user@host:~$ python -m venv venv
user@host:~$ venv\Scripts\activate
(venv) user@host:~$ pip install -U pip setuptools wheel
(venv) user@host:~$ pip install -r requirements.txt
```


## 2. Settings

The script configuration is based on the YAML language and can be changed by editing a single text file: 
`id-tech-talks/src/assets/settings.yml`. Following are the main sections from the config file.

Event settings `spreadsheets -> event`:

- `start_time`: Event start time (`HH:mm`);
- `end_time`: Event end time (`HH:mm`);
- `check_time_slot`: Validation of users actions regarding the events' time slot. If the user left before the event started, ignore their actions; otherwise, adjust the input/output timestamps to the event's previous defined time slot; 
- `check_user_name`: Validation of usernames, to ensure that users who sign in through different Teams accounts that possibly have different names, are identified as being the same user;
- `check_user_name_similarity`: Minimum similarity threshold between strings to consider that two usernames are the same.


## 3. Usage

Run Streamlit application:

```console
(venv) user@host:~$ streamlit run .\streamlit_app.py
```


\* Windows OS syntax-based commands.
