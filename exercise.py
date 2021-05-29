# define functiion to accept a sorted array of integers and finds the
# most common number (any, if there are more than one such number)

from collections import Counter

def most_common_number(ints):
    counter = Counter(ints)
    count, common = max((v, k) for k, v in counter.items())
    return common
    
