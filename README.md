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
`id-tech-talks/src/assets/settings.yml`.



## 3. Usage

Run Streamlit application:

```console
(venv) user@host:~$ streamlit run .\streamlit_app.py
```


\* Windows OS syntax-based commands.
