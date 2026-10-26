# Sensor-outage campaign: results (run 26 Oct 2026, laptop, 00:25 to 07:15 IST)

Protocol: `Fault_Injection_Protocol.md` (rules written 25 Oct, before any run). Data: `~/faults_results.tgz` (returned 26 Oct). All 19 runs finished (C02_L30 was run afterwards, same code and settings, after the first session's time cap). Replicates r1, r2 differ only through non-determinism of the live stack. Scoring: Umeyama SE(3) full span against the same ground truth as Section 6.3; "GenZ-LIO alone" = the `aft_*` pose in the same log; "VINS-Mono alone" = raw VINS pose in the LiDAR frame (valid only for LiDAR outages). References = the 24 Oct live G20 runs (MF 4, LC 4, C02 2).

## Full-span ATE (m)

| Sequence | Outage | G20 no fault | G20 with outage | GenZ-LIO alone, same run | VINS alone |
| --- | --- | --- | --- | --- | --- |
| MF | none (rewrite control) | 0.31 (0.26-0.38) | 0.26 | 0.45 | 1.29 |
| MF | camera 3x10 s | | 0.45, 0.49 | 0.31, 0.36 | - |
| MF | camera 2x30 s | | 0.46, 0.42 | 0.45, 0.63 | - |
| MF | LiDAR 3x10 s | | 12.59, 12.59 | 12.57, 12.57 | 1.36, 1.38 |
| MF | LiDAR 2x30 s | | 149.96, 52.35 | 150.40, 52.15 | 1.42, 1.39 |
| LC | camera 3x10 s | 1.67 (1.64-1.75) | 1.55, 4.08 | 1.95, 2.02 | - |
| LC | camera 2x30 s | | 5.69, 2.24 (G22 5.59) | 1.92, 1.92 | - |
| LC | LiDAR 3x10 s | | 21.90, 9.91 | 22.03, 12.17 | 5.15, 5.13 |
| LC | LiDAR 2x30 s | | 21.95, 13.67 (G22 13.63) | 24.53, 15.84 | 5.38, 5.38 |
| C02 | camera 2x30 s | 0.29 (0.28-0.30) | 0.45 | 0.28 | - |
| C02 | LiDAR 2x30 s | | 32.38 | 32.39 | 13.91 |

## Findings
1. LiDAR outage breaks the fusion. At the first scan after every gap the GenZ-LIO pose jumps (largest step 32-41 m after 10 s, 41-348 m after 30 s) and the fused trajectory follows. All 9 runs break the survival rule (5 m per step). VINS alone is unaffected (MF 1.36-1.42 m). Fused is worse than VINS alone in 9 of 9 runs (MF +11 to +148 m, LC +5 to +17 m, C02 +18 m). On MF and C02 it equals GenZ-LIO alone; on LC it is about 2 m lower in 3 of 4 runs.
2. Camera outage costs about the VIO gain. MF 0.31 -> 0.42-0.49 (= GenZ-LIO alone, 0.46). LC and C02: worse than GenZ-LIO alone in 4 of 5 runs (+0.3, +2.1, +3.8 m on LC; +0.17 on C02). VINS restarts 2-4 times per run; in the two worst LC runs fused moved 16 m away from the LiDAR-inertial pose (6 m unfaulted).
3. Predictions: H0 first part refuted as stated (GenZ-LIO live spread 0.1-0.2 m, not 0.01), control passed; H1 refuted; H2 not supported; H3 not testable (2 pairs). No Wilcoxon (units: 5 camera, 5 LiDAR, rule needs n >= 6).
4. Not checked: exact live-equals-replay under outages (keyframe files were not in the returned pack); window RPE only for the full-span drift numbers quoted in the report.

## Consequence
The report (Section 6.8, 7.1, 7.2, 8, abstract) states that the structure is not robust to a LiDAR outage. A fix (hold VIO until the LiDAR pose after a gap agrees with the VIO motion) is future work and needs NEW outage recordings, since these are now development data.
