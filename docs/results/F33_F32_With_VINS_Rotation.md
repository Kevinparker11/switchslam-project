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

## GEODE run 1, rules written before the run (batches/f33_geode.sh, 0.5x replay as the earlier GEODE runs)
GEODE is the bag where VINS-Mono is poor in stretches (F30 diverged there: 13.04 and 195.58 m; F32 not run there). F33 uses VINS-Mono rotation only while it passes the checks, so GEODE is the test of the fallback.
- Prediction: the failed VINS-Mono stretches fall back to A-LOAM rotation and guess, so the result should land near A-LOAM and F26, 3 to 7 m. Not a result.
- Precondition: tensor found for at least 95 % of scans. `sw_rotv` share is reported, not thresholded (a low share is a finding here).
- Bands: 3.26 to 6.36 m (F26 range) = "close to F26"; below = "lower"; above 6.36 m = "higher"; above 13 m = "no better than F30 run 1". A diverged or crashed run counts.
- Report: ATE RMSE / max, `sw_rotv` share, VINS failed share, gate closed share, heading error against ground truth if available, angle between output and A-LOAM rotation.
- n = 1 supports no claim; GEODE is tuned-on data for F25 to F27.

## Result: GEODE run 1 (uploaded for_claude_f33_geode.zip, 10 Nov 2026)
ATE RMSE / max, full span: **9.73 / 22.23 m** (3162 poses, GT path 301.1 m). F26 3.26 to 6.36 (n=3, mean 5.04 / 12.38), F24 6.15 to 9.15 (n=4, mean 7.23 / 18.25), F30 13.04 and 195.58.

Precondition: tensor found for 3453 of 3455 scans. Met.

Band: above 6.36 m, so "higher" than F26; below 13 m, so better than F30 run 1. Prediction (3 to 7 m) was too low. The result is 0.6 m above the top of F24's four-run spread (9.15 m), and one run does not separate it from that spread.

What the log shows:
- VINS-Mono was treated as failed on **76.3 %** of scans (step guard or no pose; the scale gate was closed on 65.2 %, no pose on 8.4 %). VINS-Mono alone scores 695 m ATE on this bag (diverged), so the checks were right to distrust it.
- Hence the VINS rotation was used on only **23.7 %** of scans (`sw_rotv`), and the run is mostly A-LOAM's rotation and guess with the Switch remap: output branches case 1 1469, case 2 1397, case 3 305 scans, guess kinds LIDAR 2866, VO 200, INTERP 105.
- Degenerate branch 53.7 % (R 53.4 %, T 0.0 %, TT 1.2 %), the same detector profile as the F30 runs on this bag (R about 54 %).
- Angle between the output and A-LOAM's rotation: median 0.5, p90 2.4, max 8.4 deg. Output ATE equals A-LOAM's own (9.72 m).
- The error over time against a whole-run alignment is not a clean drift curve (16 m in the first 40 s, 3 to 5 m at 80 to 160 s, 20 m at the end), so I do not read an onset time from it.

Reading: on GEODE F33 is a mostly-LiDAR run because VINS-Mono is unusable there, and it lands at the upper end of what F24 does on this bag, above F26's range. The structure of F33 gives no way to reach F26's GEODE values here; F26's lower numbers come from parts F33 does not have (weighted translation fusion, SAH heading anchor). n = 1, development data, no claim.
Summary of F33 so far: Multi Floor 0.83 / 1.74 (close to F26, inside the F24 / F26 spread), GEODE 9.73 / 22.23 (higher than F26). Not run: Corridor02, Cave02, Long Corridor, Farm, repeats.
