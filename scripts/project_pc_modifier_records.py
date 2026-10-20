"""Project complete PC modifier records onto separate Almanac display fields.

The full Chinese title AND body identify the record. A matching body alone,
a repeated title, or an array position is not sufficient evidence.
"""
import collections
from build_metadata_translation import is_usable_modifier_description


def project_catalog_entries(catalog, source_records, english_records, usable):
    by_source = collections.defaultdict(list)
    for section, records in source_records.items():
        if not isinstance(records, dict):
            continue
        translated = english_records.get(section, {})
        if not isinstance(translated, dict):
            continue
        for record_id, source in records.items():
            target = translated.get(record_id)
            if not isinstance(source, dict) or not isinstance(target, dict):
                continue
            text = source.get("desc")
            name, body = target.get("name"), target.get("desc")
            if (not isinstance(text, str) or not usable(name) or not usable(body)
                    or not is_usable_modifier_description(body)):
                continue
            by_source[text].append((section, record_id, name, body))
    result = []
    for index, entry in enumerate(catalog["entries"]):
        title = entry["title"]
        # Trials carry an extra UI category prefix absent from PC source.
        if entry.get("category") == "Trials" and title.startswith("试炼："):
            title = title[len("试炼："):]
        matches = by_source.get(title + "：" + entry["description"], [])
        if len(matches) != 1:
            continue
        section, record_id, name, body = matches[0]
        result.append({"index": index, "pc_section": section,
                       "pc_id": record_id, "title": name, "description": body})
    return result
