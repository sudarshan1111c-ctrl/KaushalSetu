"""Simple rule‑based matcher for workforce requests.

The function `find_matching_youth` returns a list of open
`WorkforceRequest` objects whose required skills intersect the youth's
comma‑separated skill list. This is a placeholder for a more sophisticated
ML‑based recommendation engine that could later use scikit‑learn.
"""

from .models import WorkforceRequest
from . import db

def _parse_skills(skills_str):
    """Convert a comma‑separated skill string into a set of lower‑cased skills."""
    if not skills_str:
        return set()
    return {s.strip().lower() for s in skills_str.split(',') if s.strip()}

def find_matching_youth(youth_profile):
    """Return open WorkforceRequest instances matching the youth's skills.

    Args:
        youth_profile (YouthProfile): The youth seeking work.

    Returns:
        list[WorkforceRequest]: Open requests where at least one required
        skill is present in the youth's skill set.
    """
    youth_skills = _parse_skills(youth_profile.skills)
    if not youth_skills:
        return []

    # Fetch all open requests
    open_requests = WorkforceRequest.query.filter_by(status='open').all()
    matches = []
    for req in open_requests:
        req_skills = _parse_skills(req.required_skills)
        if youth_skills & req_skills:
            matches.append(req)
    return matches
