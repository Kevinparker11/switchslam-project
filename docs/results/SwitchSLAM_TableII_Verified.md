# Switch-SLAM Table I and Table II, read from the page images of the paper (6 Nov 2026)

Until now only Multi Floor, Long Corridor and Farm were known from the text extraction (Table II is an image). Read from the PDF page images (RA-L 9(8), 2024, pages 7274 and 7275). Max / RMSE in m, translational ATE, mean of three runs, real time on an i7-1165G7, no loop closure; "-" = failure of localization (the paper gives no failure rule).

| Method | Fast Rotate | Plane | Farm | Handheld | Multi Floor | Long Corridor | ANYmal 1 | ANYmal 2 | ANYmal 3 | ANYmal 4 |
|---|---|---|---|---|---|---|---|---|---|---|
| LOAM | 1.41 / 0.44 | - | - | - | 17.9 / 10.6 | 25.6 / 12.6 | 10.26 / 6.63 | 9.67 / 5.05 | 7.81 / 2.39 | 5.79 / 3.90 |
| LIO-SAM | 0.72 / 0.21 | - | - | - | - | 17.6 / 7.64 | 8.38 / 3.77 | - | 7.10 / 3.52 | 2.47 / 1.02 |
| VINS-Mono | - | 1.17 / 0.41 | - | 21.4 / 10.3 | 12.8 / 6.30 | 23.8 / 11.8 | 24.9 / 9.08 | 36.9 / 15.1 | - | 8.55 / 3.52 |
| LVI-SAM | 8.82 / 1.82 | 1.82 / 0.69 | 28.8 / 5.75 | 3.27 / 1.23 | - | 8.62 / 4.37 | 5.83 / 2.41 | 9.53 / 3.28 | - | 6.42 / 3.75 |
| R2LIVE | 1.67 / 0.64 | 19.5 / 8.53 | 8.52 / 4.21 | - | 35.2 / 18.5 | - | - | 14.5 / 7.29 | 8.60 / 3.73 | 3.90 / 1.18 |
| R3LIVE | 10.1 / 6.43 | 9.01 / 5.84 | 58.6 / 34.7 | - | 32.4 / 19.0 | 14.5 / 7.63 | - | - | 6.77 / 2.06 | 27.1 / 14.0 |
| FAST-LIVO | 11.3 / 7.12 | - | 51.2 / 26.5 | - | - | - | - | 4.87 / 1.48 | - | - |
| **Switch-SLAM** | **1.50 / 0.23** | **1.27 / 0.35** | **1.10 / 0.38** | 3.07 / 1.25 | 3.63 / 1.61 | 5.09 / 2.42 | 2.96 / 1.29 | 3.41 / 1.37 | 3.68 / 1.61 | 2.42 / 1.05 |

(Order inside each cell: Max / RMSE. The table prints Max first, then RMSE.)

**Table I (dataset details).** Fast Rotate: LiDAR well-constrained, visual degenerate, 115 m. Plane: LiDAR degenerate, visual well-constrained, 109 m. **Farm: LiDAR degenerate and visual degenerate, 536 m.** The three are Gazebo simulations ("open-sourced environments", Clearpath cpr_gazebo, Velodyne VLP-16 10 Hz, 640 x 480 camera 60 Hz, IMU 200 Hz), shown in Fig. 5: Farm and Fast Rotate share the barn world (blue region = fast rotations, visual degeneration; red region = plane-only structure, LiDAR degeneration); Plane is a crop-row field with a red LiDAR-degenerate region covering the whole run.

## What this changes
1. **Our Farm L route is 80 m; the paper's Farm is 536 m** (about 6.7 times longer) and contains both a fast-rotation phase and a long plane-only phase. Our route has neither (A-LOAM unfed scores 0.478 on it). The earlier statement "this world does not reproduce their LOAM failure" stands, and the reason is now partly known: the distance and the degenerate stretch are not the same. The Farm row is not like for like and should say so with these two lengths.
2. **Fast Rotate: LOAM works in the paper** (1.41 / 0.44) and Switch-SLAM (1.50 / 0.23) does not beat LIO-SAM (0.72 / 0.21). VINS-Mono fails. A fusion that follows VINS-Mono would be hurt here; one that falls back to the LiDAR should match LOAM.
3. **Plane: LOAM, LIO-SAM and FAST-LIVO fail; VINS-Mono works** (1.17 / 0.41). Switch-SLAM (1.27 / 0.35) is slightly worse than VINS-Mono alone in max and slightly better in RMSE (a tie, one dataset).
4. On Multi Floor the paper's VINS-Mono is 6.30 and ours 1.28; on Long Corridor 11.8 and ours 5.81 (setup differences, already noted).
