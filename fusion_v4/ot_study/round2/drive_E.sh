#!/usr/bin/env bash
cd "$(dirname "$0")"
./be_r2.sh A_F20_clean && ./be_r2.sh B_gmax_V1b_clean && ./be_r2.sh B_F20_V1b_clean && echo BE_ALL_DONE
./drive_D.sh
