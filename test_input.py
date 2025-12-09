def find_duplicates(nums):
    duplicates = []
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j and nums[i] == nums[j]:
                if nums[i] not in duplicates:
                    duplicates.append(nums[i])
    return duplicates


def count_frequency(nums):
    freq = {}
    for i in range(len(nums)):
        if nums[i] not in freq:
            freq[nums[i]] = 0
        freq[nums[i]] += 1

    result = []
    for key in freq.keys():
        result.append((key, freq[key]))

    return result


def print_large_values(nums):
    threshold = 10
    for i in range(len(nums)):
        if nums[i] > threshold:
            print(nums[i])
            threshold = 10
