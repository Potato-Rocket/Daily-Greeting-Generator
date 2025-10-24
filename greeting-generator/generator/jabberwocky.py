"""
Random word generation based on a provided text file.

Implements N-gram markov chains to mimic english phonetics.
"""
import unicodedata
import re
import random

UNICODE_FIXES = str.maketrans({
    '\u2018': "'",  # LEFT SINGLE QUOTATION MARK
    '\u2019': "'",  # RIGHT SINGLE QUOTATION MARK
})

INITIATOR = '#'
TERMINATOR = '$'
CONTEXT_SIZE = 2

def parse_words(book_path):
    try:
        with open(book_path, 'r', encoding='utf-8') as file:
            # Step 1: Normalize and fix Unicode
            text = file.read()
            text = unicodedata.normalize('NFKD', text)
            text = text.lower()  # Lowers certain unicode fixes
            text = text.translate(UNICODE_FIXES)
            text = re.sub(r'-{2,}', ' ', text)   # Two or more hyphens

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

            # Step 3: Split words, discard short ones, count frequency
            rawlist = text.split()
            wordlist = []
            for word in rawlist:
                word = word.strip('-')
                if len(word) > CONTEXT_SIZE:
                    if word not in wordlist:
                        wordlist.append(word)

            return wordlist

    except FileNotFoundError:
        print("Book file is missing!")
        return None, None
    
    except Exception as e:
        print(f"Failed to parse selected book: {e}")
        return None, None


def build_model(wordlist):
    model = {}

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
    distribution = {}
    
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

    return cumulative


def generate_word(model, distribution):
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
    wordlist = parse_words("/mnt/data/Dropbox/Projects/021 Daily Greeting/greeting-generator/data/moby_dick.txt")
    model = build_model(wordlist)
    distribution = length_distribution(wordlist)
    print(distribution)

    generated = []
    while len(generated) < count:
        word = generate_word(model, distribution)
        if len(word) <= CONTEXT_SIZE:
            print(f"Discarded \"{word}\" because too short")
            continue
        if word in wordlist:
            print(f"Discarded \"{word}\" because it is a word")
            continue
        print(f"Added \"{word}\" to list")
        generated.append(word)
    
    return generated
    

if __name__ == "__main__":
    generate_words(None, 100)
