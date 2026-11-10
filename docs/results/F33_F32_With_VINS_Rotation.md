# F33: F32 with the output rotation taken from VINS-Mono (10 Nov 2026), rules written before any run

## Why
F32 on Multi Floor run 1 gave 6.05 / 12.48 m (F26: 0.54 m). The output of F32 is A-LOAM's own pose, and A-LOAM's heading drifted: yaw error against ground truth 12.6 / 34.8 / 32.4 deg at 100 / 200 / 300 s, F26 5.9 / 1.9 / 1.2 deg (F32 doc). F26 takes its rotation from VINS-Mono (c_R = 0) plus the structure heading anchor. F33 gives F32 the first of the two, nothing else.

## What changes against F32
On every scan where VINS-Mono is trusted (a pose is there, the step guard 1 m / 0.5 rad passes, the scale-consistency gate is open, i.e. not `vo_fail`):
1. the rotation increment of the LiDAR step is VINS-Mono's (translation still the A-LOAM scan-to-scan step), so the guess given to A-LOAM's mapping carries VINS-Mono's rotation;
2. the output keeps that rotation: the rotation correction of the scan-to-map solve is dropped (x[:3] = 0), as F26 with c_R = 0;
3. the translation follows the Switch-SLAM rule unchanged (guess kind, Eq. 15 / 16 remap, our R / T / additional-T detection).
On scans without a trusted VINS-Mono everything is F32 (A-LOAM's rotation). Config `F33` = F32 + `ROT_SRC=vins`; default `ROT_SRC=lidar` reproduces F32 and F30 (22 detector and core tests pass, including two new ones: VINS rotation is kept against a 3 deg scan-to-map turn, and the fallback when VINS-Mono is distrusted or absent). No SAH heading anchor, no new constant.

## What this is, for the paper wording
LiDAR-primary in translation, VINS-Mono-primary in rotation, the same description F26 earns. It is not "LiDAR primary" in rotation.

## Known caveat
A-LOAM's map is built from its own scan-to-map poses, while the guess handed to it is now on the VINS-Mono rotation chain. The two frames can differ by the slow heading difference between VINS-Mono and the map. The matching has to absorb that. From the F32 log, VINS-Mono's own heading drift on Multi Floor is 3.9 / 4.8 / 3.9 deg at 100 / 200 / 300 s (5.7 deg at the end), against A-LOAM's 12.6 / 35.6 / 31.1, so the offset should stay in the range scan matching handles. It is reported from the log (angle between `fused_q` and `aft_q`), not assumed.

## Run (batches/f33_mf.sh, about 15 min)
Multi Floor F33 run 1.

## Predictions written before the run
- Heading error of the output: about 4 to 6 deg at the end (VINS-Mono's drift without the anchor), against 32 deg for F32.
- ATE: between VINS-Mono alone (1.30 m) and F26's 0.54 m is not guaranteed, since the translation is still A-LOAM-based with the Switch remap. My guess is 1 to 3 m. Not a result.

## Reading rules
1. Preconditions (else the run is void for the claim, reported, not adjusted): tensor found for at least 95 % of scans; `sw_rotv` = 1 on at least 85 % of scans.
2. Bands on Multi Floor: up to 1.5 m = "close to F26" (F24 / F26 spread 0.45 to 1.01 m); above 1.5 and up to 3 m = "improved on F32, not close"; above 3 m = "rotation source is not the main cause".
3. Report: ATE RMSE / max, heading error at 100 / 200 / 300 s and end, 10 s rotation error, `sw_rotv` share, VINS failed share, gate closed share, maximum angle between output and A-LOAM rotation.
4. n = 1 supports no claim; a failed run counts. Multi Floor is the calibration bag for the gates, so this is development data. Adoption needs held-out bags and a rule written first.

## Result: Multi Floor run 1 (uploaded for_claude_f33_mf.zip, 10 Nov 2026)
ATE RMSE / max, full span: **0.83 / 1.74 m** (4004 poses, GT path 272.4 m; common window 0.81 / 1.70). F32 6.05 / 12.49, F26 0.54 / 1.01, F24 0.45 to 1.01 (n=3), VINS-Mono alone 1.31 / 4.75.

Preconditions (rule 1): tensor found for 4132 of 4138 scans (99.9 %), `sw_rotv` = 1 on 95.0 % of scans. Both met.

Band (rule 2): 0.83 m is inside "up to 1.5 m = close to F26" and inside the F24 / F26 spread (0.45 to 1.01). The prediction written before the run was 1 to 3 m; the result is below it.

| | F33 | F32 | F26 |
|---|---|---|---|
| Heading drift 100 / 200 / 300 s / end (deg) | 4.1 / 2.5 / 2.7 / 5.8 | 12.6 / 34.8 / 32.4 / 12.9 | 5.9 / 1.9 / 1.2 / 5.6 |
| 10 s rotation error median / p90 (deg) | 1.10 / 4.84 | 1.89 / 7.03 | 1.05 / 3.10 |

Same switching as F32: degenerate branch 46.1 % (R 37.2 %, T 0.0 %, TT 9.6 %), VINS-Mono failed 5.0 % (step guard), gate closed 0.0 %. Output branches: Eq. 16 case 1 2161, case 2 198, case 3 1652 scans.

Map consistency (the caveat): angle between the output rotation and A-LOAM's scan-to-map rotation median 1.5, p90 6.2, max 16.9 deg (3.3 / 0.5 / 7.4 deg at 100 / 200 / 300 s). The matching absorbed it, no mapping failure in the run.

Reading: the change of rotation source alone moves Multi Floor from 6.05 to 0.83 m, so the F32 error was the A-LOAM heading drift, as diagnosed. The remaining gap to F26 (0.83 against 0.54, max 1.74 against 1.01) is without the heading anchor and without F26's weighted translation fusion. n = 1 on the calibration bag: development data, no claim; the test of this result is held-out bags and repeats. Not run: GEODE and the other bags for F33.
