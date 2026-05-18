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

_TODO after running: pick 2-3 misses and 2-3 false positives, write 2-3 sentences each on why the agent got it wrong._
