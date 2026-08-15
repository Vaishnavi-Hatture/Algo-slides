"""
search-engine.py
Generates a step-by-step trace for a library of algorithms.

The algorithm NAMES, CATEGORIES, and INPUT SHAPES are read from algorithms.csv
so the roster can be edited without touching this file. Each row's "key"
column maps to a Python function of the same name + "_steps" defined below.

Every algorithm returns a list of steps in ONE shared shape, so the front end
can render any of them — and show a plain-English explanation of every
step — with the same card renderer:

{
    "array":      [...]            current state of the array at this step
    "highlights": {index: kind}    kind in: compare | active | swap | pivot |
                                            sorted | eliminated | match
    "pointers":   [{"index": i, "label": "L"}, ...]
    "info":       {"label": value} small badges of running state (optional)
    "message":    "plain-English explanation of what just happened"
    "status":     short pill text shown on the final/important step (optional)
    "complete":   True on the step that finishes the algorithm
}
"""

import csv
import math
import os


def make_step(array, highlights=None, pointers=None, message="", info=None,
              status=None, complete=False):
    return {
        "array": list(array),
        "highlights": highlights or {},
        "pointers": pointers or [],
        "info": info or {},
        "message": message,
        "status": status,
        "complete": complete,
    }


# ---------------------------------------------------------------- searching

def linear_search_steps(arr, target):
    steps = []
    for i, v in enumerate(arr):
        if v == target:
            steps.append(make_step(arr, {i: "match"}, [{"index": i, "label": "i"}],
                f"arr[{i}] = {v} equals the target {target}. Search ends here.",
                status="match found", complete=True))
            return steps
        steps.append(make_step(arr, {i: "compare"}, [{"index": i, "label": "i"}],
            f"arr[{i}] = {v} is not {target}. Move to the next index.",
            info={"checked so far": i + 1}))
    steps.append(make_step(arr, {}, [], f"Reached the end of the array. {target} is not present.",
        status="not found"))
    return steps


def binary_search_steps(arr, target):
    steps = []
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        highlights = {i: "eliminated" for i in list(range(0, low)) + list(range(high + 1, len(arr)))}
        pointers = [{"index": low, "label": "L"}, {"index": mid, "label": "M"}, {"index": high, "label": "R"}]
        if arr[mid] == target:
            highlights[mid] = "match"
            steps.append(make_step(arr, highlights, pointers,
                f"Middle of range [{low}, {high}] is index {mid} = {arr[mid]}. Match found.",
                status="match found", complete=True))
            return steps
        highlights[mid] = "compare"
        if arr[mid] < target:
            steps.append(make_step(arr, highlights, pointers,
                f"arr[{mid}] = {arr[mid]} is less than {target}. Discard the left half — search [{mid + 1}, {high}].",
                info={"range size": high - low + 1}))
            low = mid + 1
        else:
            steps.append(make_step(arr, highlights, pointers,
                f"arr[{mid}] = {arr[mid]} is greater than {target}. Discard the right half — search [{low}, {mid - 1}].",
                info={"range size": high - low + 1}))
            high = mid - 1
    steps.append(make_step(arr, {i: "eliminated" for i in range(len(arr))}, [],
        f"Search range is empty. {target} is not present.", status="not found"))
    return steps


def jump_search_steps(arr, target):
    n = len(arr)
    step_size = max(1, int(math.isqrt(n)))
    steps = []
    skipped = []
    idx = 0
    block_end = min(step_size, n) - 1
    while True:
        block_end = min(idx + step_size, n) - 1
        highlights = {j: "eliminated" for j in skipped}
        highlights[block_end] = "compare"
        steps.append(make_step(arr, highlights, [{"index": block_end, "label": "jump"}],
            f"Check block boundary arr[{block_end}] = {arr[block_end]}.",
            info={"block size": step_size}))
        if arr[block_end] >= target or idx + step_size >= n:
            break
        skipped.extend(range(idx, idx + step_size))
        idx += step_size

    start, end = idx, min(block_end, n - 1)
    for i in range(start, end + 1):
        highlights = {j: "eliminated" for j in skipped}
        if arr[i] == target:
            highlights[i] = "match"
            steps.append(make_step(arr, highlights, [{"index": i, "label": "i"}],
                f"arr[{i}] = {arr[i]} matches the target — found inside the block.",
                status="match found", complete=True))
            return steps
        highlights[i] = "compare"
        steps.append(make_step(arr, highlights, [{"index": i, "label": "i"}],
            f"arr[{i}] = {arr[i]} is not {target}. Scan the next index in this block."))
    steps.append(make_step(arr, {j: "eliminated" for j in skipped}, [],
        f"{target} is not present in the array.", status="not found"))
    return steps


def interpolation_search_steps(arr, target):
    steps = []
    low, high = 0, len(arr) - 1
    while low <= high and target >= arr[low] and target <= arr[high]:
        if arr[high] == arr[low]:
            pos = low
        else:
            pos = low + ((target - arr[low]) * (high - low)) // (arr[high] - arr[low])
        pos = max(low, min(high, pos))
        highlights = {i: "eliminated" for i in list(range(0, low)) + list(range(high + 1, len(arr)))}
        pointers = [{"index": low, "label": "L"}, {"index": pos, "label": "P"}, {"index": high, "label": "R"}]
        if arr[pos] == target:
            highlights[pos] = "match"
            steps.append(make_step(arr, highlights, pointers,
                f"Interpolated position {pos} holds {arr[pos]} — matches the target.",
                status="match found", complete=True))
            return steps
        highlights[pos] = "compare"
        if arr[pos] < target:
            steps.append(make_step(arr, highlights, pointers,
                f"Estimated position {pos} = {arr[pos]} is below {target}. Narrow to [{pos + 1}, {high}].",
                info={"estimate": pos}))
            low = pos + 1
        else:
            steps.append(make_step(arr, highlights, pointers,
                f"Estimated position {pos} = {arr[pos]} is above {target}. Narrow to [{low}, {pos - 1}].",
                info={"estimate": pos}))
            high = pos - 1
    steps.append(make_step(arr, {}, [], f"{target} falls outside the remaining range — not present.",
        status="not found"))
    return steps


def ternary_search_steps(arr, target):
    steps = []
    low, high = 0, len(arr) - 1
    while low <= high:
        third = (high - low) // 3
        mid1, mid2 = low + third, high - third
        highlights = {i: "eliminated" for i in list(range(0, low)) + list(range(high + 1, len(arr)))}
        pointers = [{"index": mid1, "label": "M1"}, {"index": mid2, "label": "M2"}]
        if arr[mid1] == target:
            highlights[mid1] = "match"
            steps.append(make_step(arr, highlights, pointers,
                f"Left third-point arr[{mid1}] = {arr[mid1]} matches the target.",
                status="match found", complete=True))
            return steps
        if arr[mid2] == target:
            highlights[mid2] = "match"
            steps.append(make_step(arr, highlights, pointers,
                f"Right third-point arr[{mid2}] = {arr[mid2]} matches the target.",
                status="match found", complete=True))
            return steps
        highlights[mid1] = "compare"
        highlights[mid2] = "compare"
        if target < arr[mid1]:
            steps.append(make_step(arr, highlights, pointers,
                f"{target} is below arr[{mid1}] = {arr[mid1]}. Keep only the first third: [{low}, {mid1 - 1}]."))
            high = mid1 - 1
        elif target > arr[mid2]:
            steps.append(make_step(arr, highlights, pointers,
                f"{target} is above arr[{mid2}] = {arr[mid2]}. Keep only the last third: [{mid2 + 1}, {high}]."))
            low = mid2 + 1
        else:
            steps.append(make_step(arr, highlights, pointers,
                f"{target} lies between the two third-points. Keep the middle third: [{mid1 + 1}, {mid2 - 1}]."))
            low, high = mid1 + 1, mid2 - 1
    steps.append(make_step(arr, {}, [], f"Search range is empty. {target} is not present.", status="not found"))
    return steps


# ------------------------------------------------------------------ sorting

def bubble_sort_steps(arr):
    arr = list(arr)
    n = len(arr)
    steps = []
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            sorted_tail = {k: "sorted" for k in range(n - i, n)}
            steps.append(make_step(arr, {**sorted_tail, j: "compare", j + 1: "compare"}, [],
                f"Compare arr[{j}] = {arr[j]} and arr[{j + 1}] = {arr[j + 1]}."))
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
                steps.append(make_step(arr, {**sorted_tail, j: "swap", j + 1: "swap"}, [],
                    f"arr[{j}] was bigger — swapped into arr[{j + 1}]."))
        if not swapped:
            break
    steps.append(make_step(arr, {k: "sorted" for k in range(n)}, [],
        "No swaps left to make — the array is fully sorted.", status="array sorted", complete=True))
    return steps


def selection_sort_steps(arr):
    arr = list(arr)
    n = len(arr)
    steps = []
    for i in range(n):
        min_idx = i
        sorted_head = {k: "sorted" for k in range(i)}
        steps.append(make_step(arr, {**sorted_head, i: "active"}, [],
            f"Start pass {i + 1}: assume arr[{i}] = {arr[i]} is the smallest of what's left."))
        for j in range(i + 1, n):
            steps.append(make_step(arr, {**sorted_head, min_idx: "pivot", j: "compare"}, [],
                f"Compare candidate minimum arr[{min_idx}] = {arr[min_idx]} with arr[{j}] = {arr[j]}."))
            if arr[j] < arr[min_idx]:
                min_idx = j
                steps.append(make_step(arr, {**sorted_head, min_idx: "pivot"}, [],
                    f"arr[{j}] = {arr[j]} is smaller — new minimum candidate."))
        if min_idx != i:
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
            steps.append(make_step(arr, {**sorted_head, i: "swap", min_idx: "swap"}, [],
                f"Swap the smallest found, {arr[i]}, into position {i}."))
    steps.append(make_step(arr, {k: "sorted" for k in range(n)}, [],
        "Every position now holds the correct value — the array is sorted.",
        status="array sorted", complete=True))
    return steps


def insertion_sort_steps(arr):
    arr = list(arr)
    n = len(arr)
    steps = []
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        steps.append(make_step(arr, {**{k: "sorted" for k in range(i)}, i: "active"}, [],
            f"Hold arr[{i}] = {key} aside and find where it belongs in the sorted part on its left."))
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            steps.append(make_step(arr, {**{k: "sorted" for k in range(i)}, j: "compare", j + 1: "swap"}, [],
                f"{arr[j]} is bigger than {key} — shift it one place right."))
            j -= 1
        arr[j + 1] = key
        steps.append(make_step(arr, {k: "sorted" for k in range(i + 1)}, [],
            f"Drop {key} into position {j + 1}, where everything to its left is now ≤ it."))
    steps.append(make_step(arr, {k: "sorted" for k in range(n)}, [],
        "Every element has been inserted in order — the array is sorted.",
        status="array sorted", complete=True))
    return steps


def merge_sort_steps(arr):
    arr = list(arr)
    steps = []

    def merge(lo, mid, hi):
        left, right = arr[lo:mid], arr[mid:hi]
        i = j = 0
        k = lo
        while i < len(left) and j < len(right):
            steps.append(make_step(arr, {lo + i: "compare", mid + j: "compare"}, [],
                f"Merging range [{lo}, {hi}): compare {left[i]} and {right[j]}."))
            if left[i] <= right[j]:
                arr[k] = left[i]
                i += 1
            else:
                arr[k] = right[j]
                j += 1
            steps.append(make_step(arr, {k: "swap"}, [], f"Place {arr[k]} into position {k}."))
            k += 1
        while i < len(left):
            arr[k] = left[i]
            steps.append(make_step(arr, {k: "swap"}, [], f"Copy the remaining left value {arr[k]} into position {k}."))
            i += 1
            k += 1
        while j < len(right):
            arr[k] = right[j]
            steps.append(make_step(arr, {k: "swap"}, [], f"Copy the remaining right value {arr[k]} into position {k}."))
            j += 1
            k += 1

    def sort(lo, hi):
        if hi - lo <= 1:
            return
        mid = (lo + hi) // 2
        sort(lo, mid)
        sort(mid, hi)
        merge(lo, mid, hi)

    sort(0, len(arr))
    steps.append(make_step(arr, {k: "sorted" for k in range(len(arr))}, [],
        "All sub-arrays have been merged back in order — the array is sorted.",
        status="array sorted", complete=True))
    return steps


def quick_sort_steps(arr):
    arr = list(arr)
    steps = []

    def partition(lo, hi):
        pivot = arr[hi]
        steps.append(make_step(arr, {hi: "pivot"}, [],
            f"Choose arr[{hi}] = {pivot} as the pivot for range [{lo}, {hi}]."))
        i = lo - 1
        for j in range(lo, hi):
            steps.append(make_step(arr, {hi: "pivot", j: "compare"}, [],
                f"Compare arr[{j}] = {arr[j]} with pivot {pivot}."))
            if arr[j] < pivot:
                i += 1
                if i != j:
                    arr[i], arr[j] = arr[j], arr[i]
                    steps.append(make_step(arr, {hi: "pivot", i: "swap", j: "swap"}, [],
                        f"{arr[i]} is less than the pivot — move it into the lower region."))
        arr[i + 1], arr[hi] = arr[hi], arr[i + 1]
        steps.append(make_step(arr, {i + 1: "sorted"}, [],
            f"Place the pivot {arr[i + 1]} into its final sorted position {i + 1}."))
        return i + 1

    def sort(lo, hi):
        if lo < hi:
            p = partition(lo, hi)
            sort(lo, p - 1)
            sort(p + 1, hi)

    sort(0, len(arr) - 1)
    steps.append(make_step(arr, {k: "sorted" for k in range(len(arr))}, [],
        "Every pivot has settled into its final spot — the array is sorted.",
        status="array sorted", complete=True))
    return steps


def heap_sort_steps(arr):
    arr = list(arr)
    n = len(arr)
    steps = []

    def heapify(size, i):
        largest = i
        l, r = 2 * i + 1, 2 * i + 2
        highlights = {i: "active"}
        if l < size:
            highlights[l] = "compare"
        if r < size:
            highlights[r] = "compare"
        steps.append(make_step(arr, highlights, [], f"Check node {i} = {arr[i]} against its children."))
        if l < size and arr[l] > arr[largest]:
            largest = l
        if r < size and arr[r] > arr[largest]:
            largest = r
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            steps.append(make_step(arr, {i: "swap", largest: "swap"}, [],
                f"Child {largest} was bigger — swap up to keep the max-heap property."))
            heapify(size, largest)

    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)
    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        sorted_tail = {k: "sorted" for k in range(end, n)}
        steps.append(make_step(arr, {**sorted_tail, 0: "swap", end: "swap"}, [],
            f"Move the current max, {arr[end]}, from the top of the heap to position {end}."))
        heapify(end, 0)
    steps.append(make_step(arr, {k: "sorted" for k in range(n)}, [],
        "The heap has been fully drained into place — the array is sorted.",
        status="array sorted", complete=True))
    return steps


def shell_sort_steps(arr):
    arr = list(arr)
    n = len(arr)
    steps = []
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = arr[i]
            j = i
            steps.append(make_step(arr, {i: "active"}, [],
                f"Gap = {gap}: hold arr[{i}] = {temp} and compare it {gap} places back."))
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                steps.append(make_step(arr, {j - gap: "compare", j: "swap"}, [],
                    f"arr[{j - gap}] = {arr[j - gap]} is bigger — shift it forward by the gap."))
                j -= gap
            arr[j] = temp
            steps.append(make_step(arr, {j: "swap"}, [], f"Place {temp} into position {j}."))
        gap //= 2
    steps.append(make_step(arr, {k: "sorted" for k in range(n)}, [],
        "Gap has shrunk to 0 after a final pass — the array is sorted.",
        status="array sorted", complete=True))
    return steps


def cocktail_sort_steps(arr):
    arr = list(arr)
    n = len(arr)
    steps = []
    start, end = 0, n - 1
    swapped = True
    while swapped:
        swapped = False
        for i in range(start, end):
            steps.append(make_step(arr, {i: "compare", i + 1: "compare"}, [],
                f"Forward pass: compare arr[{i}] = {arr[i]} and arr[{i + 1}] = {arr[i + 1]}."))
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                swapped = True
                steps.append(make_step(arr, {i: "swap", i + 1: "swap"}, [], "Out of order — swap."))
        end -= 1
        if not swapped:
            break
        swapped = False
        for i in range(end, start, -1):
            steps.append(make_step(arr, {i: "compare", i - 1: "compare"}, [],
                f"Backward pass: compare arr[{i}] = {arr[i]} and arr[{i - 1}] = {arr[i - 1]}."))
            if arr[i] < arr[i - 1]:
                arr[i], arr[i - 1] = arr[i - 1], arr[i]
                swapped = True
                steps.append(make_step(arr, {i: "swap", i - 1: "swap"}, [], "Out of order — swap."))
        start += 1
    steps.append(make_step(arr, {k: "sorted" for k in range(n)}, [],
        "Forward and backward passes stopped finding swaps — the array is sorted.",
        status="array sorted", complete=True))
    return steps


# ------------------------------------------------------------- array & math

def kadane_steps(arr):
    steps = []
    max_so_far = max_ending_here = arr[0]
    start = best_start = best_end = 0
    steps.append(make_step(arr, {0: "active"}, [],
        f"Start with the subarray containing just arr[0] = {arr[0]}.",
        info={"best sum": max_so_far}))
    for i in range(1, len(arr)):
        window = {k: "sorted" for k in range(best_start, best_end + 1)}
        if max_ending_here + arr[i] < arr[i]:
            max_ending_here = arr[i]
            start = i
            steps.append(make_step(arr, {**window, i: "swap"}, [],
                f"Adding arr[{i}] = {arr[i]} to the running subarray would drag the sum down — "
                f"restart the subarray at index {i} instead.",
                info={"running sum": max_ending_here, "best sum": max_so_far}))
        else:
            max_ending_here += arr[i]
            steps.append(make_step(arr, {**window, i: "compare"}, [],
                f"Extending the running subarray to include arr[{i}] = {arr[i]} still helps — keep going.",
                info={"running sum": max_ending_here, "best sum": max_so_far}))
        if max_ending_here > max_so_far:
            max_so_far = max_ending_here
            best_start, best_end = start, i
            steps.append(make_step(arr, {k: "match" for k in range(best_start, best_end + 1)}, [],
                f"Running sum {max_so_far} beats the previous best — new best subarray is [{best_start}, {best_end}].",
                info={"best sum": max_so_far}))
    steps.append(make_step(arr, {k: "match" for k in range(best_start, best_end + 1)}, [],
        f"The maximum subarray sum is {max_so_far}, from index {best_start} to {best_end}.",
        status="max subarray found", complete=True))
    return steps


def two_sum_steps(arr, target):
    steps = []
    lo, hi = 0, len(arr) - 1
    while lo < hi:
        s = arr[lo] + arr[hi]
        pointers = [{"index": lo, "label": "L"}, {"index": hi, "label": "R"}]
        if s == target:
            steps.append(make_step(arr, {lo: "match", hi: "match"}, pointers,
                f"arr[{lo}] + arr[{hi}] = {arr[lo]} + {arr[hi]} = {target}. Pair found.",
                status="pair found", complete=True))
            return steps
        elif s < target:
            steps.append(make_step(arr, {lo: "compare", hi: "compare"}, pointers,
                f"{arr[lo]} + {arr[hi]} = {s}, too small. Move the left pointer right for a bigger sum.",
                info={"current sum": s}))
            lo += 1
        else:
            steps.append(make_step(arr, {lo: "compare", hi: "compare"}, pointers,
                f"{arr[lo]} + {arr[hi]} = {s}, too big. Move the right pointer left for a smaller sum.",
                info={"current sum": s}))
            hi -= 1
    steps.append(make_step(arr, {}, [], f"Pointers crossed — no pair sums to {target}.", status="not found"))
    return steps


def sieve_steps(n):
    n = max(2, int(n))
    values = list(range(2, n + 1))
    is_prime = [True] * len(values)
    steps = []
    steps.append(make_step(values, {}, [],
        f"List every number from 2 to {n}. Anything left unmarked at the end is prime.",
        info={"limit": n}))
    for i, v in enumerate(values):
        if not is_prime[i]:
            continue
        highlights = {j: ("eliminated" if not is_prime[j] else "sorted") for j in range(i)}
        highlights[i] = "match"
        steps.append(make_step(values, highlights, [],
            f"{v} is still unmarked, so it's prime. Cross out every multiple of {v}."))
        for multiple in range(v * v, n + 1, v):
            idx = multiple - 2
            if idx < len(values):
                is_prime[idx] = False
    final_highlights = {i: ("sorted" if is_prime[i] else "eliminated") for i in range(len(values))}
    primes = [v for v, p in zip(values, is_prime) if p]
    steps.append(make_step(values, final_highlights, [],
        f"Sieve complete. Primes up to {n}: {', '.join(map(str, primes))}.",
        status="sieve complete", complete=True))
    return steps


def reverse_array_steps(arr):
    arr = list(arr)
    steps = []
    lo, hi = 0, len(arr) - 1
    if lo >= hi:
        steps.append(make_step(arr, {k: "sorted" for k in range(len(arr))}, [],
            "Array has 0 or 1 elements — already its own reverse.", status="reversed", complete=True))
        return steps
    while lo < hi:
        pointers = [{"index": lo, "label": "L"}, {"index": hi, "label": "R"}]
        steps.append(make_step(arr, {lo: "compare", hi: "compare"}, pointers,
            f"Swap the ends: arr[{lo}] = {arr[lo]} and arr[{hi}] = {arr[hi]}."))
        arr[lo], arr[hi] = arr[hi], arr[lo]
        steps.append(make_step(arr, {lo: "swap", hi: "swap"}, pointers,
            "Swapped. Move both pointers one step toward the middle."))
        lo += 1
        hi -= 1
    steps.append(make_step(arr, {k: "sorted" for k in range(len(arr))}, [],
        "Pointers met (or crossed) in the middle — the array is fully reversed.",
        status="reversed", complete=True))
    return steps


def find_max_steps(arr):
    steps = []
    best = 0
    steps.append(make_step(arr, {0: "match"}, [], f"Assume arr[0] = {arr[0]} is the maximum so far."))
    for i in range(1, len(arr)):
        steps.append(make_step(arr, {best: "pivot", i: "compare"}, [],
            f"Compare current max arr[{best}] = {arr[best]} with arr[{i}] = {arr[i]}."))
        if arr[i] > arr[best]:
            best = i
            steps.append(make_step(arr, {best: "match"}, [], f"arr[{i}] = {arr[i]} is bigger — new maximum."))
    steps.append(make_step(arr, {best: "match"}, [],
        f"Scanned the whole array. Maximum value is {arr[best]} at index {best}.",
        status="maximum found", complete=True))
    return steps


def find_min_steps(arr):
    steps = []
    best = 0
    steps.append(make_step(arr, {0: "match"}, [], f"Assume arr[0] = {arr[0]} is the minimum so far."))
    for i in range(1, len(arr)):
        steps.append(make_step(arr, {best: "pivot", i: "compare"}, [],
            f"Compare current min arr[{best}] = {arr[best]} with arr[{i}] = {arr[i]}."))
        if arr[i] < arr[best]:
            best = i
            steps.append(make_step(arr, {best: "match"}, [], f"arr[{i}] = {arr[i]} is smaller — new minimum."))
    steps.append(make_step(arr, {best: "match"}, [],
        f"Scanned the whole array. Minimum value is {arr[best]} at index {best}.",
        status="minimum found", complete=True))
    return steps


def dutch_flag_steps(arr, pivot):
    arr = list(arr)
    steps = []
    low, mid, high = 0, 0, len(arr) - 1
    steps.append(make_step(arr, {}, [],
        f"Partition the array into three bands around pivot value {pivot}: less, equal, greater."))
    while mid <= high:
        pointers = [{"index": low, "label": "low"}, {"index": mid, "label": "mid"}, {"index": high, "label": "high"}]
        if arr[mid] < pivot:
            arr[low], arr[mid] = arr[mid], arr[low]
            steps.append(make_step(arr, {low: "swap", mid: "swap"}, pointers,
                f"arr[{mid}] < {pivot} — swap it into the 'less than' band and advance both low and mid."))
            low += 1
            mid += 1
        elif arr[mid] == pivot:
            steps.append(make_step(arr, {mid: "compare"}, pointers,
                f"arr[{mid}] equals the pivot — it's already in the right band, just advance mid."))
            mid += 1
        else:
            arr[mid], arr[high] = arr[high], arr[mid]
            steps.append(make_step(arr, {mid: "swap", high: "swap"}, pointers,
                f"arr[{mid}] > {pivot} — swap it into the 'greater than' band and shrink high."))
            high -= 1
    highlights = {}
    for i in range(len(arr)):
        highlights[i] = "sorted" if arr[i] < pivot else ("match" if arr[i] == pivot else "eliminated")
    steps.append(make_step(arr, highlights, [],
        f"Partitioning complete: everything less than {pivot}, then equal, then greater.",
        status="partitioned", complete=True))
    return steps


CATEGORIES = {
    "searching": "Searching",
    "sorting": "Sorting",
    "array": "Array & Math",
}

# key -> runner function, looked up by the "key" column of algorithms.csv
_RUNNERS = {
    "linear": linear_search_steps,
    "binary": binary_search_steps,
    "jump": jump_search_steps,
    "interpolation": interpolation_search_steps,
    "ternary": ternary_search_steps,
    "bubble": bubble_sort_steps,
    "selection": selection_sort_steps,
    "insertion": insertion_sort_steps,
    "merge": merge_sort_steps,
    "quick": quick_sort_steps,
    "heap": heap_sort_steps,
    "shell": shell_sort_steps,
    "cocktail": cocktail_sort_steps,
    "kadane": kadane_steps,
    "two_sum": two_sum_steps,
    "sieve": sieve_steps,
    "reverse": reverse_array_steps,
    "find_max": find_max_steps,
    "find_min": find_min_steps,
    "dutch_flag": dutch_flag_steps,
}


def _load_algorithms_from_csv():
    """Reads algorithms.csv (name, category, input shape) and wires each
    row up to its runner function so the roster is driven by the CSV."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "algorithms.csv")
    algorithms = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = row["key"].strip()
            runner = _RUNNERS.get(key)
            if runner is None:
                continue  # CSV references a key with no implementation yet
            algorithms[key] = {
                "label": row["label"].strip(),
                "category": row["category"].strip(),
                "input": row["input"].strip(),
                "needs_sorted": row["needs_sorted"].strip().lower() == "true",
                "runner": runner,
            }
    return algorithms


ALGORITHMS = _load_algorithms_from_csv()
