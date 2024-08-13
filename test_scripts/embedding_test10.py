import re

def normalize_entry(entry):
    original_entry = entry
    entry = entry.lower()
    
    # Extract potential authors
    author_matches = re.findall(r'([a-z]+,?\s+[a-z]\.(?:\s*&\s*[a-z]+,?\s+[a-z]\.)*)', entry)
    
    # Validate authors
    authors = []
    for author in author_matches:
        # Check if the potential author is at the start of the entry or preceded by '&'
        if entry.index(author) == 0 or '&' in entry[entry.index(author)-2:entry.index(author)]:
            authors.append(author.strip())
        else:
            break  # Stop if we find a non-author match
    
    # Remove validated authors from the entry
    for author in authors:
        entry = entry.replace(author, '', 1)  # Remove only the first occurrence
    
    # Extract year, but don't remove it yet
    year_match = re.search(r'\b(19|20)\d{2}\b', entry)
    year = year_match.group(0) if year_match else ""
    
    # Clean up the remaining text (potential title)
    title = re.sub(r'[,.():;]', ' ', entry)  # Replace punctuation with spaces
    title = re.sub(r'\s+', ' ', title)  # Replace multiple spaces with a single space
    title = title.strip()  # Remove leading/trailing whitespace
    
    # Check if the year is part of the title
    if year and year in original_entry and year not in title:
        # Year was in parentheses or separated by punctuation, so we keep it separate
        title = title.replace(year, '').strip()
    elif year and year in title:
        # Year is part of the title, so we leave it in and set publication year to empty
        year = ""
    
    # Reconstruct the normalized entry
    normalized = f"{' & '.join(authors)} {title} {year}".strip()
    return normalized

# Test the function
test_entries = [
    'Smith, J. (2020). "The impact of AI on society". Journal of AI Ethics, 5(2), 123-145.',
    'Johnson, A. & Brown, B. (2019). Machine learning applications in healthcare. Medical AI Journal, 3(1), 45-60.',
    'Lee, C., & Park, D. Natural language processing in legal tech. Computational Law Review, 8(3), 201-220. (2021)',
    'Garcia, M.R. (2018) Blockchain technology and its potential in education',
    'Wilson, E.T., & Thompson, K.L. "The ethics of autonomous vehicles." Transportation Ethics Quarterly, 7(1), 15-32. 2022.',
    'Turing, A.M. Computing machinery and intelligence. Mind, 59(236), 433-460. 1950',
    'Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep learning. MIT Press.',
    'Nakamoto, S. Bitcoin: A peer-to-peer electronic cash system. 2008.',
    'Orwell, G. 1984. Secker & Warburg. 1949.',
    'Asimov, I. I, Robot. Gnome Press. 1950.',
    'The impact of A.I. on society. (2020). Journal of AI Ethics, 5(2), 123-145.',
    'Watson, J.D. & Crick, F.H.C. A structure for deoxyribose nucleic acid. Nature 171, 737–738 (1953).'
]

for entry in test_entries:
    print(f"Original: {entry}")
    print(f"Normalized: {normalize_entry(entry)}")
    print()