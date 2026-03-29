from process_data import find_range_indices, paginate, sliding_window_sum


def test_sliding_window_basic():
    assert sliding_window_sum([1, 2, 3, 4, 5], 3) == [6, 9, 12]


def test_sliding_window_size_one():
    assert sliding_window_sum([1, 2, 3], 1) == [1, 2, 3]


def test_sliding_window_full():
    assert sliding_window_sum([1, 2, 3], 3) == [6]


def test_sliding_window_empty():
    assert sliding_window_sum([], 3) == []


def test_paginate_first_page():
    assert paginate([1, 2, 3, 4, 5, 6, 7], 3, 1) == [1, 2, 3]


def test_paginate_second_page():
    assert paginate([1, 2, 3, 4, 5, 6, 7], 3, 2) == [4, 5, 6]


def test_paginate_last_page_partial():
    assert paginate([1, 2, 3, 4, 5, 6, 7], 3, 3) == [7]


def test_paginate_beyond_range():
    assert paginate([1, 2, 3], 3, 2) == []


def test_find_range_basic():
    assert find_range_indices([1, 3, 5, 7, 9], 3, 7) == (1, 4)


def test_find_range_single():
    assert find_range_indices([1, 2, 3, 4, 5], 3, 3) == (2, 3)


def test_find_range_all():
    assert find_range_indices([1, 2, 3], 0, 10) == (0, 3)


def test_find_range_empty_input():
    assert find_range_indices([], 1, 5) == (0, 0)
