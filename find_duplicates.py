import pickle

from duplicates.minhash import generate_hash_functions, get_min_hashes
from duplicates.shingles import get_shingles, get_supershingles

min_overlap = 7  # At least 7 supershingles must overlap
url_supershingles = dict()


def add_supershingles(url, supershingles):
    for e_url, e_supershingles in url_supershingles.items():
        intersecting = supershingles.intersection(e_supershingles)

        overlap = len(intersecting)
        if overlap >= min_overlap:
            print(f'Overlap of {overlap} between existing {e_url} and {url}')

            return

    url_supershingles[url] = supershingles


if __name__ == "__main__":
    # Generate hash functions to use
    hash_functions = generate_hash_functions(84)

    # Load corpus from file
    url_contents_dict = pickle.load(open('contents.p', 'rb'))

    # For each URL, compute its supershingles
    for url, contents in url_contents_dict.items():
        # Skip URLs lacking enough tokens to create shingles
        split_contents = contents.split()
        if len(split_contents) < 4:
            continue

        shingles = get_shingles(split_contents)
        min_hashes = get_min_hashes(hash_functions, shingles)

        add_supershingles(url, set(get_supershingles(min_hashes)))
