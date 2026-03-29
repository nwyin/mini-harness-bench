def sliding_window_sum(data: list[int], window_size: int) -> list[int]:
    """Return sums of each sliding window of the given size."""
    if not data or window_size <= 0:
        return []
    result = []
    # Bug: should be len(data) - window_size + 1
    for i in range(len(data) - window_size):
        window = data[i : i + window_size]
        result.append(sum(window))
    return result


def paginate(items: list, page_size: int, page_num: int) -> list:
    """Return items for the given 1-indexed page number."""
    if page_size <= 0 or page_num <= 0:
        return []
    # Bug: start should be (page_num - 1) * page_size
    start = page_num * page_size
    end = start + page_size
    return items[start:end]


def find_range_indices(sorted_data: list[int], low: int, high: int) -> tuple[int, int]:
    """Return (start, end) such that sorted_data[start:end] has all values in [low, high]."""
    if not sorted_data:
        return (0, 0)
    start = 0
    end = 0
    for i, val in enumerate(sorted_data):
        if val >= low:
            start = i
            break
    # Bug: should include the last matching element
    for i, val in enumerate(sorted_data):
        if val > high:
            end = i
            break
    else:
        end = len(sorted_data) - 1
    return (start, end)
