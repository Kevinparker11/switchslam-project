#!/usr/bin/env python3
"""Fast check of a ROS1 bag: which topics exist, and does the LiDAR PointCloud2 carry per-point time / ring?

Reads only the bag index at the end of the file and the first chunk that holds the LiDAR topic, so it takes
seconds even for a multi-GB bag on a slow USB drive (the rosbag python API reads every chunk header first).
Standard library only. Chunk compression none/bz2 works everywhere; lz4 needs the python 'lz4' module.
usage: python3 check_bag_fields.py <file.bag> [topic ...]
"""
import bz2
import struct
import sys

TOPICS = sys.argv[2:] or ["/velodyne_points", "/velodyne_packets", "/imu/data"]
DT = {1: ("b", 1), 2: ("B", 1), 3: ("h", 2), 4: ("H", 2), 5: ("i", 4), 6: ("I", 4), 7: ("f", 4), 8: ("d", 8)}


def read_record(f):
    hl = f.read(4)
    if len(hl) < 4:
        return None
    hl = struct.unpack("<I", hl)[0]
    hdr = f.read(hl)
    dl = struct.unpack("<I", f.read(4))[0]
    return parse_header(hdr), dl


def parse_header(b):
    d, i = {}, 0
    while i < len(b):
        n = struct.unpack_from("<I", b, i)[0]
        i += 4
        k, _, v = b[i:i + n].partition(b"=")
        d[k.decode()] = v
        i += n
    return d


def iter_records(buf):
    i = 0
    while i + 8 <= len(buf):
        hl = struct.unpack_from("<I", buf, i)[0]
        i += 4
        hdr = parse_header(buf[i:i + hl])
        i += hl
        dl = struct.unpack_from("<I", buf, i)[0]
        i += 4
        yield hdr, buf[i:i + dl]
        i += dl


def parse_pc2(m):
    i = 12
    n = struct.unpack_from("<I", m, i)[0]
    i += 4 + n  # frame_id
    height, width = struct.unpack_from("<II", m, i)
    i += 8
    nf = struct.unpack_from("<I", m, i)[0]
    i += 4
    fields = []
    for _ in range(nf):
        n = struct.unpack_from("<I", m, i)[0]
        i += 4
        name = m[i:i + n].decode()
        i += n
        off, dt, cnt = struct.unpack_from("<IBI", m, i)
        i += 9
        fields.append((name, off, dt, cnt))
    big, step, rstep = struct.unpack_from("<BII", m, i)
    i += 9
    dl = struct.unpack_from("<I", m, i)[0]
    i += 4
    return height, width, fields, step, m[i:i + dl]


def main(path):
    f = open(path, "rb")
    assert f.readline().startswith(b"#ROSBAG V2.0"), "not a ROS1 bag v2.0"
    hdr, dl = read_record(f)
    index_pos = struct.unpack("<Q", hdr["index_pos"])[0]
    nconn = struct.unpack("<I", hdr["conn_count"])[0]
    nchunk = struct.unpack("<I", hdr["chunk_count"])[0]
    if index_pos == 0:
        print("  bag is not indexed (needs 'rosbag reindex'); cannot check quickly")
        return
    f.seek(index_pos)
    conns, chunks = {}, []
    for _ in range(nconn):
        h, dl = read_record(f)
        data = f.read(dl)
        ch = parse_header(data)
        conns[struct.unpack("<I", h["conn"])[0]] = (h["topic"].decode(), ch.get("type", b"").decode())
    for _ in range(nchunk):
        h, dl = read_record(f)
        data = f.read(dl)
        pos = struct.unpack("<Q", h["chunk_pos"])[0]
        cnt = {}
        for j in range(0, len(data), 8):
            c, n = struct.unpack_from("<II", data, j)
            cnt[c] = n
        chunks.append((pos, cnt))
    total = {}
    for _, cnt in chunks:
        for c, n in cnt.items():
            total[c] = total.get(c, 0) + n
    print("  bag: %s, %d chunks" % (path.split("/")[-1], nchunk))
    for c, (tp, ty) in sorted(conns.items()):
        if tp in TOPICS:
            print("  %-18s %-32s %d msgs" % (tp, ty, total.get(c, 0)))
    for tp in TOPICS:
        if tp not in [t for t, _ in conns.values()]:
            print("  %-18s NOT IN BAG" % tp)
    cid = [c for c, (tp, ty) in conns.items() if tp == "/velodyne_points"]
    if not cid:
        if any(tp == "/velodyne_packets" for tp, _ in conns.values()):
            print("  raw packets only: converted during the run (velodyne_pointcloud adds ring and time)")
        return
    cid = cid[0]
    if conns[cid][1] != "sensor_msgs/PointCloud2":
        print("  /velodyne_points is %s, not PointCloud2" % conns[cid][1])
        return
    for pos, cnt in chunks:
        if cid not in cnt:
            continue
        f.seek(pos)
        h, dl = read_record(f)
        raw = f.read(dl)
        comp = h["compression"].decode()
        if comp == "bz2":
            raw = bz2.decompress(raw)
        elif comp == "lz4":
            try:
                import lz4.frame
                raw = lz4.frame.decompress(raw)
            except ImportError:
                print("  chunks are lz4-compressed and the python 'lz4' module is missing: pip install lz4")
                return
        elif comp != "none":
            print("  unknown compression", comp)
            return
        for mh, md in iter_records(raw):
            if mh.get("op") == b"\x02" and struct.unpack("<I", mh["conn"])[0] == cid:
                height, width, fields, step, data = parse_pc2(md)
                names = [x[0] for x in fields]
                npts = width * height
                print("  first scan: %d points, point_step %d" % (npts, step))
                print("  fields:", names)
                tf = [x for x in fields if x[0] in ("time", "t", "timestamp", "offset_time")]
                rf = [x for x in fields if x[0] == "ring"]
                if tf:
                    name, off, dt, _ = tf[0]
                    fmt, sz = DT[dt]
                    vals = [struct.unpack_from("<" + fmt, data, k * step + off)[0] for k in range(min(npts, len(data) // step))]
                    lo, hi = min(vals), max(vals)
                    print("  '%s' per-point values: min %.6g max %.6g (span %.6g)" % (name, lo, hi, hi - lo))
                    if hi - lo > 0:
                        print("  OK: per-point time present and varying")
                    else:
                        print("  PROBLEM: time field is constant in this scan - cannot deskew from it")
                elif rf:
                    name, off, dt, _ = rf[0]
                    fmt, sz = DT[dt]
                    vals = [struct.unpack_from("<" + fmt, data, k * step + off)[0] for k in range(min(npts, len(data) // step))]
                    print("  ring values: %d..%d" % (min(vals), max(vals)))
                    print("  OK: no time field, but ring present (GenZ-LIO recovers timing from ring/azimuth)")
                else:
                    print("  PROBLEM: neither time nor ring - GenZ-LIO cannot deskew this cloud")
                return
        break


if __name__ == "__main__":
    main(sys.argv[1])
