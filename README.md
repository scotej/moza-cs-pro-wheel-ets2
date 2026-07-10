# ETS2 Truck Cluster — MOZA CS Pro wheel display

A gauge cluster for the **MOZA CS Pro** steering wheel's built-in 2.99″ screen
(780×248, "W18 Display"), purpose-built for **Euro Truck Simulator 2**.

**→ The importable file is [`dist/ETS2 Truck Cluster/ETS2 Truck Cluster.mzdash`](dist/ETS2%20Truck%20Cluster/ETS2%20Truck%20Cluster.mzdash)**
(or grab [`dist/ETS2-Truck-Cluster.zip`](dist/ETS2-Truck-Cluster.zip)).

Normal cruising:

<img src="dist/ETS2%20Truck%20Cluster/preview-cruising.png" width="780" alt="cruising preview">

Everything shouting at once (over the speed limit, near redline, low fuel, low air
pressure, battery + coolant warnings, damage, hazards):

<img src="dist/ETS2%20Truck%20Cluster/preview-warnings.png" width="780" alt="warnings preview">

*(Previews are renders of the same layout/logic; on-wheel fonts will differ slightly.)*

## What's on screen

| Zone | Shows | Color logic |
|---|---|---|
| Top bar | RPM (rev-light scaled %) | cyan → **amber >75%** → **red >90%** |
| Under bar | numeric RPM (left), odometer (right) | gray |
| Center | **Speed** (big) + unit | white; **red when >2 km/h over the speed limit** |
| Right of speed | **Gear** in a panel | green = forward, gray = N, **amber = R** |
| Arrows | turn indicators / hazards | green, shown only while active |
| Left | Euro speed-limit sign | white disc / red ring, hidden when no limit |
| Below sign | cruise control + set speed | green when engaged, ghosted when off |
| Far right | fuel: bar, %, liters, range | green → **amber ≤20%** → **red ≤10%**; range amber <100 km |
| Bottom strip | warning lamps | see below |

Bottom lamps (ghosted dark-gray when inactive, lit when active):
**P** parking brake (red) · **AIR** air pressure (amber warn / red emergency) ·
**OIL** oil pressure low with engine running (red) · **BATT** battery voltage (red) ·
**coolant °C** (amber on warning or >105°) · **DMG** max of engine/gearbox wear
(amber >5%, red >25%) · **EB** engine brake (amber) · **RET n** retarder level (cyan) ·
**CARGO n%** cargo damage (amber, red >10%) · **BEAM** headlights (green low, blue high).

Two screens are included: **km/h** (default) and an identical **mph** variant —
assign a wheel button to screen-switch in Pit House if you want both.

## Install

1. **ETS2 telemetry plugin** (one-time): follow MOZA's official guide
   [Euro Truck Simulator 2 — MOZA Support](https://support.mozaracing.com/en/support/solutions/articles/70000627859-euro-truck-simulator-2):
   copy `ETS2SharedMemoryMapPlugin32.dll` into
   `Euro Truck Simulator 2/bin/win_x86/plugins/` and
   `ETS2SharedMemoryMapPlugin64.dll` into
   `Euro Truck Simulator 2/bin/win_x64/plugins/` (create the `plugins` folders if
   missing). ETS2 will ask to enable "Advanced SDK features" on next launch — accept.
2. **Import the dash**: MOZA Pit House → your CS Pro wheel → **Dashboards → Import**,
   select `ETS2 Truck Cluster.mzdash`, then upload it to the wheel.
3. Drive. Values appear once you're in-cab (in menus most readouts show `--` /
   stay ghosted by design).

## Customizing / rebuilding

The `.mzdash` is compiled by [`generate.py`](generate.py) (no dependencies beyond
Python 3; Pillow only if you want the preview PNGs). Tweak layout constants or
thresholds and run:

```
python3 generate.py        # writes dist/
python3 validate.py        # sanity-checks structure + runs all 72 JS bindings
```

You can also open the imported dash in Pit House's **Dash Studio** and edit it
visually — it's a normal editor-compatible file.

Reference docs produced while reverse-engineering (useful for building your own):

- [`docs/mzdash-format.md`](docs/mzdash-format.md) — the `.mzdash` JSON format
  (node skeletons, colors, bindings, device targeting), verified against five
  official MOZA Dash Community files.
- [`docs/ets2-telemetry.md`](docs/ets2-telemetry.md) — MOZA's full 455-channel
  telemetry catalog and exactly which channels ETS2 populates.

## Notes & caveats

- Telemetry expressions guard against `NaN` and MOZA's `-3.4028234e38` "no data"
  sentinel, so nothing flashes garbage in menus.
- ETS2 has no dedicated low-fuel lamp channel in MOZA's catalog; low fuel is
  derived from fuel % (≤20% amber, ≤10% red) instead.
- The turn-signal arrows use the ◀ / ▶ glyphs. If your Pit House font renders
  them as boxes, open the dash in Dash Studio and swap the two arrow Text
  elements to `<` / `>` or an image.
- Core channels (speed/gear/RPM/fuel/damage/water/oil) are confirmed in MOZA's
  official ETS2 support matrix; the truck-specific lamps (blinkers, parking
  brake, air pressure, retarder, cruise, speed limit) come from MOZA's catalog
  with SCS-SDK descriptions and are expected to work, but aren't individually
  listed in the official matrix. If one stays dark on your rig, that channel
  simply isn't being fed — the rest of the dash is unaffected.
