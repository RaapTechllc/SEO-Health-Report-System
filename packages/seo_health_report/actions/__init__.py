"""
Action Engine — DFY/DWY/DIY Classification and Generation

Transforms raw audit findings into actionable items classified by delivery tier:
- DFY (Done-For-You): Automated fixes with ready-to-deploy artifacts
- DWY (Done-With-You): Step-by-step instructions with code snippets
- DIY (Do-It-Yourself): Strategic guidance requiring human judgment
"""

from .classifier import classify_actions

__all__ = ["classify_actions"]
