# Tunnel elevation correction

## Identify tunnels and locate portals

Inspect `tunnel` and related attributes on the OSM ways the route actually follows. Check for missing tags using straight route sections, terrain elevation spikes, tunnel names on maps, and reference rides. A nearby `tunnel=yes` feature may be a culvert, underpass, or parallel bore; proximity alone is insufficient.

Possible data sources (check current availability, responses, and limits):

- Multiple OSM way tags: `https://api.openstreetmap.org/api/0.6/ways?ways=ID1,ID2`
- One way with node geometry: `https://api.openstreetmap.org/api/0.6/way/ID/full`
- A small map extract: `https://api.openstreetmap.org/api/0.6/map?bbox=west,south,east,north`
- Local road/tunnel queries through Overpass. If unavailable, use small OSM API extracts rather than repeatedly requesting large regions.
- Available OSM routing services, such as Valhalla `trace_route` or `trace_attributes`, for map matching. Inspect actual status, alternate fragments, and unmatched points. Fix failed requests or change sources instead of disabling TLS verification by default.

Locate each entry and exit portal and record its GPX segment and distance along that segment. Treat repeated passages through a tunnel separately. For out-and-back routes and loops, the nearest coordinate can belong to a different passage; constrain matches by travel order and direction. Keep projection errors and source notes. A nearest-point distance threshold cannot replace a review of the alignment.

## Portal elevations determine the result

A DEM lookup at a portal coordinate may still sample the hillside above it. Inspect nearby points on both sides and the elevation profile. Prefer credible barometric ride elevations, road engineering profiles, or stable road elevations outside the portal. Consider coordinate offsets, DEM resolution, and elevation datum differences.

Review portal elevations and interval coverage if a short tunnel has a large endpoint difference, an abrupt step, or a correction that removes only a meter or two while the terrain peak remains. Such a result does not establish that all tunnel artifacts were removed. Extend a contaminated transition only when supported by evidence; do not arbitrarily widen buffers to obtain a lower ascent.

When only portal elevations are known, connect them linearly by distance as an average-gradient estimate. A real tunnel can have internal crests or sags, so this is not a measured longitudinal profile. Use a known road profile when available. If portals are unreliable or tunnels may be missing, label the result an estimate corrected for identified tunnels, explain the uncertainty, and give a range where appropriate.

## Calculation method

1. Calculate distance separately for each segment of the final route. Do not accumulate distance or elevation changes across gaps between segments.
2. For confirmed intervals, insert portal boundaries and replace surface elevations using trusted endpoint heights, retaining the tunnel's actual modeled uphill gain. Elevation correction does not change route geometry.
3. Calculate before/after ascent using the same accumulation or noise-filtering method, then report the difference. A sum of positive elevation differences is sensitive to noise, point density, and joined elevation datums. Platforms also use different smoothing algorithms.
4. Inspect elevation steps, datum drift in reference rides, and artificial bumps at joins. Report geometry changes separately from tunnel elevation corrections.

The included `gpx_ascent.py` does not fill missing elevations. `raw_ascent_m` sums positive differences between successive points. `filtered_ascent_m` uses vertical reversal hysteresis: reversals below the threshold do not start a separate climb, while an established uphill trend includes its full rise. A new uphill trend must reach the threshold to be counted. This is not Strava's algorithm, and it does not detect implausible slopes or repair DEM data. At a zero threshold the two metrics agree. Interpret estimates alongside the original elevation profile.

## Helper input and output

Without `--tunnels`, the helper inspects the GPX and reports baseline ascent only. With `--tunnels`, supply a JSON array with distances and elevations in meters:

```json
[
  {
    "segment": 0,
    "start_m": 12500,
    "end_m": 13300,
    "entry_elevation_m": 210,
    "exit_elevation_m": 222,
    "source": "OSM way ID and reviewed portal positions / imagery",
    "elevation_source": "Reviewed portal heights from road profile"
  }
]
```

`segment` is zero-based in document order of `trkseg` elements. `start_m` and `end_m` are measured from the beginning of that segment in travel order. Intervals in the same segment must not overlap. Adjacent intervals must agree on their shared portal elevation. The required `source` and `elevation_source` strings record geometry and elevation evidence; the helper does not verify their content.

The helper accepts namespaced GPX and the equivalent unnamespaced track structure. A route-only file containing `rtept` must be deliberately converted to a track first; the helper does not replan the route. Missing elevations cause an error rather than being silently interpolated.

JSON output includes baseline and corrected raw/filtered ascent, their differences, a tunnel audit, segment lengths, point counts, and maximum point spacing. It reports results only; it does not write a GPX with corrected elevations. Without credible portal heights, report the limitations of the original estimate instead of treating terrain heights above the portals as a valid tunnel correction.
