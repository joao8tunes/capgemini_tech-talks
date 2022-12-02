#!/usr/bin/env python
# encoding: utf-8

# Capgemini (Brazil) - www.capgemini.com/br-pt
# "People matter, results count"

from fuzzywuzzy.fuzz import \
    ratio, partial_ratio, token_sort_ratio, token_set_ratio, partial_token_sort_ratio, partial_token_set_ratio


def compare_strings(s1: str, s2: str, fuzzy_method: str = "ratio") -> float:
    """
    Compare strings based on fuzzy logic methods.

    Parameters
    ----------
    s1: str
        String.
    s2: str
        String.
    fuzzy_method: str
        Fuzzy method to compare strings.

    Returns
    -------
    similarity: float
        Similarity between strings `s1` and `s2` in range [0,1].

    References
    ----------
    [1] Fuzzy String Matching in Python Tutorial: https://www.datacamp.com/community/tutorials/fuzzy-string-python
    [2] TheFuzz: https://github.com/seatgeek/thefuzz
    """
    supported_fuzzy_methods = \
        ("ratio", "partial_ratio", "token_sort_ratio", "token_set_ratio", "partial_token_sort_ratio",
         "partial_token_set_ratio")

    assert fuzzy_method in supported_fuzzy_methods, \
        f"fuzzy method '{fuzzy_method}' not supported ({', '.join(supported_fuzzy_methods)})."

    strings_similarity = ratio

    if fuzzy_method == 'partial_ratio':
        strings_similarity = partial_ratio
    elif fuzzy_method == 'token_sort_ratio':
        strings_similarity = token_sort_ratio
    elif fuzzy_method == 'token_set_ratio':
        strings_similarity = token_set_ratio
    elif fuzzy_method == 'partial_token_sort_ratio':
        strings_similarity = partial_token_sort_ratio
    elif fuzzy_method == 'partial_token_set_ratio':
        strings_similarity = partial_token_set_ratio

    similarity = strings_similarity(s1, s2) / 100.0

    return similarity


def find_string(string: str, strings_list: [str], fuzzy_method: str = "ratio") -> (str, float):
    best_match, best_similarity = None, 0.0

    for s in strings_list:
        similarity = compare_strings(string, s, fuzzy_method=fuzzy_method)

        if similarity > best_similarity:
            best_match, best_similarity = s, similarity

    return best_match, best_similarity
