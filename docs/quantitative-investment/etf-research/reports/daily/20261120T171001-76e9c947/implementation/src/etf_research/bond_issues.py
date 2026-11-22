"""Look through disclosed bond codes using official exchange/interbank identities."""
from decimal import Decimal as D
from .publication import read, verify_bundle


def identity_map(folder):
    verify_bundle(folder)
    identities = {}
    for meta_file in sorted(folder.glob("identity_*_request.json")):
        meta = read(meta_file)
        response = read(folder / (meta["name"] + ".body"))
        rows = response.get("result", [])
        if meta["status"] != 200 or meta.get("error") or len(rows) != 1:
            raise ValueError("Unverified bond identity")
        row = rows[0]
        if meta["name"] != "identity_" + row["BOND_CODE"] or row["ISSUE_OWNER"] != "财政部":
            raise ValueError("Bond identity mismatch")
        for code in (row["BOND_CODE"], row["BANK_CODE"]):
            if code in identities:
                raise ValueError("Conflicting bond alias: " + code)
            identities[code] = row["BOND_FULL"]
    return identities


def issue_exposures(fund, identities, etf_value, account_nav):
    nav = D(fund["nav"])
    groups = {}
    seen = set()
    for position in fund["listed_positions"]:
        code = position["code"]
        if code in seen:
            raise ValueError("Duplicate disclosed bond code")
        seen.add(code)
        name = identities.get(code)
        group = groups.setdefault(name or code, dict(issue=name, codes=[], fair_value=D(0)))
        group["codes"].append(code)
        group["fair_value"] += D(position["fair_value"])
    total = sum(row["fair_value"] for row in groups.values())
    if abs(total / nav - D(fund["listed_nav_fraction"])) > D("1e-24"):
        raise ValueError("Grouped bond exposure does not reconcile")
    result = []
    for row in groups.values():
        fraction = row["fair_value"] / nav
        amount = etf_value * fraction
        result.append(dict(**{**row, "fair_value": str(row["fair_value"])},
                           fund_fraction=str(fraction), portfolio_amount=str(amount),
                           portfolio_fraction=str(amount / account_nav)))
    return result
