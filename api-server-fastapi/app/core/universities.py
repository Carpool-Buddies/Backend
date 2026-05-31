"""Data-driven university registry.

Adding a new university is a one-line entry in UNIVERSITIES — no code changes
elsewhere. Org detection maps an email's domain (and any subdomain) to a code.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class University:
    code: str          # stable identifier stored on the user, e.g. "BGU"
    name_he: str       # Hebrew display name
    name_en: str       # English display name
    domains: tuple[str, ...]  # email domains that belong to this university


# To add a university: append an entry here. That's it.
UNIVERSITIES: tuple[University, ...] = (
    University(
        code="BGU",
        name_he="אוניברסיטת בן-גוריון בנגב",
        name_en="Ben-Gurion University of the Negev",
        domains=("bgu.ac.il", "post.bgu.ac.il"),
    ),
    University(
        code="TAU",
        name_he="אוניברסיטת תל אביב",
        name_en="Tel Aviv University",
        domains=("tau.ac.il", "mail.tau.ac.il"),
    ),
    University(
        code="HUJI",
        name_he="האוניברסיטה העברית בירושלים",
        name_en="Hebrew University of Jerusalem",
        domains=("huji.ac.il", "mail.huji.ac.il"),
    ),
    University(
        code="TECHNION",
        name_he="הטכניון",
        name_en="Technion - Israel Institute of Technology",
        domains=("technion.ac.il", "campus.technion.ac.il"),
    ),
)

# Built once at import: domain -> code, for O(1) lookup.
_DOMAIN_TO_CODE: dict[str, str] = {
    domain: uni.code for uni in UNIVERSITIES for domain in uni.domains
}

_CODE_TO_UNIVERSITY: dict[str, University] = {uni.code: uni for uni in UNIVERSITIES}


def detect_org(email: str) -> str | None:
    """Return the university code for an email, or None if unrecognized.

    Matches the full domain or any parent domain, so "x@cs.bgu.ac.il" still
    resolves to BGU via its "bgu.ac.il" entry.
    """
    if "@" not in email:
        return None
    domain = email.rsplit("@", 1)[1].strip().lower()

    parts = domain.split(".")
    for i in range(len(parts) - 1):
        candidate = ".".join(parts[i:])
        if candidate in _DOMAIN_TO_CODE:
            return _DOMAIN_TO_CODE[candidate]
    return None


def get_university(code: str | None) -> University | None:
    if code is None:
        return None
    return _CODE_TO_UNIVERSITY.get(code)
