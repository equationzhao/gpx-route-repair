# GPX Route Repair

An English-language agent skill for repairing cycling routes and estimating ascent after correcting terrain elevation artifacts above tunnels.

Use OpenStreetMap, public Strava segments or rides, and imagery to investigate unsupported shortcuts, missed bends, and incorrect turnarounds. Deliver a planning GPX for import into Strava or GPX Studio, with the evidence and remaining uncertainty explained.

## Install

With the [skills CLI](https://skills.sh/):

```bash
npx skills add equationzhao/gpx-route-repair
```

Select your agent when prompted. For manual installation in Codex, copy the `skills/gpx-route-repair` directory into `~/.codex/skills/`, then start a new session. Other agents that support `SKILL.md` may use a different installation location.

## Use

Example requests:

> Use $gpx-route-repair to inspect this GPX for sections that do not follow roads. Use OSM, public rides or segments, and imagery as evidence. Give me a repaired GPX and identify any unresolved sections.

> Use $gpx-route-repair to estimate this route's ascent after correcting terrain elevations above tunnels. Retain the tunnels' actual uphill gain and explain the uncertainty.

> Repair this route and deliver a GPX I can import into Strava or GPX Studio. Recalculate tunnel-corrected ascent from the final route.

The agent needs file access and access to suitable map/reference sources to perform route repair. It chooses tools available in its environment; no specific MCP server or paid API is required by the skill. Some reference sources may require authentication or may be unavailable. The skill directs the agent to retain and flag unresolved sections when evidence is insufficient.

## Ascent helper

The bundled helper uses Python 3.8+ and the standard library only. From the repository root:

```bash
# Baseline ascent from a track with elevations
python3 skills/gpx-route-repair/scripts/gpx_ascent.py examples/synthetic-route.gpx

# Correction with explicitly supplied portal elevations
python3 skills/gpx-route-repair/scripts/gpx_ascent.py examples/synthetic-route.gpx \
  --tunnels examples/synthetic-tunnels.json --threshold-m 3
```

The example is entirely synthetic: it is not a real ride, road, or tunnel. It demonstrates a surface elevation spike replaced with a rising tunnel profile. Rounded results are:

| Metric | Baseline | Tunnel-corrected |
| --- | ---: | ---: |
| Sum of positive elevation differences | 85 m | 20 m |
| Ascent with a 3 m reversal threshold | 85 m | 20 m |

The modeled tunnel still rises by 5 m. Correcting its terrain artifact removes 65 m from the example's total ascent.

The helper reads GPX track segments and reviewed tunnel JSON, then prints an audit as JSON. It makes no network requests and does not modify or export a GPX. It cannot discover tunnels, establish road access, or independently verify supplied evidence. Missing elevations are rejected. See [the tunnel reference](skills/gpx-route-repair/references/tunnel-elevation.md) for the input schema and calculation method.

## Scope and limitations

- Route geometry repair is an agent-guided workflow, not an automatic map-matching program bundled with this repository.
- Tunnel correction removes false surface hills while retaining modeled tunnel ascent. Linear portal interpolation is an estimate, not a surveyed tunnel profile.
- The helper's filtering method is documented and does not reproduce Strava's proprietary ascent calculation.
- GPX format checks do not establish that a platform import succeeded. Automatic rerouting can also change repaired geometry when roads are absent from its map.
- The workflow produces route-planning files; activity synchronization and uploading fabricated rides are outside its scope.

This repository includes no personal ride files, credentials, or copied Strava activities. When using OSM or other third-party data, follow the source's attribution and usage requirements; this repository's license covers its own code and instructions.

## Repository layout

```text
skills/gpx-route-repair/
  SKILL.md                        Agent instructions
  agents/openai.yaml              Codex UI metadata
  references/tunnel-elevation.md  Portal review and calculation guidance
  scripts/gpx_ascent.py           Offline ascent helper
examples/
  synthetic-route.gpx             Artificial elevation profile
  synthetic-tunnels.json          Artificial portal data
```

## License

[MIT](LICENSE).
