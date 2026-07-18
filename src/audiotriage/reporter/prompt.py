INCIDENT_REPORT_TEMPLATE = """
## Audio Incident

- Timestamp: {timestamp}
- Classification: {category} ({confidence:.2f})
- Likely Cause: {likely_cause}

### Evidence
{evidence_block}

### Raw Context
{raw_context}
""".strip()


SUMMARY_REPORT_TEMPLATE = """
# AudioTriage Summary

Period: {since} -> {until}
Total incidents: {total}

## Top Categories
{category_block}

## Top Correlated Causes
{cause_block}
""".strip()
