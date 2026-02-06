"""
Formatting Utilities for Report Generation

Common formatting functions for consistent, professional report output.
Use these everywhere to prevent grammar errors like "1th" or "1 months".
"""


def ordinal(n: int) -> str:
    """
    Convert integer to ordinal string (1st, 2nd, 3rd, 4th, etc.).
    
    Examples:
        ordinal(1) -> "1st"
        ordinal(2) -> "2nd"
        ordinal(3) -> "3rd"
        ordinal(11) -> "11th"
        ordinal(21) -> "21st"
    """
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


def pluralize(value: int, singular: str, plural: str = None) -> str:
    """
    Return singular or plural form based on value.
    
    Examples:
        pluralize(1, 'month') -> 'month'
        pluralize(3, 'month') -> 'months'
        pluralize(1, 'company', 'companies') -> 'company'
        pluralize(5, 'company', 'companies') -> 'companies'
    
    Args:
        value: The numeric value to check
        singular: The singular form of the word
        plural: The plural form (defaults to singular + 's')
    
    Returns:
        The appropriate form of the word
    """
    if plural is None:
        plural = singular + 's'
    return singular if value == 1 else plural


def format_months(value: int) -> str:
    """
    Format a number of months with proper pluralization.
    
    Examples:
        format_months(1) -> "1 month"
        format_months(3) -> "3 months"
    """
    return f"{value} {pluralize(value, 'month')}"


def format_rank(rank: int, total: int = None) -> str:
    """
    Format a ranking with optional total.
    
    Examples:
        format_rank(1) -> "#1"
        format_rank(1, 10) -> "#1 of 10"
    """
    if total:
        return f"#{rank} of {total}"
    return f"#{rank}"


def format_percentile(value: int) -> str:
    """
    Format a percentile with proper ordinal.
    
    Examples:
        format_percentile(1) -> "1st percentile"
        format_percentile(50) -> "50th percentile"
    """
    return f"{ordinal(value)} percentile"


__all__ = [
    'ordinal',
    'pluralize',
    'format_months',
    'format_rank',
    'format_percentile',
]
