"""
Random word generation based on a provided text file.

Implements N-gram markov chains to mimic english phonetics.
"""
import unicodedata
import re
import random
import logging

UNICODE_FIXES = str.maketrans({
    '\u2018': "'",  # LEFT SINGLE QUOTATION MARK
    '\u2019': "'",  # RIGHT SINGLE QUOTATION MARK
})

INITIATOR = '#'
TERMINATOR = '$'
CONTEXT_SIZE = 2

def parse_words(io_manager):
    """
    Fetches and parses the selected book into a list of unique words.

    Normalizes unicode into NFKD so that diacritics are preserved.
    Apostrophes are standardized and preserved, as are compound word hyphenations.
    Punctuation and extraneous special characters are properly stripped.

    Args:
        io_manager: The IOManager currently in use
    
    Returns:
        list: The unique words in the book, properly encoded
    """
    try:
        # Load the book and verify
        text = io_manager.load_book()
        if text is None:
            logging.warning("No stored book found")
            return None
        
        logging.info("Normalizing and fixing Unicode encoding")
        # Step 1: Normalize and fix Unicode
        text = unicodedata.normalize('NFKD', text)
        text = text.lower()  # Lowers certain unicode fixes
        text = text.translate(UNICODE_FIXES)
        text = re.sub(r'-{2,}', ' ', text)   # Two or more hyphens

        logging.info("Stripping undesired special characters")
        # Step 2: Strip special characters
        result = []
        for char in text:
            category = unicodedata.category(char)
            if (category.startswith('L') or # Letters (all types)
                category == 'Mn' or         # Combining marks
                char in "'-"):              # Desired special chars
                result.append(char)
            else:
                result.append(' ')
        
        text = ''.join(result)

        logging.info("Tokenizing text and collapsing duplicates")
        # Step 3: Split words, discard short ones, count frequency
        rawlist = text.split()
        wordlist = []
        for word in rawlist:
            word = word.strip('-')
            if len(word) > CONTEXT_SIZE:
                if word not in wordlist:
                    wordlist.append(word)

        return wordlist
    
    except Exception as e:
        print(f"Failed to parse selected book: {e}")
        return None


def build_model(wordlist):
    """
    Builds a dictionary of letter probabilities based on the unique words in the text.

    Each words is made to start with a special character and end with a different one.
    Weights are determined for each character given the previous N letters.

    Returns:
        dict: The letter probability weights for all present letter combinations
    """
    model = {}

    logging.info("Buliding Markov chain model from text")
    for word in wordlist:
        # Start and end word with special characters for parsing
        word = INITIATOR + word + TERMINATOR
        # For each character in the word following the initiator
        for i in range(1, len(word)):
            # Get the context and current letter
            context = word[:i][-CONTEXT_SIZE:]
            letter = word[i]
            # Make sure the requisite dictionary entries exist
            if context not in model.keys():
                model[context] = {}
            if letter not in model[context].keys():
                model[context][letter] = 0
            # Increment the appropriate counter
            model[context][letter] += 1
    
    return model


def length_distribution(wordlist):
    """
    Calculates terminator probability factors based on the word length distribution.

    Counts word lengths, then does a total normalization such that the the total is one.
    Takes the square root of the distribution to flatten the curve.
    Finally, calculates the cumulative distribution so a terminator gets more likely as the word gets longer.

    Args:
        wordlist: List of unique words in the text
    """
    distribution = {}

    logging.info("Calculating word length distribution from text")
    for word in wordlist:
        length = len(word)
        if length not in distribution.keys():
            distribution[length] = 0
        distribution[length] += 1
    
    distribution = dict(sorted(distribution.items(), key=lambda item: item[0]))

    cumulative = [0]

    for i in range(1, max(distribution.keys()) + 1):
        value = cumulative[-1]
        if i in distribution.keys():
            value += (distribution[i] / sum(distribution.values())) ** 0.5
        cumulative.append(value)
    
    logging.debug(f"Flattened, normalized, cumulative word length distrbution:\n{cumulative}")

    return cumulative


def generate_word(model, distribution):
    """
    Uses a Markov chain model to generate a Jabberwocky style gibberish word.
    
    Weights terminator probablility based on the provided distribution.

    Args:
        model: The dict markov chain model with letter probabilities
        distribution: The terminator probability factors

    Returns:
        str: The generated gibberish word
    """
    word = INITIATOR

    while word[-1] != TERMINATOR:
        context = word[-CONTEXT_SIZE:]
        weights = model[context]
        if TERMINATOR in weights.keys():
            weights = weights.copy()
            if len(word) < len(distribution):
                weights[TERMINATOR] *= distribution[len(word)]
            else:
                weights[TERMINATOR] *= distribution[-1]
        word += random.choices(list(weights.keys()), list(weights.values()))[0]
    
    return word.strip(INITIATOR + TERMINATOR)


def generate_words(io_manager, count):
    """
    Uses the selected book to generate some number of Jabberwocky style gibberish words.

    Args:
        io_manager: The IOManager currently in use
        count: The number of words to generate
    
    Returns:
        list: The list of generated words
    """

    wordlist = parse_words(io_manager)
    if wordlist is None:
        logging.warning("No Jabberwocky words generated")
        return None

    model = build_model(wordlist)
    distribution = length_distribution(wordlist)

    logging.info("Generating {count} Jabberwocky words")
    generated = []
    while len(generated) < count:
        word = generate_word(model, distribution)
        # Makes sure the generated word is new and not a repeat
        if word in wordlist or word in generated:
            logging.debug(f"Discarded \"{word}\" because it is a word")
            continue
        print(f"Added \"{word}\" to list")
        generated.append(word)
    
    return generated
