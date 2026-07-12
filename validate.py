#!/usr/bin/env python3
"""Validate the compiled .mzdash against the reverse-engineered format.

1. Structural check: every node's key set (and per-type block key sets) must
   match the corresponding node type in real MOZA community dashboards.
2. Expression check: every METHOD_CHAINING chain is executed in Node.js with
   a stubbed Telemetry API across a matrix of telemetry states (live values,
   NaN "menu" state, -FLT_MAX sentinel), asserting each chain yields a
   sensible value type and never throws.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent
DASH = REPO / "dist" / "ETS2 Truck Cluster" / "ETS2 Truck Cluster.mzdash"
SAMPLES = Path(sys.argv[1]) if len(sys.argv) > 1 else None


def walk(n):
    yield n
    for c in n.get("children", []):
        yield from walk(c)


def key_profile(node):
    """Node's top-level keys plus the key sets of its nested blocks."""
    prof = {"_keys": sorted(node.keys() - {"children"})}
    for blk in ("general", "borderStyle", "effect", "text", "textEffect",
                "linearGauge", "image", "window"):
        if blk in node:
            prof[blk] = sorted(node[blk].keys())
    return prof


def structural_check(dash, sample_paths):
    ref = {}  # type -> profile from official samples
    for p in sample_paths:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        for n in walk(d):
            ref.setdefault(n["type"], key_profile(n))
    problems = []
    for n in walk(dash):
        t = n["type"]
        if t not in ref:
            problems.append(f"node {n['id']} type {t}: no reference sample")
            continue
        mine, theirs = key_profile(n), ref[t]
        for blk in theirs:
            if blk not in mine:
                problems.append(f"node {n['id']} ({t}): missing block {blk}")
            elif mine[blk] != theirs[blk]:
                extra = set(mine[blk]) - set(theirs[blk])
                missing = set(theirs[blk]) - set(mine[blk])
                if extra or missing:
                    problems.append(
                        f"node {n['id']} ({t}) block {blk}: "
                        f"extra={sorted(extra)} missing={sorted(missing)}")
    return problems


JS_HARNESS = r"""
const [,, exprFile] = process.argv;
const chains = JSON.parse(require('fs').readFileSync(exprFile, 'utf8'));

// Telemetry stub states: name -> value provider
const NEG_FLT_MAX = -3.4028234e+38;
const LIVE = {
  Gear: 9, SpeedKmh: 79, SpeedMph: 49, Rpm: 1250, MaxRpm: 2500,
  CarSettings_CurrentDisplayedRPMPercent: 48, FuelRemainder: 64, Fuel: 448,
  FuelRange: 1470, CruiseControl: 80, CruiseControlMph: 50,
  NavigationSpeedLimit: 80, ParkingBrake: 0, RetarderLevel: 0,
  LBlinker: 0, RBlinker: 0, HazardWarning: 0, LowBeamLight: 1,
  HighBeamLight: 0, AirPressure: 120, AirPressWarning: 0,
  AirPressEmergency: 0, BatteryWarningVolt: 0, WaterTemp: 86,
  WaterTempWarning: 0, OilPressure: 60, EngineDamage: 2, GearBoxDamage: 1,
  Odometer: 182432, EngineStarted: 1, EngineBrake: 0, CargoDamage: 0.02,
};
const states = {
  live: (ch) => (ch in LIVE ? LIVE[ch] : 0),
  reverse: (ch) => (ch === 'Gear' ? -1 : states.live(ch)),
  neutral: (ch) => (ch === 'Gear' ? 0 : states.live(ch)),
  menu_nan: () => NaN,
  menu_undef: () => undefined,
  sentinel: () => NEG_FLT_MAX,
  zeros: () => 0,
  extremes: (ch) => 1e9,
};

let failures = 0;
for (const [stateName, provider] of Object.entries(states)) {
  const Telemetry = {
    get(path) {
      const ch = path.replace('v1/gameData/', '');
      return { value: provider(ch) };
    },
  };
  for (const chain of chains) {
    let _result;
    for (const m of chain.methods) {
      try {
        _result = new Function('Telemetry', '_result',
                               `return (${m});`)(Telemetry, _result);
      } catch (e) {
        console.log(`FAIL [${stateName}] ${chain.where}: ${e.message}`);
        console.log(`  expr: ${m.slice(0, 120)}`);
        failures++;
        break;
      }
    }
    const t = typeof _result;
    if (!['string', 'number', 'boolean'].includes(t) || (t === 'number' && isNaN(_result))) {
      console.log(`BAD RESULT [${stateName}] ${chain.where}: ${String(_result)} (${t})`);
      failures++;
    }
    if (chain.where.endsWith('Color') || chain.where.includes('fontColor') ||
        chain.where.includes('gaugeColor')) {
      if (t !== 'string' || !/^#[0-9A-Fa-f]{6,8}$/.test(_result)) {
        console.log(`BAD COLOR [${stateName}] ${chain.where}: ${String(_result)}`);
        failures++;
      }
    }
  }
}
console.log(failures ? `${failures} expression failures` : 'all expressions OK');
process.exit(failures ? 1 : 0);
"""


def expression_check(dash):
    chains = []
    for n in walk(dash):
        for prop, b in n.get("binding", {}).items():
            assert b["type"] == "METHOD_CHAINING"
            chains.append({"where": f"node{n['id']}:{n['name']}:{prop}",
                           "methods": b["methods"]})
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(chains, f)
        expr_file = f.name
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(JS_HARNESS)
        js_file = f.name
    r = subprocess.run(["node", js_file, expr_file],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.stderr.strip():
        print(r.stderr.strip())
    return r.returncode == 0, len(chains)


def main():
    dash = json.loads(DASH.read_text(encoding="utf-8"))

    sample_dir = SAMPLES
    problems = []
    if sample_dir and sample_dir.exists():
        samples = list(sample_dir.rglob("*.mzdash"))
        print(f"structural check against {len(samples)} official samples")
        problems = structural_check(dash, samples)
        for p in problems:
            print("STRUCT:", p)
    else:
        print("(no sample dir given; skipping structural check)")

    ok, n = expression_check(dash)
    print(f"checked {n} binding chains")

    # basic invariants
    assert dash["general"]["width"] == 780 and dash["general"]["height"] == 248
    assert dash["window"]["idealDeviceInfos"][0]["productType"] == "W18 Display"
    ids = [n["id"] for n in walk(dash)]
    assert len(ids) == len(set(ids))
    assert dash["imageResources"] == []  # single-file dash, no assets needed

    if problems or not ok:
        sys.exit(1)
    print("VALIDATION PASSED")


if __name__ == "__main__":
    main()
