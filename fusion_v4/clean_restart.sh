#!/bin/bash
# Real, permanent fix for the "duplicate process" problem.
# Run this ONE command before every session -- it guarantees both
# containers are genuinely empty, no manual PID hunting needed.

echo "=== Restarting both containers (guarantees zero leftover processes) ==="
docker restart switchslam_gpu_v2
docker restart vinsmono_test
sleep 4

echo "=== Verifying genuinely clean ==="
GPU_PROCS=$(docker exec switchslam_gpu_v2 bash -c "ps aux | grep -E 'ros|gz|rviz|nodelet' | grep -v grep")
VINS_PROCS=$(docker exec vinsmono_test bash -c "ps aux | grep -E 'vins|feature' | grep -v grep")

if [ -n "$GPU_PROCS" ]; then
    echo "WARNING: switchslam_gpu_v2 still has processes:"
    echo "$GPU_PROCS"
else
    echo "switchslam_gpu_v2: clean"
fi

if [ -n "$VINS_PROCS" ]; then
    echo "WARNING: vinsmono_test still has processes:"
    echo "$VINS_PROCS"
else
    echo "vinsmono_test: clean"
fi

echo ""
echo "=== Real, current IPs (use these in your launch commands) ==="
GPU_IP=$(docker inspect -f '{{.NetworkSettings.Networks.vins_bridge.IPAddress}}' switchslam_gpu_v2)
VINS_IP=$(docker inspect -f '{{.NetworkSettings.Networks.vins_bridge.IPAddress}}' vinsmono_test)
echo "switchslam_gpu_v2 IP: $GPU_IP"
echo "vinsmono_test IP:     $VINS_IP"
echo ""
echo "Real DISPLAY value on this host: $DISPLAY"
echo ""
echo "Ready for a clean launch."
