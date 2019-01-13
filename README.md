# webcrawler
Multi-threaded webcrawler made as a part of the Web Intelligence course at AAU. Follows (somewhat) the Mercator crawler design.

Group participants:
* Anders Langballe Jakobsen

# Boolean query
## Examples
* Casing is ignored


    Enter query:USA
    110 matches
    Enter query:usa
    110 matches
* Stemming means that different words with different meanings produce the same results


    Enter query:democratic
    25 matches
    Enter query:democratization
    25 matches

* Apostrophes are removed from terms


    Enter query:can't
    38 matches
    Enter query:cant
    38 matches

## Cut corners
- In order to optimise boolean queries, we can sequentially process ANDs in order of increasing document frequency for each term
- I have cut a corner here by not processing the terms in that sequence


# Overall thoughts
## Pre-processing
- Even after stemming and removing stopwords, I obviously still get a lot of gibberish terms
- Example pairs: `('�W�', 97), ('�W�', 97), ('�W�', 97), ('�W�', 125), ('�W�', 125)`
- Further investigation revealed that these were sourced from PDF files
  - Obviously, these need special treatment
- It's difficult to filter these our (are they syntactically valid in some language?)
- I've iteratively removed symbols like `@` and `#`. Probably a good idea to find a comprehensive list instead

## Postings list data structure
- Postings lists are stored as Python dictionaries
  - Allows us to store the frequency of the term for each document the term appears in
- Time complexity of intersection and union is `O(n+m)` in the average case

## PageRank
- Initialize, I saved references from hosts to themselves
- I was seeing some highly specific URLs and I was hoping I could get more general, shorter URLs
- It helped, but I still have the problem that a host like Twitter references `help.twitter.com` many times
- I then changed it to extract the TLD (top-level domain) with suffix, which gave much better results
- Still had the problem that sites like `aau.dk` reference their social media a lot. Less of a problem at a larger scale

## Duplicate prevention
- I disregard the size of fingerprints. Whereas a 64-bit hashing function would be good for super shingles, and a 48-bit
hashing function good for super shingles, I use the same hashing function base for both 
- Python's hashing functions are re-generated on each run (for security purposes), so in practice I would need a hashing
algorithm which is consistent across runs

## Front queue prioritization
- I have not implemented prioritization in front queues. It uses a random system which is really no better than having
one large queue
- Why not? Didn't want to write a heuristic for "important" websites