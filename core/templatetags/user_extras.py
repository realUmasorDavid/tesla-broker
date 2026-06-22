# core/templatetags/user_extras.py
from django import template

register = template.Library()

@register.filter
def initials(user):
    """Return user initials (e.g. John Doe → JD)"""
    if not user:
        return "U"
    
    first = user.first_name.strip() if user.first_name else ""
    last = user.last_name.strip() if user.last_name else ""
    
    if first and last:
        return (first[0] + last[0]).upper()
    elif first:
        return first[:2].upper()
    elif last:
        return last[:2].upper()
    else:
        # Fallback to username
        return user.username[:2].upper()
    
@register.filter
def format_tier(tier):
    """Convert 'tier1' to 'Tier 1'"""
    if not tier:
        return "Tier 1"
    return tier.replace('tier', 'Tier ')