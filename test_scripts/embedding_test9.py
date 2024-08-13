import re

def normalize_entry(entry):
    entry = entry.lower()
    
    # Extract authors (unchanged)
    authors = re.findall(r'([a-z]+,?\s+[a-z]\.)', entry)
    authors = sorted([author.strip() for author in authors])
    
    # Improved title extraction
    title_match = re.search(r'(?:^|[\s.])(["\']?)(.+?)\1?[\s.](?:\(|vol|journal|pp|doi)', entry, re.IGNORECASE)
    if title_match:
        title = title_match.group(2).strip()
    else:
        # Fallback: take the longest segment between punctuation as the title
        segments = re.split(r'[.,:;()]+', entry)
        title = max(segments, key=len).strip()
    
    # Extract year (unchanged)
    year_match = re.search(r'\b(19|20)\d{2}\b', entry)
    year = year_match.group(0) if year_match else ""
    
    return f"{' '.join(authors)} {title} {year}".strip()

# Test the function
test_entries = [
    'Smith, J. (2020). "The impact of AI on society". Journal of AI Ethics, 5(2), 123-145.',
    'Johnson, A. & Brown, B. (2019). Machine learning applications in healthcare. Medical AI Journal, 3(1), 45-60.',
    'Lee, C., & Park, D. Natural language processing in legal tech. Computational Law Review, 8(3), 201-220. (2021)',
    'Garcia, M.R. (2018) Blockchain technology and its potential in education',
    'Wilson, E.T., & Thompson, K.L. "The ethics of autonomous vehicles." Transportation Ethics Quarterly, 7(1), 15-32. 2022.'
]

for entry in test_entries:
    print(f"Original: {entry}")
    print(f"Normalized: {normalize_entry(entry)}")
    print()