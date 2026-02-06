"""
Human Copy Guidelines

Centralized guidelines for generating human-like AI copy across all reports.
Import these prompts/helpers into any AI generation module.
"""

# =============================================================================
# HUMAN COPY PROMPT FRAGMENTS
# =============================================================================

# Add this to system prompts to enforce human tone
HUMAN_TONE_SYSTEM = """
You write like a trusted senior advisor—not a generic content AI.

VOICE RULES:
- Be direct. Say "Your site has a problem" not "It has been observed that issues may exist."
- Use active voice. "Fix this now" not "This should be fixed."
- Be specific. Name actual numbers, pages, competitors.
- Use contractions naturally: "you're", "won't", "it's"—like a real person.
- Vary sentence length. Short punches. Then a longer sentence for flow.
- Never use: "delving", "game-changer", "synergy", "leverage", "utilize", "harness"
- Never start with: "In today's digital landscape", "In an era of", "As we navigate"
- Never use list markers like "Firstly", "Secondly", "In conclusion"
"""

# Add this to prompts that generate recommendations
RECOMMENDATIONS_TONE = """
When writing recommendations:
- Lead with ACTION, not explanation: "Add schema markup to your service pages" not "Schema markup is important because..."
- Include the WHY in one punchy clause: "...so AI search tools can cite your business."
- Be concrete: "Homepage loads in 4.2s—aim for under 2.5s" not "Improve page speed."
- Prioritize ruthlessly: If everything is "critical", nothing is.
"""

# Add this when generating executive summaries
EXECUTIVE_SUMMARY_TONE = """
This executive summary will be read by a CEO or business owner.

RULES:
- Open with the verdict, not the setup. "You're losing to three competitors" not "We analyzed your website..."
- Use "you/your" to make it personal
- One insight per paragraph. White space is your friend.
- Numbers are persuasive: "4 competitors outrank you for 'plumber near me'" > "Some competitors rank better"
- End with urgency that isn't annoying: State the cost of inaction, not a generic "act now!"
"""

# Banned phrases that immediately signal AI-generated copy
BANNED_PHRASES = [
    "in today's digital landscape",
    "in an ever-evolving",
    "as we navigate",
    "delving into",
    "game-changer",
    "paradigm shift",
    "leverage the power",
    "harness the potential",
    "synergistic",
    "utilize",
    "in conclusion",
    "to summarize",
    "firstly",
    "secondly",
    "thirdly",
    "it is important to note",
    "it goes without saying",
    "at the end of the day",
    "moving forward",
    "circle back",
    "low-hanging fruit",
    "best-in-class",
    "cutting-edge",
    "state-of-the-art",
    "revolutionary",
    "groundbreaking",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clean_ai_copy(text: str) -> str:
    """
    Post-process AI-generated copy to remove robotic phrases.

    Args:
        text: Raw AI-generated text

    Returns:
        Cleaned text with banned phrases removed/replaced
    """
    import re

    result = text

    # Remove common AI intro phrases
    intro_patterns = [
        r"^In today's (?:digital |competitive )?(?:landscape|world|environment)[,.\s]+",
        r"^(?:As we |When we )?(?:navigate|delve into|explore)[,.\s]+",
        r"^It's (?:important|worth) (?:to note|noting) that[,.\s]+",
    ]

    for pattern in intro_patterns:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.MULTILINE)

    # Replace stiff phrases with natural alternatives
    replacements = {
        # Common AI stiff words
        "utilize": "use",
        "utilizes": "uses",
        "utilizing": "using",
        "leveraging": "using",
        "leverage": "use",
        "harness": "use",
        "harnessing": "using",
        "delving into": "exploring",
        "delve into": "explore",
        "delving": "looking at",
        "paradigm": "approach",
        "synergy": "collaboration",
        "synergies": "benefits",
        # Overused superlatives
        "best-in-class": "top-tier",
        "best in class": "top-tier",
        "cutting-edge": "modern",
        "state-of-the-art": "advanced",
        "groundbreaking": "innovative",
        "revolutionary": "new",
        "game-changer": "significant improvement",
        "game changer": "significant improvement",
        # Filler phrases
        "it is important to note that": "",
        "it's important to note that": "",
        "it should be noted that": "",
        "needless to say,": "",
        "it goes without saying that": "",
        "in order to": "to",
        "due to the fact that": "because",
        "at the end of the day": "ultimately",
        "moving forward": "next",
        "going forward": "next",
        "at this point in time": "now",
        "for all intents and purposes": "essentially",
    }

    for phrase, replacement in replacements.items():
        result = re.sub(
            r'\b' + re.escape(phrase) + r'\b',
            replacement,
            result,
            flags=re.IGNORECASE
        )

    # Clean up any double spaces created
    result = re.sub(r' +', ' ', result)
    result = re.sub(r'\n +', '\n', result)

    return result.strip()


def get_human_prompt_prefix(tone: str = "advisor") -> str:
    """
    Get the appropriate prompt prefix for human-like copy.

    Args:
        tone: Type of copy - 'advisor', 'executive', 'technical', 'recommendations'

    Returns:
        Prompt prefix to prepend to AI prompts
    """
    prefixes = {
        "advisor": HUMAN_TONE_SYSTEM,
        "executive": HUMAN_TONE_SYSTEM + "\n\n" + EXECUTIVE_SUMMARY_TONE,
        "recommendations": HUMAN_TONE_SYSTEM + "\n\n" + RECOMMENDATIONS_TONE,
        "technical": HUMAN_TONE_SYSTEM,
    }

    return prefixes.get(tone, HUMAN_TONE_SYSTEM)


def score_copy_humanness(text: str) -> dict:
    """
    Score how human-like a piece of copy is.

    Returns a dict with:
    - score: 0-100 (higher = more human)
    - issues: List of detected problems
    - suggestions: List of improvement suggestions
    """
    issues = []
    deductions = 0

    text_lower = text.lower()

    # Check for banned phrases
    for phrase in BANNED_PHRASES:
        if phrase.lower() in text_lower:
            issues.append(f"Contains AI-sounding phrase: '{phrase}'")
            deductions += 5

    # Check sentence variety
    sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    if sentences:
        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)

        if avg_length > 25:
            issues.append("Sentences are too long on average")
            deductions += 10

        # Check for variety
        if len(set(lengths)) < len(lengths) * 0.5:
            issues.append("Sentence lengths are too uniform")
            deductions += 5

    # Check for passive voice indicators
    passive_indicators = [" is being ", " was being ", " has been ", " had been ", " will be ", " should be "]
    passive_count = sum(1 for p in passive_indicators if p in text_lower)
    if passive_count > 3:
        issues.append(f"Too much passive voice ({passive_count} instances)")
        deductions += passive_count * 2

    # Check for contractions (humans use them)
    contractions = ["'s", "'re", "'ll", "'ve", "n't", "'d", "'m"]
    has_contractions = any(c in text for c in contractions)
    if not has_contractions and len(text) > 200:
        issues.append("No contractions found - sounds formal/robotic")
        deductions += 5

    # Check for "you/your" (direct address)
    if "you" not in text_lower and "your" not in text_lower and len(text) > 200:
        issues.append("No direct 'you/your' address - less engaging")
        deductions += 5

    score = max(0, 100 - deductions)

    suggestions = []
    if score < 80:
        suggestions.append("Try reading it aloud - edit anything that sounds stiff")
    if score < 60:
        suggestions.append("Rewrite opening sentences to be more direct")
        suggestions.append("Add contractions to sound more natural")

    return {
        "score": score,
        "issues": issues,
        "suggestions": suggestions,
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "HUMAN_TONE_SYSTEM",
    "RECOMMENDATIONS_TONE",
    "EXECUTIVE_SUMMARY_TONE",
    "BANNED_PHRASES",
    "clean_ai_copy",
    "get_human_prompt_prefix",
    "score_copy_humanness",
]
