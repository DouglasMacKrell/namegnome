import re

filename = "Show-S01E01-E02-Episode.mp4"
print(f"Testing filename: {filename}")

# Test the span pattern
span_pattern = r"S\d+E(\d+)[-–]E(\d+)"
span_match = re.search(span_pattern, filename)
print(f"Span pattern '{span_pattern}': {span_match}")
if span_match:
    print(f"  Groups: {span_match.groups()}")

# Test single episode pattern
single_pattern = r"S\d+E(\d+)"
single_match = re.search(single_pattern, filename)
print(f"Single pattern '{single_pattern}': {single_match}")
if single_match:
    print(f"  Groups: {single_match.groups()}")

# Test anthology keywords
anthology_keywords = ["and", "&", "plus", "with"]
has_anthology = any(keyword in filename.lower() for keyword in anthology_keywords)
print(f"Has anthology keywords: {has_anthology}")
