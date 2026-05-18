# Eval reports — how to build the ground truth set

You need 5 CTI reports with published ATT&CK technique mappings. For each report, create two files in this directory:

- `report_N.txt` — the narrative prose of the report (no ATT&CK table)
- `report_N_truth.json` — `{"techniques": ["T1059.001", "T1566.001", ...]}`

## Where to find reports with mappings

**The DFIR Report** — https://thedfirreport.com
Most posts end with a full ATT&CK technique table. Pick reports with 10-25 techniques (skip the very long ones with 50+).

**Mandiant blog (now Google Threat Intelligence)** — https://cloud.google.com/blog/topics/threat-intelligence
Many incident write-ups include MITRE ATT&CK mapping sections.

**CISA advisories** — https://www.cisa.gov/news-events/cybersecurity-advisories
Consistently include a "MITRE ATT&CK Tactics and Techniques" section.

**Microsoft Threat Intelligence blog** — https://www.microsoft.com/en-us/security/blog/topic/threat-intelligence/
Technique lists frequently appear at the bottom of detailed posts.

## How to prep each report

1. Copy the narrative prose into `report_N.txt`. **Strip the ATT&CK table at the bottom** — otherwise the agent reads the answer key instead of inferring.
2. From the stripped table, build `report_N_truth.json` like:

```json
{
  "techniques": ["T1566.001", "T1059.001", "T1027", "T1071.001"],
  "source_url": "https://thedfirreport.com/2024/..."
}
```

## Picking good reports

- 10-25 techniques each is the sweet spot.
- Skip reports that are entirely IOC dumps with no narrative — the agent needs prose to reason over.
- A mix of intrusion types (ransomware, espionage, phishing) gives more meaningful error analysis.
- Save the source URL in the truth JSON so you can re-find it later for the writeup.
