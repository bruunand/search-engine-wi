import sys
from random import randint
from functools import partial
from duplicates.shingles import get_shingles, get_supershingles


def generate_hash_functions(n=64):
    """ Generate n random hash functions """
    functions = []

    for _ in range(84):
        # Each random hash function just uses Python's built-in hash modulo a random value
        functions.append(partial(lambda m, o: hash(o) % m, randint(1, 100000)))

    return functions


def get_min_hashes(hash_functions, shingles):
    min_hashes = list()

    # For each hash function, run it on all the shingles
    # Take the minimum value (minHash) for each hash_function-[shingles] pair
    for hash_function in hash_functions:
        min_hashes.append(min(map(hash_function, shingles)))

    return min_hashes


def jaccard_similarity(a, b):
    """ Generic Jaccard similarity between two sets """
    a = set(a)
    b = set(b)

    return len(a.intersection(b)) / len(a.union(b))


def demonstrate():
    hash_functions = generate_hash_functions(84)

    example_a = get_shingles('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.', 4)
    example_b = get_shingles('Lorem dolor sit amet, consectetur adipiscing elit, sed do tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.', 4)

    min_a = get_min_hashes(hash_functions, example_a)
    min_b = get_min_hashes(hash_functions, example_b)

    # Print min hashes for both examples
    print(get_min_hashes(hash_functions, example_a))
    print(get_min_hashes(hash_functions, example_b))

    # Print Jaccard similarity, both between shingle lists and minhash lists
    print(jaccard_similarity(example_a, example_b))
    print(jaccard_similarity(min_a, min_b))

    # Get supershingles from sketches
    super_a = get_supershingles(min_a)
    super_b = get_supershingles(min_b)

    # Print intersecting supershingles
    print(set(super_a).intersection(set(super_b)))


if __name__ == "__main__":
    demonstrate()
