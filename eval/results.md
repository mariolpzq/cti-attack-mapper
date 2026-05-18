# Eval Results

Strict T-ID exact-match precision / recall / F1.

## Summary

| Report | Predicted | Truth | Precision | Recall | F1 |
|---|---|---|---|---|---|
| report_1 | 9 | 10 | 0.78 | 0.70 | 0.74 |
| report_2 | 8 | 16 | 0.25 | 0.12 | 0.17 |
| report_3 | 7 | 28 | 0.57 | 0.14 | 0.23 |
| **Macro avg** | | | **0.53** | **0.32** | **0.38** |

## Per-report details

### report_1

- **Hits** (7): T1003.001, T1021.002, T1041, T1059.001, T1071.001, T1547.001, T1566.001
- **Misses** (3): T1027, T1204.002, T1560.001
- **Extras** (2): T1059.005, T1560

### report_2

- **Hits** (2): T1059.001, T1486
- **Misses** (14): T1003, T1021.002, T1033, T1046, T1047, T1053, T1055, T1069.002, T1083, T1134, T1135, T1482, T1518.001, T1562.001
- **Extras** (6): T1003.001, T1041, T1053.005, T1218.010, T1570, T1685

### report_3

- **Hits** (4): T1003.001, T1059.001, T1204.002, T1558.003
- **Misses** (24): T1016, T1018, T1021.001, T1021.002, T1036, T1047, T1055, T1057, T1059.003, T1069.002, T1070.004, T1071.001, T1078, T1087.002, T1105, T1110.001, T1218.011, T1219, T1482, T1518, T1553.005, T1566, T1569, T1570
- **Extras** (3): T1021.006, T1563.002, T1574.001

## Error analysis

### Misses

**T1204.002 — User Execution: Malicious File (report_1)**
The report states "the victim opened the document and enabled macros." The agent
correctly identified delivery (T1566.001) from the same clause but did not
separately surface the user's act of executing the file as a distinct technique.
Delivery and execution co-occur in a single narrative sentence, and the agent
collapses them into the more salient technique. This boundary between Initial
Access and Execution phases is a consistent challenge across all reports.

**T1562.001 — Disable or Modify Tools (report_2)**
The IcedID report describes security software being disabled but in passing,
without naming specific tools or mechanisms. The agent's conservative prompt
instructs it not to include techniques "implied without supporting narrative,"
so it correctly declines to predict T1562.001 — but the ground truth includes
it. This is a deliberate precision/recall tradeoff set by the prompt; a less
conservative agent would catch more implied techniques at the cost of more
false positives.

**T1071.001 — Application Layer Protocol: Web Protocols (report_3)**
The BumbleBee report describes C2 communication over web protocols but this
behavior appears in the second half of the report, past the MAX_REPORT_CHARS
truncation boundary. The agent never read the relevant passage. This is an
infrastructure limitation — not a reasoning failure — and the primary driver
of the low recall on longer reports.

---

### False positives (extras)

**T1685 — hallucinated technique ID (report_2)**
T1685 does not exist in MITRE ATT&CK Enterprise. The agent generated a
plausible-looking identifier for a behavior where the RAG retrieval returned
no strong candidate, rather than returning nothing or flagging uncertainty.
This failure mode is reproducible: T1685 appeared in two separate runs on
the same report. A post-processing validation step — checking predicted IDs
against the known ATT&CK index — would eliminate this class of error with
zero model changes.

**T1059.005 — Visual Basic (report_1)**
The synthetic report explicitly mentions "an embedded VBA macro executed."
VBA is Visual Basic for Applications and maps directly to T1059.005. This is
not a false positive — the agent correctly identified a technique the
ground-truth annotation missed. It illustrates that human-annotated ground
truth is itself imperfect, and that precision/recall scores have a ceiling
set by annotator consistency rather than model quality alone.

**T1021.006 / T1563.002 — implausible technique assignments (report_3)**
T1021.006 (Remote Services: Windows Remote Management) and T1563.002 (Remote
Service Session Hijacking: RDP Hijacking) are plausible Windows lateral
movement techniques but are not supported by explicit evidence in the BumbleBee
narrative. These suggest the agent occasionally accepts RAG candidates that
are semantically adjacent but contextually underspecified — accepting a
technique because the description partially matches rather than because the
report clearly describes the behavior.
