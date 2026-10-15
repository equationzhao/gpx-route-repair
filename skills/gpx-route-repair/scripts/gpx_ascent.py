#!/usr/bin/env python3
"""Inspect GPX tracks and estimate ascent with reviewed tunnel portal heights."""
import argparse
import bisect
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def local(tag):
    return tag.rsplit('}', 1)[-1]


def number(value, label):
    if isinstance(value, bool):
        raise ValueError(f'{label}: expected a finite number')
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f'{label}: expected a finite number')
    return value


def distance(a, b):
    p, q = math.radians(a[0]), math.radians(b[0])
    h = math.sin((q-p)/2)**2 + math.cos(p)*math.cos(q)*math.sin(math.radians(b[1]-a[1])/2)**2
    return 12742000*math.asin(math.sqrt(min(1.0, max(0.0, h))))


def read_gpx(path):
    root = ET.parse(path).getroot()
    segments = []
    for index, seg in enumerate(x for x in root.iter() if local(x.tag) == 'trkseg'):
        points = []
        for point in seg:
            if local(point.tag) != 'trkpt':
                continue
            lat = number(point.get('lat'), 'latitude')
            lon = number(point.get('lon'), 'longitude')
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError('Coordinates outside WGS84 bounds')
            elevation = next((x.text for x in point if local(x.tag) == 'ele'), None)
            if elevation is None:
                raise ValueError(f'Segment {index}: missing elevation; obtain elevations before estimating ascent')
            points.append((lat, lon, number(elevation, 'elevation')))
        if not points:
            raise ValueError(f'Segment {index}: empty track segment')
        distances = [0.0]
        for a, b in zip(points, points[1:]):
            distances.append(distances[-1]+distance(a, b))
        segments.append((points, distances))
    if not segments:
        raise ValueError('No trkseg/trkpt geometry; route-only GPX is not supported')
    return segments


def ascent(heights, threshold):
    raw = sum(max(0.0, b-a) for a, b in zip(heights, heights[1:]))
    if threshold == 0:
        return raw, raw
    low = high = heights[0]
    rising = False
    total = 0.0
    for z in heights[1:]:
        if not rising:
            low = min(low, z)
            if z-low >= threshold:
                high = z
                rising = True
        else:
            high = max(high, z)
            if high-z >= threshold:
                total += high-low
                low = z
                rising = False
    if rising:
        total += high-low
    return raw, total


def height_at(points, distances, s):
    i = bisect.bisect_left(distances, s)
    if i == 0 or (i < len(distances) and distances[i] == s):
        return points[i][2]
    f = (s-distances[i-1])/(distances[i]-distances[i-1])
    return points[i-1][2]+f*(points[i][2]-points[i-1][2])


def calculate(path, tunnel_specs, threshold):
    if threshold < 0 or not math.isfinite(threshold):
        raise ValueError('Threshold must be finite and nonnegative')
    segments = read_gpx(path)
    if not isinstance(tunnel_specs, list):
        raise ValueError('Tunnel JSON must be an array')
    grouped = {}
    for spec in tunnel_specs:
        if not isinstance(spec, dict):
            raise ValueError('Each tunnel must be an object')
        index = spec.get('segment')
        if type(index) is not int or not 0 <= index < len(segments):
            raise ValueError('Invalid tunnel segment index')
        for key in ('source', 'elevation_source'):
            if not isinstance(spec.get(key), str) or not spec[key].strip():
                raise ValueError(f'Tunnel {key} must describe the reviewed evidence')
        values = {k: number(spec[k], k) for k in (
            'start_m', 'end_m', 'entry_elevation_m', 'exit_elevation_m')}
        if not 0 <= values['start_m'] < values['end_m'] <= segments[index][1][-1]:
            raise ValueError('Tunnel interval outside segment, reversed, or empty')
        grouped.setdefault(index, []).append(dict(spec, **values))

    totals = dict(raw_ascent_m=0.0, filtered_ascent_m=0.0)
    corrected = dict(raw_ascent_m=0.0, filtered_ascent_m=0.0)
    audit = []
    details = []
    for index, (points, distances) in enumerate(segments):
        spans = sorted(grouped.get(index, []), key=lambda x: x['start_m'])
        if any(a['end_m'] > b['start_m'] for a, b in zip(spans, spans[1:])):
            raise ValueError('Overlapping tunnel intervals')
        for a, b in zip(spans, spans[1:]):
            if a['end_m'] == b['start_m'] and a['exit_elevation_m'] != b['entry_elevation_m']:
                raise ValueError('Adjacent tunnels have inconsistent shared portal elevation')
        profile = list(zip(distances, [p[2] for p in points]))
        for span in spans:
            start, end = span['start_m'], span['end_m']
            z0, z1 = span['entry_elevation_m'], span['exit_elevation_m']
            audit.append(dict(span,
                gpx_entry_elevation_m=height_at(points, distances, start),
                gpx_exit_elevation_m=height_at(points, distances, end),
                modeled_tunnel_ascent_m=max(0.0, z1-z0)))
            updated = []
            for s, z in profile:
                if start <= s <= end:
                    z = z0+(z1-z0)*(s-start)/(end-start)
                updated.append((s, z))
            # Explicit portals avoid overextending the correction to neighbouring samples.
            existing_distances = {s for s, _ in profile}
            if start not in existing_distances:
                updated.append((start, z0))
            if end not in existing_distances:
                updated.append((end, z1))
            profile = sorted(updated, key=lambda point: point[0])
        before = ascent([p[2] for p in points], threshold)
        after = ascent([z for _, z in profile], threshold)
        for k, v, w in zip(totals, before, after):
            totals[k] += v
            corrected[k] += w
        details.append(dict(segment=index, points=len(points), distance_m=distances[-1],
            max_point_spacing_m=max((b-a for a, b in zip(distances, distances[1:])), default=0.0)))
    return dict(file=str(Path(path).resolve()), threshold_m=threshold,
        method='Positive differences; filtered variant uses vertical reversal hysteresis per segment',
        baseline=totals, tunnel_corrected=corrected if tunnel_specs else None,
        removed_ascent_m={k: totals[k]-corrected[k] for k in totals} if tunnel_specs else None,
        tunnel_count=len(tunnel_specs), tunnels=audit, segments=details,
        distance_m=sum(x[1][-1] for x in segments),
        limitation='Portal evidence and tunnel coverage are supplied by the caller, not verified by this script')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('gpx', type=Path)
    parser.add_argument('--tunnels', type=Path)
    parser.add_argument('--threshold-m', type=float, default=3.0)
    args = parser.parse_args()
    try:
        specs = json.loads(args.tunnels.read_text()) if args.tunnels else []
        result = calculate(args.gpx, specs, args.threshold_m)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, TypeError, KeyError, OSError, ET.ParseError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
