# Serial Number Convertor

This Streamlit app merges and filters Excel files. It uses a list of equipment numbers to filter the AM LOG input.

## Equipment list file

Equipment numbers are stored in `equipment_list.txt` located in the project root. The file must contain one equipment number per line. Example:

```
000000000001001917
000000000001001808
...
```

`streamlit_app.py` loads this file on startup. Edit `equipment_list.txt` to update the list without modifying the code.

