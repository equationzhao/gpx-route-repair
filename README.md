# GPX Route Repair

Repair cycling routes that cut across hills, miss bends, or follow the wrong road. Get a GPX for import into Strava or GPX Studio, and estimate ascent after removing false elevation spikes above tunnels.

Repairs use OpenStreetMap, public Strava segments or rides, and imagery to preserve the intended route. Sections that cannot be confirmed are flagged for review.

## Install

With the [skills CLI](https://skills.sh/):

```bash
npx skills add equationzhao/gpx-route-repair
```

Select your agent when prompted. To install manually in Codex, copy `skills/gpx-route-repair` into `~/.codex/skills/` and start a new session.

## Use

Provide a GPX file or an accessible Strava route:

> Use $gpx-route-repair to fix the sections that do not follow roads. Give me a repaired GPX and flag any unresolved sections.

> Use $gpx-route-repair to repair this route and calculate its ascent after correcting tunnel elevations.

Tunnel correction retains the tunnel's actual uphill gain. When only portal heights are available, the gradient between them is estimated; results can differ from Strava's ascent calculation.

The agent needs access to the route file and map sources. If repaired roads are missing from an editor's map, use manual drawing mode to avoid losing the repairs during automatic rerouting.

## Calculate ascent directly

The included helper requires Python 3.8+ with no additional packages. From the repository root:

```bash
# Baseline ascent from a track with elevations
python3 skills/gpx-route-repair/scripts/gpx_ascent.py examples/synthetic-route.gpx

# Correction with explicitly supplied portal elevations
python3 skills/gpx-route-repair/scripts/gpx_ascent.py examples/synthetic-route.gpx \
  --tunnels examples/synthetic-tunnels.json --threshold-m 3
```

The synthetic example reduces ascent from 85 m to 20 m while retaining a 5 m rise inside the tunnel.

For your own route, supply a GPX with elevations and reviewed tunnel intervals and portal heights. The helper prints a JSON report; it does not discover tunnels or modify the GPX. See [tunnel inputs and calculation details](skills/gpx-route-repair/references/tunnel-elevation.md).

## License

[MIT](LICENSE).
