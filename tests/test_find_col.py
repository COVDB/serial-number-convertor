import pandas as pd

from streamlit_app import find_col


def test_find_col_simple_match():
    df = pd.DataFrame(columns=['Equipment Number', 'Serial'])
    assert find_col(df, ['equipment']) == 'Equipment Number'


def test_find_col_no_match():
    df = pd.DataFrame(columns=['A', 'B'])
    assert find_col(df, ['equipment']) is None


def test_find_col_multiple_keywords():
    df = pd.DataFrame(columns=['SerialNum', 'Customer Reference'])
    assert find_col(df, ['customer reference', 'serial']) == 'Customer Reference'
