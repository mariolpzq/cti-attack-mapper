# Eval reports

For each CTI report, create two files in this directory:

- `report_N.txt` — the narrative prose of the report (no ATT&CK table)
- `report_N_truth.json` — `{"techniques": ["T1059.001", "T1566.001", ...]}`



1. Copy the narrative prose into `report_N.txt`. **Strip the ATT&CK table at the bottom**; otherwise, the agent reads the answer key instead of inferring.
2. From the stripped table, build `report_N_truth.json` like:

```json
{
  "techniques": ["T1566.001", "T1059.001", "T1027", "T1071.001"],
  "source_url": "https://thedfirreport.com/2024/..."
}
```

## Chosen reports

*Report 1*: smoke test
*Report 2* [Nitrogen Campaign Drops Sliver and Ends With BlackCat Ransomware ](http://thedfirreport.com/2024/09/30/nitrogen-campaign-drops-sliver-and-ends-with-blackcat-ransomware/)
*Report 3*: [IcedID to XingLocker Ransomware in 24 hours](https://thedfirreport.com/2021/10/18/icedid-to-xinglocker-ransomware-in-24-hours/)
*Report 4*: [BumbleBee Roasts Its Way to Domain Admin](https://thedfirreport.com/2022/08/08/bumblebee-roasts-its-way-to-domain-admin/)