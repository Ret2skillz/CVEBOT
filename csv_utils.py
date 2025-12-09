import csv
import io
from typing import Iterable, Mapping

def vulns_to_csv_bytes(vulns: Iterable[Mapping]) -> bytes:
    """
    Convert an iterable of mapping-like vuln objects to CSV bytes.

    - vulns: iterable of dict-like objects. Keys used for header are the union of keys across items.
    - Returns: bytes of UTF-8 encoded CSV.
    """
    # Collect items into list to inspect keys (vulns is typically a small list)
    items = list(vulns)

    # If empty, return an empty CSV with only header
    if not items:
        header = ["id", "description", "url"]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(header)
        return output.getvalue().encode("utf-8")

    # Determine header as union of keys, but prefer a sensible ordering if present
    preferred_order = ["id", "description", "published", "url", "tag", "type_vuln", "severity"]
    keys = []
    seen = set()
    # Add preferred keys that exist in any item
    for k in preferred_order:
        for item in items:
            if k in item and k not in seen:
                keys.append(k)
                seen.add(k)
                break
    # add any other keys found across items
    for item in items:
        for k in item.keys():
            if k not in seen:
                keys.append(k)
                seen.add(k)

    # Fallback: if still no keys, try first item keys
    if not keys:
        keys = list(items[0].keys())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(keys)

    for item in items:
        row = [item.get(k, "") for k in keys]
        writer.writerow(row)

    return output.getvalue().encode("utf-8")
