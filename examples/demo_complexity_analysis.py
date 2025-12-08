"""Demo: Code Complexity Analysis

Demonstrates the Big-O complexity analyzer on various code patterns.
Similar to LeetCode's complexity analysis feature.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from app.workflows.code_review import run_code_review


# Example 1: Simple linear search
LINEAR_SEARCH = """
def find_max(numbers):
    '''Find the maximum number in a list'''
    if not numbers:
        return None

    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val
"""

# Example 2: Binary search
BINARY_SEARCH = """
def binary_search(arr, target):
    '''Binary search implementation'''
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1
"""

# Example 3: Two pointers - palindrome check
PALINDROME_CHECK = """
def isPalindrome(s: str) -> bool:
    '''Check if string is a palindrome, ignoring non-alphanumeric'''
    cleaned = ""

    for ch in s:
        if ch.isalnum():
            cleaned += ch.lower()

    return cleaned == cleaned[::-1]
"""

# Example 4: Nested loops - bubble sort
BUBBLE_SORT = """
def bubble_sort(arr):
    '''Sort array using bubble sort'''
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""

# Example 5: Hash map - two sum
TWO_SUM = """
def two_sum(nums, target):
    '''Find two numbers that add up to target'''
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""


async def analyze_code(code: str, title: str):
    """Analyze code and print results"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")
    print("\nCode:")
    print(code)

    # Run code review
    result = await run_code_review(code, use_llm=False)

    # Extract complexity analysis
    if "complexity_analysis" in result.data:
        analysis = result.data["complexity_analysis"]

        for func_name, details in analysis.items():
            print(f"\nFunction: {func_name}")
            print(f"  Time Complexity:  {details['time_complexity']}")
            print(f"  Space Complexity: {details['space_complexity']}")
            print(f"  Explanation: {details['explanation']}")

    # Show quality metrics
    print(f"\nQuality Score: {result.data.get('quality_score', 'N/A')}/100")
    print(f"Issues Found: {result.data.get('issue_count', 0)}")

    if result.data.get("suggestions"):
        print("\nSuggestions:")
        for i, suggestion in enumerate(result.data["suggestions"][:3], 1):
            print(f"  {i}. {suggestion}")


async def main():
    """Run complexity analysis demo"""
    print("=" * 70)
    print("CODE COMPLEXITY ANALYZER DEMO")
    print("Analyzing various algorithmic patterns")
    print("=" * 70)

    # Analyze each example
    await analyze_code(LINEAR_SEARCH, "Example 1: Linear Search (O(n))")
    await analyze_code(BINARY_SEARCH, "Example 2: Binary Search (O(log n))")
    await analyze_code(PALINDROME_CHECK, "Example 3: Palindrome Check")
    await analyze_code(BUBBLE_SORT, "Example 4: Bubble Sort (O(n²))")
    await analyze_code(TWO_SUM, "Example 5: Two Sum with Hash Map")

    print(f"\n{'='*70}")
    print("Analysis complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
