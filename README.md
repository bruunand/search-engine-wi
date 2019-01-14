# webcrawler
Multi-threaded webcrawler made as a part of the Web Intelligence course at AAU. Follows (somewhat) the Mercator crawler design.

Group participants:
* Anders Langballe Jakobsen

# Content ranking (cosine similarity)
## Examples
* Querying for AAU results in

        1. https://www.en.aau.dk/contact
        2. https://www.en.aau.dk/about-aau/organisation-management
        3. https://www.en.aau.dk/about-aau/figures-facts
        4. https://www.en.aau.dk/about-aau/international-cooperation
        5. https://www.en.aau.dk/education/study-in-scandinavia
        6. https://www.en.aau.dk/about-aau
        7. https://www.en.aau.dk/
* These are all relatively short documents that contain AAU, so intuitively they have a closer similarity to the query.
However, one might expect that the 7th ranked URL (aau.dk) is ranked highest, which shows the problem with pure content
ranking

## Cut corners
- I compute the vector length for each document at indexing time in order to save time during query time. I don't know
whether this is a standard practice, but computing the vector length at query time was simply to expensive. This is one
of the shortcomings of the inverted index, since I would have to iterate over each term to find out if a document uses
it

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

# Duplicate prevention
- I found that in general, duplicates were found when the sites had language selectors
- I disregard the size of fingerprints. Whereas a 64-bit hashing function would be good for super shingles, and a 48-bit
hashing function good for super shingles, I use the same hashing function base for both 
- Python's hashing functions are re-generated on each run (for security purposes), so in practice I would need a hashing
algorithm which is consistent across runs

## Examples
- Some have anchor hashtags (these have since been normalized, since it only affects the browser)


    Similarity of 100.0% between https://www.eciu.org/ and https://www.eciu.org/#mission
- Some of the detected duplicates are obvious ones (e.g. HTTPS vs HTTP)


    Similarity of 100.0% between http://kundeservice.tv2.dk/ and https://kundeservice.tv2.dk/
    Similarity of 89.28571428571429% between https://apnews.com/ and https://www.apnews.com/
- Some are less obvious (different TLDs)


    Similarity of 100.0% between http://www.youronlinechoices.eu/ and http://www.youronlinechoices.com/
- Some are false positives. In this case, they share a lot of the same website structure and are relatively small
documents


    Similarity of 66.3157894736842% between https://www.search.aau.dk/?locale=da and https://www.its.aau.dk/vejledninger/nyadgangskode/linux/
# Overall thoughts
## Pre-processing
- Even after stemming and removing stopwords, I obviously still get a lot of gibberish terms
- Example pairs: `('�W�', 97), ('�W�', 97), ('�W�', 97), ('�W�', 125), ('�W�', 125)`
- Further investigation revealed that these were sourced from PDF files
  - Obviously, these need special treatment
  - Since then, I only parse a URL if the content-type is text or HTML
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

## Front queue prioritization
- I have not implemented prioritization in front queues. It uses a random system which is really no better than having
one large queue
- Why not? Didn't want to write a heuristic for "important" websites