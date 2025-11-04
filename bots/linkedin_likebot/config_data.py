"""
LinkedIn Bot Configuration Data
Edit these lists for your LinkedIn bot behavior
"""

# Keywords to search for on LinkedIn
# Posts containing these keywords will be found and potentially liked
KEYWORDS = [
    "horeca",
    "restaurant",
    "café",
    "bar",
    "hospitality",
    # Add more keywords here
]

# Words to exclude - posts containing these will be skipped
# Even if they match keywords
EXCLUDEWORDS = [
    "vacature",
    "solliciteer",
    "hiring",
    "recruitment",
    "job opening",
    # Add more exclude words here
]

# LinkedIn profiles of interesting people
# The bot will visit their activity pages and like recent posts
INTERESTING_PEOPLE = [
    # Add more LinkedIn profile URLs here
    # Format: https://www.linkedin.com/in/username/
]