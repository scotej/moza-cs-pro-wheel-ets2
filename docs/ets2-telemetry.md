# MOZA Pit House / Dash Studio telemetry variables — with ETS2 focus

Research date: 2026-07-10

## 1. How dashboards bind data

MOZA Dash Studio (inside Pit House) binds widget properties via the "fx" (expression) icon.
Bindings are JavaScript expressions evaluated against a `Telemetry` object:

```js
Telemetry.get('v1/gameData/Rpm').value                    // numeric value
Telemetry.get('v1/gameData/Rpm').value > 7000 ? '#FF0000' : '#808080'   // ternary for colors/visibility
```

- Only the `.value` accessor is documented by MOZA (Dash Studio tutorial).
- Full JS expressions (ternaries, arithmetic, string concat) are supported.
- Dial gauges / linear gauges / text controls all use the same binding; the Map widget auto-binds.
- Dashboards are saved as `.mzdash` files (JSON + PNG resources). The same variable paths
  ("channel URLs") are used on the wire when Pit House streams telemetry to wheel screens.

**Source (verbatim syntax):** MOZA Dash Studio tutorial,
https://support.mozaracing.com/en/support/solutions/articles/70000665526-moza-dash-studio-tutorial

## 2. Where the variable catalog comes from

The complete channel catalog lives in MOZA's `Telemetry.json` (the "B_telemetry_json" catalog that
Pit House ships). A verbatim copy (with community-verified encoding fixes) is maintained in the
open-source AZOM SimHub plugin: `Data/Telemetry.json` in https://github.com/giantorth/AZOM
(raw: https://raw.githubusercontent.com/giantorth/AZOM/main/Data/Telemetry.json).

- The copy analysed here has **455 channels**: 316 `v1/gameData/*`, 136 `v1/gameData/patch/*`,
  3 `v1/preset/*`. (AZOM's docs describe an earlier 410-channel Pit House snapshot; the extra
  entries — spotter, time-gap, vehicle-tag, EV/hybrid channels — are later Pit House additions
  carried in the AZOM copy. Treat those specific entries as "present in catalog, not
  independently re-verified against the newest Pit House".)
- Every `url`, `data_type`, `compression`, `package_level`, description and range below is
  **verbatim from that catalog file** unless explicitly marked inferred.

### Namespaces

| Namespace | Count | Meaning |
|---|---|---|
| `v1/gameData/` | 316 | Standard game telemetry (what dashboards normally read) |
| `v1/gameData/patch/` | 136 | Extended: track-map coords (`Location`, `Location_0..63`), radar/race-info (`ri0..63`), `GameName`, `TrackName`, `DisplayTrackName`, `OnTrack`, `OpponentCount`, `PlayerIndex`, `TrackPositionPercent` |
| `v1/preset/` | 3 | Wheel-internal state (`TimeStamp`, `CurrentTorque`, `SteeringWheelAngle`) — filled by wheelbase firmware, NOT sent by Pit House |

### Unit-variant path convention (verbatim)

Some channels exist in multiple unit variants selected by a suffix **inside the path string**:

- `&unit=F` → Fahrenheit (e.g. `v1/gameData/TyreTempFrontLeft&unit=F`, `v1/gameData/AirTemp&unit=F`)
- `&F` → Fahrenheit shorthand (e.g. `v1/gameData/BrakesTemperatureAvg&F`)
- `&M` → miles (e.g. `v1/gameData/SessionOdo&M`, `v1/gameData/StintOdo&M`)
- `&B` / `&kpa` → bar / kPa tyre pressure (e.g. `v1/gameData/TyrePressureFL&B`, `...&kpa`);
  the un-suffixed `TyrePressureFrontLeft` etc. are **psi**.

### Value types

`data_type` in the catalog is one of `int`, `float`, `bool`, `string`. In Dash Studio JS,
numeric channels come back as numbers, bools as 0/1 (descriptions say `1:true 0:false`),
strings as strings. The `compression` column is the wire encoding used when streaming to
wheel screens (bit-packed; see AZOM `docs/protocol/telemetry/channels.md`), and also tells you
the practical resolution/limits (e.g. `percent_1` = 0.1% steps, `float_6000_1` = 0.1 units,
`uint16_t` RPM = integer, `int30` gear = 5-bit).

### Update tiers

`package_level` is the streaming interval in ms: 30 ≈ 33 Hz (RPM, speed, gear, pedals),
500 = 2 Hz, 1000 = 1 Hz (`TimeAbsolute` only), 2000 = 0.5 Hz (lap records, wear, strings).
This governs the wheel-screen stream cadence.

## 3. Key channels cheat-sheet (all paths verbatim)

| Path | Type | Meaning / units |
|---|---|---|
| `v1/gameData/Rpm` | int | Engine RPM |
| `v1/gameData/MaxRpm` | int | Max engine RPM |
| `v1/gameData/CarSettings_CurrentDisplayedRPMPercent` | float | RPM percent 0–100 |
| `v1/gameData/SpeedKmh` / `SpeedMph` / `SpeedMs` | number | Vehicle speed in km/h, mph, m/s |
| `v1/gameData/Gear` | int | **-1 = R, 0 = N, 1–12 forward** (catalog range: `-1(R)、0(N)、1~12`) |
| `v1/gameData/CarSettings_MaxGears` | int | Max gear count |
| `v1/gameData/Throttle` / `Brake` / `Clutch` | float | Pedal positions **0–1** |
| `v1/gameData/Handbrake` | bool | Handbrake on |
| `v1/gameData/Fuel` | float | Remaining fuel (game units, ETS2: liters) |
| `v1/gameData/FuelCapacity` | float | Tank capacity |
| `v1/gameData/FuelRemainder` | int | Fuel level **percent 0–100** |
| `v1/gameData/FuelRange` | float | Estimated range with current fuel, **km** (truck-sim wording) |
| `v1/gameData/InstantConsumption_L100KM` / `_MPG_UK` / `_MPG_US` | float | Instant fuel consumption |
| `v1/gameData/CruiseControl` | float | Cruise-control set speed in **km/h**, 0 = CC off |
| `v1/gameData/CruiseControlMph` | float | Cruise set speed in mph (catalog desc mistakenly says m/s) |
| `v1/gameData/CruiseControlMs` | float | Cruise set speed in m/s |
| `v1/gameData/NavigationSpeedLimit` | float | Truck route-advisor speed limit, **m/s** (verbatim: "In m/s") |
| `v1/gameData/JobSpeedLimitValue` | float | Job speed-limit setting |
| `v1/gameData/RetarderLevel` | int | Current retarder level |
| `v1/gameData/EngineBrake` | bool | Engine/motor brake enabled |
| `v1/gameData/ParkingBrake` | bool | Parking brake on |
| `v1/gameData/LBlinker` / `RBlinker` | bool | Left/right turn indicator on (blinking state) |
| `v1/gameData/HazardWarning` | bool | Hazards on |
| `v1/gameData/LowBeamLight` / `HighBeamLight` | bool | Low/high beam on |
| `v1/gameData/ParkingLight` / `BeaconLight` / `FrontAuxLight` / `RoofAuxLight` / `ReverseLight` / `RainLight` | bool | Other lights |
| `v1/gameData/Wipers` | bool; `WiperClass` int | Wipers on / wiper stage |
| `v1/gameData/AirPressure` | float | Brake air-tank pressure |
| `v1/gameData/AirPressWarning` / `AirPressEmergency` | bool | Air pressure warning / emergency-brake threshold |
| `v1/gameData/BatteryWarningVolt` | bool | Battery voltage / not-charging warning |
| `v1/gameData/WaterTemp` | float; `WaterTempWarning` bool | Coolant temp / warning |
| `v1/gameData/OilPressure` | float | Oil pressure |
| `v1/gameData/FuelTemp` | float | Catalog name is FuelTemp but description says **"Oil Temperature"** (mapped to oil temp in truck sims) |
| `v1/gameData/EngineDamage` | int | Engine wear percent 0–100 (catalog `name`: EngineWear) |
| `v1/gameData/GearBoxDamage` | int | Transmission wear percent 0–100 |
| `v1/gameData/CargoDamage` | float | Cargo damage 0.0–1.0 |
| `v1/gameData/Odometer` | float | Odometer, **km** |
| `v1/gameData/InCome` | int | Job income |
| `v1/gameData/NextRestStop` | int | Minutes to next rest stop |
| `v1/gameData/DestinationCity` | string | Job destination city |
| `v1/gameData/EngineEnabled` / `EngineStarted` / `EngineIgnition` | bool | Engine running / started / ignition |
| `v1/gameData/TimeAbsolute` | int | Absolute in-game time |
| `v1/gameData/CarId` / `CarModel` | string | Vehicle name / model (ETS2: truck) |
| `v1/gameData/patch/GameName` | string | Short game name (dashboards branch on it) |

Racing-only channels (laps, sectors, flags, DRS/ERS, tyre temps/pressures, spotter, etc.) are in
the full table below; they exist in the catalog but are not fed by ETS2.

## 4. ETS2 (Euro Truck Simulator 2) specifics

### Required setup (verbatim from MOZA support)

ETS2 telemetry requires MOZA's copy of the SCS shared-memory plugin:

1. Copy `ETS2SharedMemoryMapPlugin32.dll` → `Euro Truck Simulator 2/bin/win_x86/plugins`
2. Copy `ETS2SharedMemoryMapPlugin64.dll` → `Euro Truck Simulator 2/bin/win_x64/plugins`
   (create the `plugins` folders if missing; ETS2 shows an "SDK activated" OK prompt each launch)
- Downloads: `https://image.gudsen.com/mozaracing/game%20configuration/Euro%20Truck%20Simulator%202/ETS2SharedMemoryMapPlugin64.dll` (and ...32.dll)
- Source: https://support.mozaracing.com/en/support/solutions/articles/70000627859-euro-truck-simulator-2

This DLL is the SimHub author's fork of nlhans' `ets2-sdk-plugin`
(https://github.com/SHWotever/ets2-sdk-plugin), which exposes the SCS SDK data as a
memory-mapped struct. So Pit House sees exactly the fields in that struct (see §4.4).
Same plugin works for ATS.

### 4.1 Officially supported ETS2 items (verbatim from MOZA's Digital Dash support matrix)

Source: https://support.mozaracing.com/en/support/solutions/articles/70000627978-digital-dash-telemetry-support
(HTML table parsed directly; ETS2 and ATS rows are identical — 46 items marked "●").
Matrix uses catalog short names; mapped here to paths:

MaxRpm, SpeedMph, SpeedKmh, SpeedMs, Rpm, Gear, Throttle, Brake, Clutch,
FuelRemain→`FuelRemainder`, BrakeTempFL/FR/RL/RR (+`&unit=F` variants) →`BrakeTempFrontLeft`...,
FuelTemp, TyreWearFL/FR/RL/RR→`TyreWearFrontLeft`..., EngineWear→`EngineDamage`,
GearBoxWear→`GearBoxDamage`, FuelCapacity, EngineIgnition, ReverseLight,
AccX/Y/Z→`AccelerationX/Y/Z`, Pitch, Roll, WaterTemperature→`WaterTemp`, OilPressure, Fuel,
CarId, CarCoordinates01/02/03, CarSettings_MaxGears, EngineStarted, CarModel,
CarSettings_CurrentDisplayedRPMPercent, Gamename→`patch/GameName`, Location→`patch/Location`.

Explicitly NOT supported for ETS2 in that matrix (98 items): all lap/sector/position timing,
flags, DRS/ERS/ABS/TC/ECU/BrakeBias/Boost, tyre temps & pressures, TrackTemp/AirTemp,
IsInPit/PitLane/PitLimiter, SessionTimeLeft, TrackLength, TrackId, PlayerName,
TrackPositionPercent, OpponentCount, etc.

**Caveat:** that matrix is for the wheel's built-in Digital Dash and predates MOZA's
truck-wheel (TSW) era — it has no rows at all for the truck-specific channels below.

### 4.2 Truck-specific channels (in the catalog, added for ETS2/ATS)

These channels' catalog descriptions are copied almost verbatim from the SCS SDK docs
("Pressure Of The Air In The Tank Below Which The Emergency Brakes Activate", "Estimated
Range Of Truck ... In km", "The Value Of Truck's Navigation Speed Limit (In m/s)"), i.e. they
exist specifically for ETS2/ATS. Expect them to carry data in ETS2 (inference, strong):

`AirPressure`, `AirPressWarning`, `AirPressEmergency`, `BatteryWarningVolt`, `BeaconLight`,
`CargoDamage`, `CruiseControl`, `CruiseControlMph`, `CruiseControlMs`, `DestinationCity`,
`EngineBrake`, `EngineEnabled`, `FrontAuxLight`, `RoofAuxLight`, `FuelRange`,
`HazardWarning`, `HighBeamLight`, `LowBeamLight`, `InCome`, `InstantConsumption_L100KM`,
`InstantConsumption_MPG_UK`, `InstantConsumption_MPG_US`, `JobSpeedLimitValue`, `LBlinker`,
`RBlinker`, `NavigationSpeedLimit`, `NextRestStop`, `Odometer`, `ParkingBrake`,
`ParkingLight`, `RetarderLevel`, `WaterTempWarning`, `Wipers`, `WiperClass`, `TimeAbsolute`.

Wire-level confirmation (AZOM USB captures of Pit House, `Telemetry/Protocol/CompressionTable.cs`
comments): Pit House emits `NavigationSpeedLimit` (compression 0x10, ×100 scale) and
`TimeAbsolute` (32-bit) **in truck-sim (ETS2/ATS) tier-defs** — proof the truck channel set is
actively streamed for these games.

### 4.3 Value conventions relevant to ETS2

- **Gear**: number; `-1` = reverse, `0` = neutral, `1..N` forward (catalog documents 1–12; the
  wheel-stream encoding `int30` is 5-bit, reverse sent as raw 31). ETS2 trucks with >12 gears may
  clamp on wheel screens; whether Pit House uses SCS `gear` or `gearDashboard` (display gear with
  range logic) is not documented. In expressions:
  `Telemetry.get('v1/gameData/Gear').value == -1 ? 'R' : (v == 0 ? 'N' : v)`.
- **Speed**: SCS SDK delivers m/s; MOZA precomputes `SpeedKmh` / `SpeedMph` / `SpeedMs` — no
  manual conversion needed. `NavigationSpeedLimit` stays in **m/s** (×3.6 for km/h).
- **Cruise control**: `CruiseControl` km/h, `CruiseControlMs` m/s, `CruiseControlMph` mph;
  value 0 ⇒ cruise off (usable as a boolean).
- **Warning lamps available**: air pressure (warning + emergency), battery voltage, water temp.
- **Warning lamps NOT in the catalog** although ETS2's plugin exposes them: `adblueWarning`
  (+ AdBlue level), `oilPressureWarning`, `fuelWarning` (low-fuel lamp) — no `v1/gameData` path
  exists for these, so a low-fuel light must be derived, e.g.
  `Telemetry.get('v1/gameData/FuelRemainder').value < 10`.
- **Also missing** vs the SCS struct: `routeDistance` / `routeTime` (navigation ETA — only
  `NextRestStop` minutes exist), trailer data (attached/mass/name), `batteryVoltage` numeric,
  wear for cabin/chassis/wheels/trailer, truck make/brand strings.
- **Damage**: `EngineDamage`/`GearBoxDamage` are 0–100 percent (SCS `wearEngine`/`wearTransmission`
  ×100); `CargoDamage` is 0.0–1.0.
- ETS2 has no laps/sectors/flags — those channels read 0/default; `CurrentLapTime`-style timing
  and tyre temp/pressure channels are unsupported per MOZA's matrix.

### 4.4 What the ETS2 plugin itself exposes (upper bound of available data)

From `ets2-telemetry-common.hpp` in SHWotever/ets2-sdk-plugin (the DLL MOZA rehosts):
engine on/electric on, trailer attached, speed (m/s), acceleration XYZ, coordinates XYZ,
rotation XYZ, gear / #gears / #reverse gears / gearDashboard / gear ranges & ratios, RPM, max
RPM, fuel, fuel capacity, fuel avg consumption, fuel range, user & game inputs (steer, throttle,
brake, clutch), truck & trailer weight, trailer id/name/mass, job income / delivery time /
source & destination city+company, retarder level, shifter slot/toggle, cruise control
on + set speed (m/s), wipers, park brake, motor brake, blinker L/R active+on, lights (parking,
low beam, high beam, aux front, aux roof, beacon, brake, reverse), warnings (battery voltage,
air pressure, air pressure emergency, adblue, oil pressure, water temperature, low fuel),
air pressure, brake temperature, adblue level/consumption, oil pressure, oil temperature,
water temperature, battery voltage, dashboard backlight, wear (engine, transmission, cabin,
chassis, wheels, trailer), odometer, navigation speed limit / route distance / route time,
truck make/model, onJob/jobFinished.

## 5. Full catalog tables

See `catalog_tables.md` in this directory for the complete 455-channel dump
(all paths verbatim, with type / wire encoding / tier / description / range).
Raw catalog: `Telemetry.json`; flat TSV: `catalog.tsv`.

## 6. Sources

1. AZOM (unofficial open-source MOZA protocol implementation / SimHub plugin) — main source:
   - https://github.com/giantorth/AZOM
   - `Data/Telemetry.json` (channel catalog, verbatim paths): https://raw.githubusercontent.com/giantorth/AZOM/main/Data/Telemetry.json
   - `docs/protocol/telemetry/channels.md` (encodings, namespaces, tiers)
   - `docs/protocol/telemetry/tiers.md` (package_level cadences)
   - `Telemetry/Protocol/CompressionTable.cs` (wire-capture evidence of ETS2/ATS truck tier-defs)
2. MOZA support:
   - Dash Studio tutorial (Telemetry.get syntax): https://support.mozaracing.com/en/support/solutions/articles/70000665526-moza-dash-studio-tutorial
   - Digital Dash Telemetry Support matrix (per-game): https://support.mozaracing.com/en/support/solutions/articles/70000627978-digital-dash-telemetry-support
   - ETS2 setup: https://support.mozaracing.com/en/support/solutions/articles/70000627859-euro-truck-simulator-2
3. ETS2 plugin struct: https://github.com/SHWotever/ets2-sdk-plugin (`ets2-telemetry/inc/ets2-telemetry-common.hpp`) — fork of https://github.com/nlhans/ets2-sdk-plugin
## Full channel catalog — `v1/gameData/*` (316 channels)

| Path | Type | Wire encoding | Tier (ms) | Description | Range |
|---|---|---|---|---|---|
| `v1/gameData/ABSActive` | float | bool | 30 | ABS Activation | 0:triggered 1:untriggered |
| `v1/gameData/ABSLevel` | float | level_1 | 30 | ABS Value | 0:off >=1:The higher the value, the greater the degree of control intervention |
| `v1/gameData/ABSMaxLevel` | int | uint8 | 500 | Maximum adjustable ABS level | >=0 |
| `v1/gameData/AccelerationX` | float | float | 30 | Acceleration X | -∞~+∞ |
| `v1/gameData/AccelerationY` | float | float | 30 | Acceleration Y | -∞~+∞ |
| `v1/gameData/AccelerationZ` | float | float | 30 | Acceleration Z | -∞~+∞ |
| `v1/gameData/AirPressEmergency` | bool | bool | 30 | Pressure Of The Air In The Tank Below Which The Emergency Brakes Activate. | 1:true 0:false |
| `v1/gameData/AirPressure` | float | float | 30 | AirPressure | >0 |
| `v1/gameData/AirPressWarning` | bool | bool | 500 | Pressure Of The Air In The Tank Below Which The Warning Activates. | 1:true 0:false |
| `v1/gameData/AirTemp` | float | tyre_temp_1 | 2000 | Air Temperature | 0~255 |
| `v1/gameData/AirTemp&unit=F` | float | track_temp_1 | 2000 | Air Temperature(F°) | 0~255 |
| `v1/gameData/AllTimeBest` | float | float | 500 | AllTimeBest | >0 |
| `v1/gameData/AttackMode` | int | uint16_t | 30 | Current attack mode state (e.g. Formula E) | >=0 |
| `v1/gameData/BatteryPercent` | float | float | 30 | Battery charge percentage for hybrid/electric vehicles | 0~100 |
| `v1/gameData/BatteryWarningVolt` | bool | bool | 30 | Is The Battery Voltage/Not Charging Warning Active | 1:true 0:false |
| `v1/gameData/BeaconLight` | bool | bool | 30 | Are The Beacon Lights Enabled | 1:true 0:false |
| `v1/gameData/BestLapTime` | float | float | 2000 | Personal Best Lap Time | >=0 |
| `v1/gameData/BlueFlag` | int | bool | 30 | Blue Flag Status | 1:true 0:false |
| `v1/gameData/Boost` | float | percent_1 | 30 | Turbocharging | 0~100 |
| `v1/gameData/Brake` | float | float_001 | 30 | Brake Pedal Position | 0~1 |
| `v1/gameData/BrakeBias` | float | float | 30 | Brake Bias | 0~100 |
| `v1/gameData/BrakeLockupFrontLeft` | bool | bool | 500 | BrakeLockupFrontLeft | 1:true 0:false |
| `v1/gameData/BrakeLockupFrontRight` | bool | bool | 500 | BrakeLockupFrontRight | 1:true 0:false |
| `v1/gameData/BrakeLockupRearLeft` | bool | bool | 500 | BrakeLockupRearLeft | 1:true 0:false |
| `v1/gameData/BrakeLockupRearRight` | bool | bool | 500 | BrakeLockupRearRight | 1:true 0:false |
| `v1/gameData/BrakesTemperatureAvg` | float | brake_temp_1 | 500 | BrakesTemperatureAvg | 0~65535 |
| `v1/gameData/BrakesTemperatureAvg&F` | float | brake_temp_1 | 500 | BrakesTemperatureAvg&F | 0~65535 |
| `v1/gameData/BrakesTemperatureMax` | float | brake_temp_1 | 500 | BrakesTemperatureMax | 0~65535 |
| `v1/gameData/BrakesTemperatureMax&F` | float | brake_temp_1 | 500 | BrakesTemperatureMax&F | 0~65535 |
| `v1/gameData/BrakesTemperatureMin` | float | brake_temp_1 | 500 | BrakesTemperatureMin | 0~65535 |
| `v1/gameData/BrakesTemperatureMin&F` | float | brake_temp_1 | 500 | BrakesTemperatureMin&F | 0~65535 |
| `v1/gameData/BrakeTempFrontLeft` | float | brake_temp_1 | 2000 | Left Front Brake Pad Temperature | 0~65535 |
| `v1/gameData/BrakeTempFrontLeft&unit=F` | float | brake_temp_1 | 2000 | Left Front Brake Pad Temperature(F°) | 0~65535 |
| `v1/gameData/BrakeTempFrontRight` | float | brake_temp_1 | 2000 | Right Front Brake Pad Temperature | 0~65535 |
| `v1/gameData/BrakeTempFrontRight&unit=F` | float | brake_temp_1 | 2000 | Right Front Brake Pad Temperature(F°) | 0~65535 |
| `v1/gameData/BrakeTempRearLeft` | float | brake_temp_1 | 2000 | Left Rear Brake Pad Temperature | 0~65535 |
| `v1/gameData/BrakeTempRearLeft&unit=F` | float | brake_temp_1 | 2000 | Left Rear Brake Pad Temperature(F°) | 0~65535 |
| `v1/gameData/BrakeTempRearRight` | float | brake_temp_1 | 2000 | Right Rear Brake Pad Temperature | 0~65535 |
| `v1/gameData/BrakeTempRearRight&unit=F` | float | brake_temp_1 | 2000 | Right Rear Brake Pad Temperature(F°) | 0~65535 |
| `v1/gameData/CarClass` | string | string | 2000 | CarClass | 1~100 character |
| `v1/gameData/CarCoordinates01` | float | float | 30 | Car Position_X | None |
| `v1/gameData/CarCoordinates02` | float | float | 30 | Car Position_Y | None |
| `v1/gameData/CarCoordinates03` | float | float | 30 | Car Position_Z | None |
| `v1/gameData/CarDamage1` | float | float | 2000 | CarDamage1 | >=0 |
| `v1/gameData/CarDamage2` | float | float | 2000 | CarDamage2 | >=0 |
| `v1/gameData/CarDamage3` | float | float | 2000 | CarDamage3 | >=0 |
| `v1/gameData/CarDamage4` | float | float | 2000 | CarDamage4 | >=0 |
| `v1/gameData/CarDamage5` | float | float | 2000 | CarDamage5 | >=0 |
| `v1/gameData/CarDamagesAvg` | float | float | 2000 | CarDamagesAvg | >=0 |
| `v1/gameData/CarDamagesMax` | float | float | 2000 | CarDamagesMax | >=0 |
| `v1/gameData/CarDamagesMin` | float | float | 2000 | CarDamagesMin | >=0 |
| `v1/gameData/CargoDamage` | float | float | 30 | CargoDamage | 0.0-1.0 |
| `v1/gameData/CarId` | string | string | 2000 | Car Name | 1~100 character |
| `v1/gameData/CarModel` | string | string | 2000 | Car Model | 1~100 character |
| `v1/gameData/CarSettings_CurrentDisplayedRPMPercent` | float | percent_1 | 30 | Current Engine RPM Percentage | 0~100 |
| `v1/gameData/CarSettings_MaxGears` | int | uint8_t | 2000 | Maximum Gear Count | >0 |
| `v1/gameData/CloudCoverage` | int | uint8 | 30 | Current weather cloud coverage level | >=0 |
| `v1/gameData/Clutch` | float | float_001 | 30 | Clutch Pedal Position | 0~1 |
| `v1/gameData/CompletedLaps` | int | uint8_t | 2000 | Laps Completed | >=0 |
| `v1/gameData/CruiseControl` | float | float | 30 | Speed Selected For The Cruise Control In Km/h Is Zero If Cruise Control Is Disabled. | >0 |
| `v1/gameData/CruiseControlMph` | float | float | 30 | Speed Selected For The Cruise Control In m/s Is Zero If Cruise Control Is Disabled. | >0 |
| `v1/gameData/CruiseControlMs` | float | float | 30 | Speed Selected For The Cruise Control In m/s Is Zero If Cruise Control Is Disabled. | >0 |
| `v1/gameData/CurrentCarCount` | int | int8_t | 2000 | Number Of Entries | 1~255 |
| `v1/gameData/CurrentLap` | int | int8_t | 500 | Current Lap +1 | 1~255 |
| `v1/gameData/CurrentLapCount` | int | uint8_t | 2000 | Total Laps | 0~255 |
| `v1/gameData/CurrentLapTime` | float | float | 30 | Elapsed Time In Current Lap | >=0 |
| `v1/gameData/CurrentPos` | int | int8_t | 500 | Current Position | >0 |
| `v1/gameData/DestinationCity` | string | string | 2000 | DestinationCity | 1~100 character |
| `v1/gameData/DRSAllowed` | int | bool | 30 | Variable Aerodynamic System Enabled | 1:true 0:false |
| `v1/gameData/DRSAvailable` | int | bool | 30 | DRS Available | 0:available 1:unavailable |
| `v1/gameData/DrsState` | int | bool | 30 | DRS Activation | 0:off 1:on |
| `v1/gameData/ECUMap` | float | uint8 | 30 | Each Level Corresponds To Different Speed, Fuel Consumption, And Throttle | 1~8 |
| `v1/gameData/EngineBrake` | bool | bool | 30 | Is The Engine Brake Enabled | 1:true 0:false |
| `v1/gameData/EngineDamage` | int | percent_1 | 2000 | Engine Damage | 0~100 |
| `v1/gameData/EngineEnabled` | bool | bool | 30 | Is The Engine Enabled | 1:true 0:false |
| `v1/gameData/EngineIgnition` | bool | bool | 30 | Engine Ignition Status | true false |
| `v1/gameData/EngineMapMax` | int | uint8 | 500 | Maximum adjustable engine map level | >=0 |
| `v1/gameData/EngineStarted` | int | bool | 30 | Engine Start Status | 1:true 0:false |
| `v1/gameData/EngineTorque` | float | float | 30 | The Torque Output of the Engine | >=0 |
| `v1/gameData/ErsDeployedThisLap` | int | percent_1 | 2000 | ERS Energy Transfer Percentage | 0~100 |
| `v1/gameData/ErsHarvestedThisLap` | int | percent_1 | 2000 | ERS Energy Recovery (MGU-H & MGU-K) Percentage | 0~100 |
| `v1/gameData/ERSMax` | float | float | 30 | Energy Recovery System (ERS) Maximum Output | >=0 |
| `v1/gameData/ERSPercent` | float | percent_1 | 30 | Energy Recovery System (ERS) Energy Level Percentage | 0~100 |
| `v1/gameData/ErsState` | int | uint3 | 30 | Energy Recovery System Deployment Mode | 0:无 1:中度 2:最快圈速 3:超车 |
| `v1/gameData/ERSStored` | float | percent_1 | 30 | Energy Recovery System Storage | -∞~+∞ |
| `v1/gameData/ErsStoreEnergy` | int | percent_1 | 2000 | ERS Charge Percentage | 0~100 |
| `v1/gameData/EstimatedLapTime` | float | float | 30 | Estimated Lap Time | >=0 |
| `v1/gameData/EVMode` | int | uint8 | 30 | Current electric boost motor state | >=0 |
| `v1/gameData/Flag_Black` | int | bool | 30 | Black Flag Status | 1:true 0:false |
| `v1/gameData/Flag_Checkered` | bool | bool | 30 | In Racing or Simulation, the Checkered Flag is Waved When A Car Crosses the Finish Line on the Final Lap, Signaling the End of the Race | 1:true 0:false |
| `v1/gameData/Flag_Name` | string | string | 500 | FlagName | 1~100 character |
| `v1/gameData/Flag_Orange` | bool | bool | 30 | OrangeFlag | 1:true 0:false |
| `v1/gameData/FrontARB` | float | float | 500 | Front Anti-Roll Bar | >=0 |
| `v1/gameData/FrontARBMax` | int | uint8 | 500 | Maximum adjustable front anti-roll bar level | >=0 |
| `v1/gameData/FrontAuxLight` | bool | bool | 30 | Are The Auxiliary Front Lights Active | 1:true 0:false |
| `v1/gameData/FrontLeftWingDamage` | int | percent_1 | 2000 | Left Front Wing Damage | 0~100 |
| `v1/gameData/FrontRightWingDamage` | int | percent_1 | 2000 | Right Front Wing Damage | 0~100 |
| `v1/gameData/Fuel` | float | float | 500 | Remaining Fuel | >=0 |
| `v1/gameData/FuelCapacity` | float | float_6000_1 | 2000 | Fuel Capacity | >0 |
| `v1/gameData/FuelConsumeLap` | float | float | 30 | FuelConsumeLap | >=0 |
| `v1/gameData/FuelConsumptionClass` | float | uint15 | 2000 | Fuel Consumption Rate | >=0 |
| `v1/gameData/FuelLaps` | float | int8_t | 500 | Laps Remaining | Float |
| `v1/gameData/FuelRange` | float | float | 500 | Estimated Range Of Truck With Current Amount Of Fuel In km | >0 |
| `v1/gameData/FuelRemainder` | int | percent_1 | 500 | Fuel Level Percentage | 0~100 |
| `v1/gameData/FuelRemains` | float | float_6000_1 | 500 | FuelRemains | >0 |
| `v1/gameData/FuelSurplusLaps` | float | uint8_t | 500 | Laps In Reserve | Float |
| `v1/gameData/FuelTemp` | float | track_temp_1 | 500 | Oil Temperature | 0~255 |
| `v1/gameData/FuelUsed` | float | float_600_2 | 500 | FuelUsed | >0 |
| `v1/gameData/GAP` | float | float | 30 | Delta Time | -∞~+∞ |
| `v1/gameData/Gear` | int | int30 | 30 | Current Gear | -1(R)、0(N)、1~12 |
| `v1/gameData/GearBoxDamage` | int | percent_1 | 2000 | Gearbox Damage | 0~100 |
| `v1/gameData/GlobalAccelerationG` | float | float | 30 | Global Acceleration | -∞~+∞ |
| `v1/gameData/GreenFlag` | int | bool | 30 | Yellow Flag Status | 1:true 0:false |
| `v1/gameData/Handbrake` | bool | bool | 30 | Handbrake | 1:true 0:false |
| `v1/gameData/HazardWarning` | bool | bool | 30 | Are The Hazard Warning Light Enabled | 1:true 0:false |
| `v1/gameData/Heading` | float | tyre_temp_1 | 30 | Yaw Rate | >=0 |
| `v1/gameData/HighBeamLight` | bool | bool | 30 | High Beam Light On | 1:true 0:false |
| `v1/gameData/InCome` | int | int32_t | 30 | Task Income | 0 ~ +∞ |
| `v1/gameData/InstantConsumption_L100KM` | float | float_600_2 | 30 | InstantConsumption_L100KM | >=0 |
| `v1/gameData/InstantConsumption_MPG_UK` | float | float_600_2 | 30 | InstantConsumption_MPG_UK | >=0 |
| `v1/gameData/InstantConsumption_MPG_US` | float | float_600_2 | 30 | InstantConsumption_MPG_US | >=0 |
| `v1/gameData/IsFixedSetup` | bool | bool | 30 | Whether the current session uses fixed vehicle setup | 1:true 0:false |
| `v1/gameData/IsInPit` | int | bool | 30 | Car Repair Status | 1:true 0:false |
| `v1/gameData/IsInPitSince` | bool | bool | 30 | IsInPitSince | 1:true 0:false |
| `v1/gameData/IsSessionRestart` | bool | bool | 30 | IsSessionRestart | 1:true 0:false |
| `v1/gameData/JobSpeedLimitValue` | float | float | 30 | Task Speed Limit Setting | >0 |
| `v1/gameData/LapInvalidated` | bool | bool | 500 | Is Invalid Lap | 1:true 0:false |
| `v1/gameData/LastLapTime` | float | float | 2000 | Last Lap Time | >=0 |
| `v1/gameData/LastPitStopDuration` | float | float | 500 | LastPitStopDuration | >=0 |
| `v1/gameData/LastSectorTime` | float | float | 30 | LastSectorTime | >=0 |
| `v1/gameData/LastSectorTimeAnyLap` | float | float | 500 | The Most Recent Segment Time Record Among All Completed Laps | >=0 |
| `v1/gameData/LBlinker` | bool | bool | 30 | Is Blinker Left On | 1:true 0:false |
| `v1/gameData/LiftAndCoastProgress` | int | uint8 | 30 | Lift-and-Coast LED progress indicator | >=0 |
| `v1/gameData/LowBeamLight` | bool | bool | 30 | Low Beam Light On | 1:true 0:false |
| `v1/gameData/MapAllowed` | bool | bool | 30 | MapAllowed | 1:true 0:false |
| `v1/gameData/MaxEngineTorque` | float | float | 2000 | MaxEngineTorque | >=0 |
| `v1/gameData/MaxRpm` | int | uint16_t | 2000 | Maximum Engine RPM | >0 |
| `v1/gameData/MaxSpeedKmh` | float | float_600_2 | 2000 | MaxSpeedKmh | >=0 |
| `v1/gameData/MaxSpeedMph` | float | float_600_2 | 2000 | MaxSpeedMph | >=0 |
| `v1/gameData/MaxTurbo` | float | float | 2000 | MaxTurbo | >=0 |
| `v1/gameData/Migration` | int | uint8 | 30 | Current fuel migration (fuel flow) setting level | >=0 |
| `v1/gameData/MigrationMax` | int | uint8 | 500 | Maximum adjustable fuel migration level | >=0 |
| `v1/gameData/NavigationSpeedLimit` | float | nav_speed_limit | 500 | The Value Of Truck's Navigation Speed Limit (In m/s). | >0 |
| `v1/gameData/NextRestStop` | int | int32_t | 30 | NextRestStop(minutes) | 0 ~ +∞ |
| `v1/gameData/Odometer` | float | float | 500 | The Value Of The Odometer In km. | >0 |
| `v1/gameData/OilPressure` | float | oil_pressure_1 | 2000 | Oil Pressure | >0 |
| `v1/gameData/OrientationPitchAcceleration` | float | float_600_2 | 30 | OrientationPitchAcceleration | >=0 |
| `v1/gameData/OrientationRollAcceleration` | float | float_600_2 | 30 | OrientationRollAcceleration | >=0 |
| `v1/gameData/OrientationYawAcceleration` | float | float_600_2 | 30 | OrientationYawAcceleration | >=0 |
| `v1/gameData/OrientationYawVelocity` | float | float_600_2 | 30 | OrientationYawAcceleration | >=0 |
| `v1/gameData/PacketTime` | string | string | 500 | Packet Time | 1~100 character |
| `v1/gameData/ParkingBrake` | bool | bool | 30 | Is The Parking Brake Enabled | 1:true 0:false |
| `v1/gameData/ParkingLight` | bool | bool | 30 | Are The Parking Lights Enabled | 1:true 0:false |
| `v1/gameData/Pitch` | float | float | 30 | Pitch Rate | >=0 |
| `v1/gameData/PitLane` | int | bool | 30 | Pit Lane Status | 1:true 0:false |
| `v1/gameData/PitLimiter` | int | bool | 30 | Pit Lane Speed Limiter Status | 1:true 0:false |
| `v1/gameData/PlayerClassOpponentsCount` | int | uint8_t | 30 | PlayerClassOpponentsCount | >=0 |
| `v1/gameData/PlayerName` | string | string | 2000 | Player Name | 1~100 character |
| `v1/gameData/PushToPassActive` | bool | bool | 30 | PushToPassActive | 1:true 0:false |
| `v1/gameData/RainLight` | bool | bool | 30 | Rain Lights On | 1:true 0:false |
| `v1/gameData/RBlinker` | bool | bool | 30 | Is Blinker Right On | 1:true 0:false |
| `v1/gameData/RearARB` | float | float | 500 | Rear Anti-Roll Bar | >=0 |
| `v1/gameData/RearARBMax` | int | uint8 | 500 | Maximum adjustable rear anti-roll bar level | >=0 |
| `v1/gameData/RearWingDamage` | int | percent_1 | 2000 | Rear Wing Damage | 0~100 |
| `v1/gameData/RedFlag` | int | bool | 30 | Red Flag Status | 1:true 0:false |
| `v1/gameData/Regen` | float | float | 30 | Current regenerative braking setting | >=0 |
| `v1/gameData/ReplayMode` | string | string | 2000 | Replay Mode | 1~100 character |
| `v1/gameData/RetarderLevel` | int | uint8 | 30 | Current Level Of The Retarder. | >0 |
| `v1/gameData/ReverseLight` | bool | bool | 30 | Reverse Light Status | true false |
| `v1/gameData/Roll` | float | float | 30 | Roll Rate | >=0 |
| `v1/gameData/RoofAuxLight` | bool | bool | 30 | Are The Auxiliary Roof Lights Active | 1:true 0:false |
| `v1/gameData/Rpm` | int | uint16_t | 30 | Engine RPM | >=0 |
| `v1/gameData/Sector1BestTime` | float | float | 30 | Sector1BestTime | >=0 |
| `v1/gameData/Sector1LastLapTime` | float | float | 500 | Sector1LastLapTime | >=0 |
| `v1/gameData/Sector1Time` | float | float | 30 | Sector 1 Time | >=0 |
| `v1/gameData/Sector2BestTime` | float | float | 30 | Sector2BestTime | >=0 |
| `v1/gameData/Sector2LastLapTime` | float | float | 500 | Sector2LastLapTime | >=0 |
| `v1/gameData/Sector2Time` | float | float | 30 | Sector 2 Time | >=0 |
| `v1/gameData/Sector3BestTime` | float | float | 30 | Sector3BestTime | >=0 |
| `v1/gameData/Sector3LastLapTime` | float | float | 500 | Sector3LastLapTime | >=0 |
| `v1/gameData/SectorIndex` | int | level_1 | 2000 | Sector Number | >=0 |
| `v1/gameData/SectorsCount` | float | uint8_t | 2000 | Total Number Of Track Segments | >0 |
| `v1/gameData/SessionOdo` | float | float | 30 | Session Odometer | >=0 |
| `v1/gameData/SessionOdo&M` | float | float | 30 | Session Odometer | >=0 |
| `v1/gameData/SessionTimeLeft` | int | float | 30 | Session Time Remaining | >=0 |
| `v1/gameData/SessionTypeName` | string | string | 2000 | Session Type Name | 1~100 character |
| `v1/gameData/SoC` | float | float | 30 | Battery state of Charge for hybrid/electric vehicles | >=0 |
| `v1/gameData/Spectating` | int | uint32_t | 2000 | Spectating | >=0 |
| `v1/gameData/SpeedKmh` | int | float_6000_1 | 30 | Vehicle Speed(Kmh) | >=0 |
| `v1/gameData/SpeedMph` | int | float_6000_1 | 30 | Vehicle Speed(Mph) | >=0 |
| `v1/gameData/SpeedMs` | float | float_600_2 | 30 | Vehicle Speed(Ms) | >=0 |
| `v1/gameData/SpotterCarLeft` | float | bool | 30 | Blind-spot spotter: car detected on the left side (0: no 1: yes) | 0:no 1:yes |
| `v1/gameData/SpotterCarLeftAngle` | float | float | 30 | Bearing of the left target relative to car heading (deg); usually negative for left | -180~180 |
| `v1/gameData/SpotterCarLeftDistance` | float | float | 30 | Distance to the nearest target on the left (meters) | >=0 |
| `v1/gameData/SpotterCarRight` | float | bool | 30 | Blind-spot spotter: car detected on the right side (0: no 1: yes) | 0:no 1:yes |
| `v1/gameData/SpotterCarRightAngle` | float | float | 30 | Bearing of the right target relative to car heading (deg); usually positive for right | -180~180 |
| `v1/gameData/SpotterCarRightDistance` | float | float | 30 | Distance to the nearest target on the right (meters) | >=0 |
| `v1/gameData/StintOdo` | float | float | 30 | Total Distance Traveled by the Vehicle Over a Period of Time | >=0 |
| `v1/gameData/StintOdo&M` | float | float | 30 | Total Distance Traveled by the Vehicle Over a Period of Time(Mph) | >=0 |
| `v1/gameData/TC_B` | float | float | 30 | Current Traction Control Slip setting | 0:off >=1:The higher the value, the greater the degree of control intervention |
| `v1/gameData/TCActive` | float | bool | 30 | TC Activation | 0:triggered 1:untriggered |
| `v1/gameData/TCCut` | int | uint8 | 30 | Traction control Cut Level | 0:off >=1:The higher the value, the greater the degree of control intervention |
| `v1/gameData/TCCutMax` | int | uint8 | 500 | Maximum adjustable traction control cut level | >=0 |
| `v1/gameData/TCLevel` | float | level_1 | 30 | Traction Control Value | 0:off >=1:The higher the value, the greater the degree of control intervention |
| `v1/gameData/TCMaxLevel` | int | uint8 | 500 | Maximum adjustable traction control level | >=0 |
| `v1/gameData/TCSlipMax` | int | uint8 | 500 | Maximum adjustable traction control slip level | >=0 |
| `v1/gameData/Throttle` | float | float_001 | 30 | Throttle Position | 0~1 |
| `v1/gameData/ThrottleShaping` | float | float | 500 | ThrottleShaping | >=0 |
| `v1/gameData/TimeAbsolute` | int | int32_5 | 1000 | TimeAbsolute | >0 |
| `v1/gameData/TimeGapCarAhead` | float | float | 30 | Time gap to the nearest car ahead on track (seconds) | >=0 |
| `v1/gameData/TimeGapCarBehind` | float | float | 30 | Time gap to the nearest car behind on track (seconds) | >=0 |
| `v1/gameData/TimeGapPlaceAhead` | float | float | 30 | Time gap to the car in the next higher race position (seconds) | >=0 |
| `v1/gameData/TimeGapPlaceBehind` | float | float | 30 | Time gap to the car in the next lower race position (seconds) | >=0 |
| `v1/gameData/TimeOfDay` | float | float | 30 | Current in-game time of day on track | >=0 |
| `v1/gameData/TrackCode` | string | string | 500 | Track Code or Dentifier | 1~100 character |
| `v1/gameData/TrackConfig` | string | string | 2000 | Track Configuration | 1~100 character |
| `v1/gameData/TrackGripLevel` | int | uint8 | 30 | Current track grip level | >=0 |
| `v1/gameData/TrackId` | string | string | 2000 | Track ID | 1~100 character |
| `v1/gameData/TrackLength` | float | float | 2000 | Track Length | >0 |
| `v1/gameData/TrackLimitsSteps` | int | uint8 | 30 | Current accumulated track limits violation steps | >=0 |
| `v1/gameData/TrackLimitsStepsPerPenalty` | int | uint8 | 30 | Track limits violation steps required per penalty | >=0 |
| `v1/gameData/TrackLimitsStepsPerPoint` | int | uint8 | 30 | Track limits violation steps required per point | >=0 |
| `v1/gameData/TrackPositionMeters` | float | float | 30 | Track Position | >=0 |
| `v1/gameData/TrackTemp` | float | tyre_temp_1 | 2000 | Track Temperature | 0~255 |
| `v1/gameData/TrackTemp&unit=F` | float | track_temp_1 | 2000 | Track Temperature(F°) | 0~255 |
| `v1/gameData/TurboPercent` | float | percent_1 | 30 | Percentage of Turbocharger System Operation | >=0 |
| `v1/gameData/TyreCompoundIndexFrontLeft` | int | uint8 | 500 | Front left tyre compound index number | >=0 |
| `v1/gameData/TyreCompoundIndexFrontRight` | int | uint8 | 500 | Front right tyre compound index number | >=0 |
| `v1/gameData/TyreCompoundIndexRearLeft` | int | uint8 | 500 | Rear left tyre compound index number | >=0 |
| `v1/gameData/TyreCompoundIndexRearRight` | int | uint8 | 500 | Rear right tyre compound index number | >=0 |
| `v1/gameData/TyreCompoundTypeFrontLeft` | string | string | 500 | Front left tyre compound type number | 1~100 character |
| `v1/gameData/TyreCompoundTypeFrontRight` | string | string | 500 | Front right tyre compound type number | 1~100 character |
| `v1/gameData/TyreCompoundTypeRearLeft` | string | string | 500 | Rear left tyre compound type number | 1~100 character |
| `v1/gameData/TyreCompoundTypeRearRight` | string | string | 500 | Rear right tyre compound type number | 1~100 character |
| `v1/gameData/TyreDirtFrontLeft` | float | float | 2000 | Left Front Tire Dirt Accumulation | >=0 |
| `v1/gameData/TyreDirtFrontRight` | float | float | 2000 | Right Front Tire Dirt Accumulation | >=0 |
| `v1/gameData/TyreDirtRearLeft` | float | float | 2000 | Left Rear Tire Dirt Accumulation | >=0 |
| `v1/gameData/TyreDirtRearRight` | float | float | 2000 | Right Rear Tire Dirt Accumulation | >=0 |
| `v1/gameData/TyreOptimalTempFrontLeft` | float | float | 30 | Front left tyre optimal operating temperature (°C) | >=0 |
| `v1/gameData/TyreOptimalTempFrontRight` | float | float | 30 | Front right tyre optimal operating temperature (°C) | >=0 |
| `v1/gameData/TyreOptimalTempRearLeft` | float | float | 30 | Rear left tyre optimal operating temperature (°C) | >=0 |
| `v1/gameData/TyreOptimalTempRearRight` | float | float | 500 | Rear right tyre optimal operating temperature (°C) | >=0 |
| `v1/gameData/TyrePressureFL&B` | float | float | 2000 | Left Front Tire Pressure(bar) | >0 |
| `v1/gameData/TyrePressureFL&kpa` | float | float | 2000 | Left Front Tire Pressure(kpa) | >0 |
| `v1/gameData/TyrePressureFR&B` | float | float | 2000 | Right Front Tire Pressure(bar) | >0 |
| `v1/gameData/TyrePressureFR&kpa` | float | float | 2000 | Right Front Tire Pressure(kpa) | >0 |
| `v1/gameData/TyrePressureFrontLeft` | float | tyre_pressure_1 | 2000 | Left Front Tire Pressure(psi) | >0 |
| `v1/gameData/TyrePressureFrontRight` | float | tyre_pressure_1 | 2000 | Right Front Tire Pressure(psi) | >0 |
| `v1/gameData/TyrePressureRearLeft` | float | tyre_pressure_1 | 2000 | Left Rear Tire Pressure(psi) | >0 |
| `v1/gameData/TyrePressureRearRight` | float | tyre_pressure_1 | 2000 | Right Rear Tire Pressure(psi) | >0 |
| `v1/gameData/TyrePressureRL&B` | float | float | 2000 | Left Rear Tire Pressure(bar) | >0 |
| `v1/gameData/TyrePressureRL&kpa` | float | float | 2000 | Left Rear Tire Pressure(kpa) | >0 |
| `v1/gameData/TyrePressureRR&B` | float | float | 2000 | Right Rear Tire Pressure(bar) | >0 |
| `v1/gameData/TyrePressureRR&kpa` | float | float | 2000 | Right Rear Tire Pressure(kpa) | >0 |
| `v1/gameData/TyresDirtyLevelAvg` | float | float | 2000 | Average Tire Dirtiness Level | >=0 |
| `v1/gameData/TyresDirtyLevelMax` | float | float | 2000 | Maximum Tire Dirtiness Level | >=0 |
| `v1/gameData/TyresDirtyLevelMin` | float | float | 2000 | Minimum Tire Dirtiness Level | >=0 |
| `v1/gameData/TyresTemperatureAvg` | float | float | 2000 | Average Tire Temperature | >=0 |
| `v1/gameData/TyresTemperatureAvg&F` | float | float | 2000 | Maximum Tire Temperature( F°) | >=0 |
| `v1/gameData/TyresTemperatureMax` | float | float | 2000 | Maximum Tire Temperature | >=0 |
| `v1/gameData/TyresTemperatureMax&F` | float | float | 2000 | Maximum Tire Temperature( F°) | >=0 |
| `v1/gameData/TyresTemperatureMin` | float | float | 2000 | Minimum Tire Temperature | >=0 |
| `v1/gameData/TyresTemperatureMin&F` | float | float | 2000 | Minimum Tire Temperature( F°) | >=0 |
| `v1/gameData/TyresWearAvg` | float | float | 2000 | Average Tire Wear | >=0 |
| `v1/gameData/TyresWearMax` | float | float | 2000 | Maximum Tire Wear | >=0 |
| `v1/gameData/TyresWearMin` | float | float | 2000 | Minimum Tire Wear | >=0 |
| `v1/gameData/TyreTempFrontLeft` | float | tyre_temp_1 | 2000 | Left Front Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontLeft&unit=F` | float | float | 2000 | Left Front Tire Temperature(F°) | -148~384 |
| `v1/gameData/TyreTempFrontLeftInner` | float | tyre_temp_1 | 2000 | Left Front Inner Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontLeftInner&unit=F` | float | float | 2000 | Left Front Inner Tire Temperature(F°) | -148~384 |
| `v1/gameData/TyreTempFrontLeftMiddle` | float | tyre_temp_1 | 2000 | Left Front Center Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontLeftMiddle&unit=F` | float | float | 2000 | Left Rear Center Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontLeftOuter` | float | tyre_temp_1 | 2000 | Left Front Outer Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontLeftOuter&unit=F` | float | float | 2000 | Left Front Outer Tire Temperature (°F) | -148~384 |
| `v1/gameData/TyreTempFrontRight` | float | tyre_temp_1 | 2000 | Right Front Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontRight&unit=F` | float | float | 2000 | Right Front Tire Temperature(F°) | -148~384 |
| `v1/gameData/TyreTempFrontRightInner` | float | tyre_temp_1 | 2000 | Right Front Inner Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontRightInner&unit=F` | float | float | 2000 | Right Front Inner Tire Temperature(F°) | -148~384 |
| `v1/gameData/TyreTempFrontRightMiddle` | float | tyre_temp_1 | 2000 | Right Front Center Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontRightMiddle&unit=F` | float | float | 2000 | Right Front Center Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontRightOuter` | float | tyre_temp_1 | 2000 | Right Front Outer Tire Temperature | -148~384 |
| `v1/gameData/TyreTempFrontRightOuter&unit=F` | float | float | 2000 | Right Front Outer Tire Temperature (°F) | -148~384 |
| `v1/gameData/TyreTempRearLeft` | float | tyre_temp_1 | 2000 | Left Rear Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearLeft&unit=F` | float | float | 2000 | Left Rear Tire Temperature(F°) | -148~384 |
| `v1/gameData/TyreTempRearLeftInner` | float | tyre_temp_1 | 2000 | Left Rear Inner Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearLeftInner&unit=F` | float | float | 2000 | Left Rear Inner Tire Temperature(F°) | -148~384 |
| `v1/gameData/TyreTempRearLeftMiddle` | float | tyre_temp_1 | 2000 | Left Rear Center Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearLeftMiddle&unit=F` | float | float | 2000 | Left Rear Center Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearLeftOuter` | float | tyre_temp_1 | 2000 | Left Rear Outer Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearLeftOuter&unit=F` | float | float | 2000 | Left Rear Outer Tire Temperature (°F) | -148~384 |
| `v1/gameData/TyreTempRearRight` | float | tyre_temp_1 | 2000 | Right Rear Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearRight&unit=F` | float | float | 2000 | Right Rear Tire Temperature(F°) | -148~384 |
| `v1/gameData/TyreTempRearRightInner` | float | tyre_temp_1 | 2000 | Right Rear Inner Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearRightInner&unit=F` | float | float | 2000 | Right Reart Inner Tire Temperature(F°) | -148~384 |
| `v1/gameData/TyreTempRearRightMiddle` | float | tyre_temp_1 | 2000 | Right Rear Center Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearRightMiddle&unit=F` | float | float | 2000 | Right Rear Center Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearRightOuter` | float | tyre_temp_1 | 2000 | Right Rear Outer Tire Temperature | -148~384 |
| `v1/gameData/TyreTempRearRightOuter&unit=F` | float | float | 2000 | Right Rear Outer Tire Temperature (°F) | -148~384 |
| `v1/gameData/TyreType` | int | uint8 | 500 | Tyre Compound Used | >0 |
| `v1/gameData/TyreWearFrontLeft` | int | percent_1 | 2000 | Left Front Tire Wear | 0~100 |
| `v1/gameData/TyreWearFrontRight` | int | percent_1 | 2000 | Right Front Tire Wear | 0~100 |
| `v1/gameData/TyreWearRearLeft` | int | percent_1 | 2000 | Left Rear Tire Wear | 0~100 |
| `v1/gameData/TyreWearRearRight` | int | percent_1 | 2000 | Right Rear Tire Wear | 0~100 |
| `v1/gameData/VehicleFilename` | string | string | 2000 | Current vehicle configuration filename | string |
| `v1/gameData/VehicleTag1` | string | string | 500 | Vehicle custom tag 1 (e.g. vehicle sub-class) | string |
| `v1/gameData/VehicleTag2` | string | string | 500 | Vehicle custom tag 2 | string |
| `v1/gameData/VehicleTag3` | string | string | 500 | Vehicle custom tag 3 | string |
| `v1/gameData/VirtualEnergy` | float | float | 30 | Virtual energy value for energy management rules | >=0 |
| `v1/gameData/WaterPress` | float | float | 2000 | WaterPress | >0 |
| `v1/gameData/WaterTemp` | float | float | 500 | Water Temperature | >0 |
| `v1/gameData/WaterTempWarning` | bool | bool | 500 | Is The Water Temperature Warning Active | 1:true 0:false |
| `v1/gameData/WheelSpin` | int | bool | 30 | Tire Slip | 1:true 0:false |
| `v1/gameData/WhiteFlag` | int | bool | 30 | Green Flag Status | 1:true 0:false |
| `v1/gameData/WiperClass` | int | uint8 | 30 | Current Wiper Stage | 0:off >=1:The higher the value, the greater the degree of control intervention |
| `v1/gameData/Wipers` | bool | bool | 30 | Are The Wipers Enabled | 1:true 0:false |
| `v1/gameData/YellowFlag` | int | bool | 30 | Yellow Flag Status | 1:true 0:false |

## `v1/gameData/patch/*` scalar/string channels

| Path | Type | Wire encoding | Tier (ms) | Description | Range |
|---|---|---|---|---|---|
| `v1/gameData/patch/DisplayTrackName` | string | string | 2000 | Track Name | 1~100 character |
| `v1/gameData/patch/GameName` | string | string | 2000 | Game Name | 1~100 character |
| `v1/gameData/patch/Location` | array | location_t | 30 | Current Player Position | None |
| `v1/gameData/patch/OnTrack` | bool | bool | 500 | On-Track Status | 1:true 0:false |
| `v1/gameData/patch/OpponentCount` | int | int8_t | 2000 | Number Of Opponents | >=0 |
| `v1/gameData/patch/PlayerIndex` | int | int8_t | 2000 | Current Player's Position | >0 |
| `v1/gameData/patch/TrackName` | string | string | 2000 | Track Name | 1~100 character |
| `v1/gameData/patch/TrackPositionPercent` | float | percent_1 | 30 | Current Lap Progress | 0-1 |

(plus `v1/gameData/patch/Location` + `patch/Location_0`..`patch/Location_63` — packed 64-bit track-map coordinates, and `patch/ri0`..`patch/ri63` — radar/race-info slots)


## `v1/preset/*` (wheel-internal, not game telemetry)

| Path | Type | Wire encoding | Tier (ms) | Description | Range |
|---|---|---|---|---|---|
| `v1/preset/CurrentTorque` | float | float | 30 | Current Torque | >0 |
| `v1/preset/SteeringWheelAngle` | float | float | 30 | Steering Wheel Angle | -∞~+∞ |
| `v1/preset/TimeStamp` | float | float | 30 | Monotonic millisecond timestamp | >=0 |