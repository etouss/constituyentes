from fuzzywuzzy import fuzz

def closest_match(vocabulary, candidate):
    candidate = candidate.lower()
    closest_word = None
    highest_score = -1
    for word in vocabulary:
        score = fuzz.ratio(candidate, word)
        if score > highest_score:
            highest_score = score
            closest_word = word
    return closest_word