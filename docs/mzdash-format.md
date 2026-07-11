# MOZA `.mzdash` Dashboard File Format

Reverse-engineered 2026-07-10 from five real community dashboards published on
https://mozaracing.com/blogs/dash-community (MOZA "Dash Community"). All claims below are
verified against the actual files on disk in this directory.

## Samples on disk (this directory)

| Sample | Target device | Canvas | Path (relative to this dir) |
|---|---|---|---|
| BMW M4 GT3 CS KS PRO (Maomi-Tom) | `W18 Display` (CS/KS Pro wheel screen) | 780x248 | `BMW M4 GT3 CS KS PRO Maomi-Tom/BMW M4 GT3 CS KS PRO Maomi-Tom.mzdash` |
| ICONIC DASHBOARD CS KS PRO | `W18 Display` | 780x248 | `iconic/ICONIC DASHBOARD CS KS PRO Maomi-Tom/ICONIC DASHBOARD CS KS PRO Maomi-Tom.mzdash` |
| Simple Rally Mini Dash | `W17 Display` | 780x248 | `mini/Simple Rally Mini Dash.mzdash` (+ `mini/Resource/MD5/*.png`) |
| Simple Rally Dash - English (from "CM2 dashes") | `S09 Display` | 1280x720 | `Simple Rally Dash - English.mzdash` (+ `./Resource/MD5/*.png`) |
| NFS8 (Vision GS, round screen) | `Display` | 480x480 | `nfs8/NFS8/NFS8.mzdash` (+ `nfs8/NFS8/Resource/MD5/*.png`) |

Original zips also kept: `bmw-m4-gt3.zip`, `iconic.zip`, `mini.zip`, `cm2-dirt.zip`, `nfs8.zip`.

Download note: the official CDN `image.mozaracing.com` currently serves an **expired TLS
certificate** (expired 2026-07-06), so direct curl fails verification. Workaround used: trigger a
Wayback Machine save (`https://web.archive.org/save/<url>`) and download the archived original
bytes from `https://web.archive.org/web/<timestamp>id_/<url>`.

## 1. Container format

- A `.mzdash` file is **plain UTF-8 JSON text** (single file, no zip/gzip/binary wrapper).
  `file` reports "JSON text data". Sizes seen: 33 KB - 331 KB.
- Community dashboards are *distributed* as an ordinary `.zip` containing:
  ```
  <Dash Name>/
    <Dash Name>.mzdash          # the JSON document
    1.png, 2.png, ...           # marketing/preview screenshots (not referenced by the JSON)
    Resource/
      MD5/
        <md5hex>.png            # image assets used by the dashboard (only if it uses images)
  ```
- Image assets are **not embedded** in the JSON. They live in `Resource/MD5/` next to the
  `.mzdash`, and each file is named `<md5-of-its-own-content>.png` (verified: `md5sum` of every
  sample asset matches its filename). The JSON references them by the relative string
  `"MD5/<md5hex>.png"`.
- No other manifest, signature, or checksum exists. The only consistency requirements are:
  (a) resource filename == MD5 of file content, (b) every referenced image appears in the
  top-level `imageResources` array, (c) node `id`s are unique integers within the file.

## 2. Top-level document (the Window node)

The document root is itself a node of type `Window.qml`. Exact top-level keys (all samples,
`"version": "1.1.1"`):

```jsonc
{
  "type": "Window.qml",
  "version": "1.1.1",                // format version
  "id": 0,                           // root node id is always 0
  "name": "BMW M4 GT3 CS KS PRO Maomi-Tom",   // dashboard display name
  "lastModified": 1768119304,        // unix time, seconds
  "window": {
    "GUID": "2vM1c6XnFB2Ff3JvLE222ZxkUhegkjTR",  // 32-char random alnum, OR "{uuid}" braced form
    "defaultScreenId": 0,            // index of the initially shown Screen (0 in all samples)
    "idealDeviceInfos": [            // device targeting (see section 7)
      { "deviceId": 8, "networkId": 1,
        "hardwareVersion": "RS21-W18-HW RGB-DU-V11",
        "productType": "W18 Display" }
    ]
  },
  "general":  { ... },               // common geometry/appearance block; width/height = canvas
  "borderStyle": { ... },            // common border block (all zeros at root)
  "effect": { "gravitySensorEnabled": false, "rotation": 0 },   // root effect is minimal
  "binding": {},                     // common binding block (empty at root in samples)
  "actions": {},                     // empty object in ALL samples (semantics unknown)
  "macros": {},                      // empty object in ALL samples
  "plugins": [],                     // empty array in ALL samples
  "imageResources": [                // manifest of every image asset used anywhere in the tree
    "MD5/1aba96dcd6c0c16f7ee32d95e160d333.png",
    "MD5/bd529011a002c03dc77b2f63b193b789.png"
  ],
  "children": [ /* one or more Screen.qml nodes */ ]
}
```

Canvas resolution is declared in root `general.width` / `general.height` (and repeated on each
Screen): **780x248 for the CS/KS Pro wheel display**, 1280x720 for the S09, 480x480 for Vision GS.

## 3. The node tree

Every element is a node with this **common skeleton** (all keys always present):

```jsonc
{
  "type": "<Kind>.qml",       // node class, see section 4
  "id": 26,                   // unique integer within the file
  "name": "GEAR",             // free-form editor label (may be any UTF-8, e.g. Chinese)
  "children": [],             // nested nodes (Window -> Screens -> widgets; widgets may nest)
  "general": {
    "x": 290, "y": 0,         // position in parent coordinates (floats allowed)
    "width": 180, "height": 248,
    "visible": true,
    "locked": false,          // editor-only lock flag
    "backgroundColor": { "type": "SOLID", "color": "#00000000" },   // see section 5
    "borderColor":     { "type": "SOLID", "color": "#00000000" },
    "borderWidth": 0,
    "borderRadius": 0
  },
  "borderStyle": {            // per-edge border control (duplicates/refines general border)
    "allBorders": 0, "bordersTop": 0, "bordersBottom": 0, "bordersLeft": 0, "bordersRight": 0,
    "borderColor": { "type": "SOLID", "color": "#00000000" },
    "allCornerRadius": 0,
    "radiusTopLeft": 0, "radiusTopRight": 0, "radiusBottomLeft": 0, "radiusBottomRight": 0
  },
  "effect": {
    "opacity": 100,           // 0-100
    "rotation": 0,            // degrees
    "blurRadius": 0,
    "blinkEnabled": false, "blinkDelay": 250,        // ms; blink can be bound (see section 6)
    "gravitySensorEnabled": false,
    // optional, present on some node kinds:
    "outerShadow": { "blur": 0, "depth": 0, "direction": 0,
                     "color": { "type": "SOLID", "color": "#00000000" } },
    "innerShadow": { "blur": 0, "size": 0,
                     "color": { "type": "SOLID", "color": "#FFFFFF" } }
  },
  "binding": {},              // telemetry bindings, see section 6
  "actions": {}, "macros": {}, "plugins": [],   // always empty in samples
  // ...plus type-specific blocks below
}
```

Child order = z-order; in the samples the full-canvas background Rectangle is first in
`children` and text overlays follow (i.e. earlier entries render underneath later ones).

## 4. Node types observed and their type-specific blocks

### `Screen.qml`
Direct children of the Window. A dashboard may contain several screens (NFS8 has 5, the rally
dash has 2 - KM/H and MPH variants); `window.defaultScreenId` selects the initial one. Extra
keys beyond the common skeleton:
```jsonc
"guides": [],                 // editor alignment guides
"image":  { "src": "" }       // optional background image ("MD5/<hash>.png")
```
Screen `general.width/height` equals the canvas size, `x`/`y` = 0.

### `Rectangle.qml`
No extra block; drawn purely from `general` + `borderStyle` (+ effects). Background may be a
gradient (section 5).

### `Text.qml`
```jsonc
"text": {
  "text": "N",                          // static/default text (bindings override at runtime)
  "fontFamily": "Furore",               // font referenced BY NAME only, never embedded
  "fontSize": 180,
  "fontWeight": 500,
  "fontColor": { "type": "SOLID", "color": "#00ff00" },
  "horizontalAlignment": "AlignCenter", // AlignLeft | AlignCenter | AlignRight
  "verticalAlignment": "AlignCenter",   // AlignTop | AlignCenter | AlignBottom
  "wrapText": false,
  "paddingTop": 0, "paddingBottom": 0, "paddingLeft": 0, "paddingRight": 0
},
"textEffect": {
  "shadowBlur": 0, "shadowDepth": 0, "shadowDirection": 0,
  "shadowColor": { "type": "SOLID", "color": "#00000000" }
}
```
Font families seen in the wild: Furore, Bebas Neue, League Gothic, Roboto, FRIZON, Manrope3,
Alibaba PuHuiTi, Source Han Sans CN, Fontquan-XinYilogoTi. They must exist on the authoring
PC / in Pit House; there is no font-embedding mechanism in the file.

### `Image.qml`
```jsonc
"image": { "src": "MD5/bd529011a002c03dc77b2f63b193b789.png" }
```
`src` is relative to the sibling `Resource/` directory and must also be listed in the root
`imageResources` array.

### `LinearGauge.qml` (bar gauge)
```jsonc
"linearGauge": {
  "minimum": 0, "maximum": 100, "value": 0,        // value usually bound
  "gaugeOrientation": "Horizontal",                 // or "Vertical"
  "gaugeAlignment": "AlignLeft",                    // fill origin
  "gaugeColor": { "type": "SOLID", "color": "#ffffff" },
  "gaugeImage": "", "backgroundImage": "",          // optional "MD5/<hash>.png"
  "alternateStyle": {
    "useAlternateStyle": false,
    "gaugeColor": { "type": "SOLID", "color": "#03A200" },
    "gaugeImage": ""
  }
}
```

### `CircularGauge.qml` (arc gauge)
```jsonc
"circularGauge": {
  "minimum": 0, "maximum": 100, "value": 30,
  "startAngle": 190, "sweepAngle": 40,              // degrees
  "strokeThickness": 10,
  "backgroundColor": { "type": "SOLID", "color": "#017809" },
  "gaugeColor":      { "type": "SOLID", "color": "#3f3f3f" },
  "backgroundImage": "", "gaugeImage": ""
}
```

### `DialGauge.qml` (needle dial / tachometer)
Type-specific blocks are **top-level on the node** (not nested under a `dialGauge` key):
```jsonc
"value": { "minimum": 0, "maximum": 7, "value": 0 },       // bound via "value.value"
"dial": {
  "outerRadius": 240, "innerRadius": 0,
  "outerStrokeThickness": 0, "innerStrokeThickness": 2.5,
  "dialBackgroundColor": { "type": "SOLID", "color": "#00000000" },
  "borderStrokeColor":   { "type": "SOLID", "color": "#00000000" }
},
"scale": { "startAngle": 95, "sweepAngle": 200,
           "scaleGlowRadius": null,
           "scaleGlowColor": { "type": "SOLID", "color": "#00000000" } },
"majorTicks": { "valuePerMajorDivision": 1, "majorTickLength": 15, "majorTickRadius": 217,
                "majorTickThickness": 0,
                "majorTickColor": { "type": "SOLID", "color": "#ffffff" } },
"minorTicks": { "minorDivisionsCount": 4, "minorTickLength": 0, "minorTickRadius": 0,
                "minorTickThickness": 2,
                "minorTickColor": { "type": "SOLID", "color": "#ffffff" } },
"scaleLabels": {
  "fontFamily": "Fontquan-XinYilogoTi", "fontSize": 50, "fontWeight": 500,
  "fontColor": { "type": "SOLID", "color": "#ffffff" },
  "positionRadius": 400, "labelAngleOffset": 0, "majorTicksPerLabel": 1,
  "labelsCustomText": "", "circularLabelOrientation": false,
  "alternateLabelStyle": { "useAlternateLabel": false, "fontFamily": "...", "fontSize": 32,
                           "fontWeight": 500, "positionRadius": 150,
                           "fontColor": { "type": "SOLID", "color": "#FFFFFF" } }
},
"needle": { "showNeedle": true, "needleImage": "MD5/e5211790949bd75852cef3a71c8a181a.png",
            "needleLength": 130, "needleOffset": 100, "needleThickness": 30, "capRadius": 0 },
"radialGauge": { "showRadialGauge": false, "radialGaugeRadius": 0, "radialGaugeStartOffset": 0,
                 "radialGaugeThickness": 10,
                 "radialGaugeColor": { "type": "SOLID", "color": "#56ff00" } },
"optimalRange": {
  "startValue": 5, "endValue": 6, "arcRadius": 220, "arcThickness": 20,
  "optimalStyle":      { "arcColor": {...}, "majorTickColor": {...}, "minorTickColor": {...},
                         "customLabelColor": {...},
                         "showMajorTickColor": false, "showMinorTickColor": false,
                         "showCustomLabelColor": true },
  "aboveOptimalStyle": { /* same shape */ },
  "belowOptimalStyle": { /* same shape */ }
}
```

(Widget types not present in these five samples — e.g. video/indicator types the Dash Studio
editor may offer — are undocumented here.)

## 5. Color objects

Every color is an object, never a bare string:

```jsonc
{ "type": "SOLID", "color": "#FF000000" }
```
- Hex is `#RRGGBB` or `#AARRGGBB` (alpha FIRST): `#00000000` = fully transparent,
  `#FF000000` = opaque black, `#2CC3C3C3` = ~17%-alpha grey.
- Linear gradient variant (seen on a Rectangle `general.backgroundColor`):
```jsonc
{
  "type": "GRADIENT_LINEAR",
  "color": "#00000000",                       // fallback/base color
  "gradientHandlePositions": [                // normalized handles (start, end, width), Figma-style
    { "x": 0.5, "y": -0.09 }, { "x": 0.5, "y": 1 }, { "x": 0.25, "y": 5 }
  ],
  "gradientStops": [
    { "color": "#ff0000",   "position": 0.80 },
    { "color": "#00ff0000", "position": 1 }
  ]
}
```

## 6. Telemetry bindings (`binding` block)

A node's `binding` object maps a **dotted property path** (relative to the node) to a method
chain evaluated as JavaScript:

```jsonc
"binding": {
  "text.text": {
    "type": "METHOD_CHAINING",
    "methods": [
      "Telemetry.get(\"v1/gameData/Gear\").value",
      "((r=Number(_result))=>{if(isNaN(r))return _result;else if(r==0)return'N';else if(r>0)return r.toString();else if(r==-1)return 'R';else if(r<-1)return 'R'+Math.abs(r).toString();})()"
    ]
  }
}
```

Rules observed:
- `type` is always `"METHOD_CHAINING"`. `methods` is an ordered array of JS expression strings.
- Method N+1 sees the previous expression's result as the variable **`_result`**. A trailing
  `"_result"` pass-through entry is common (harmless identity step); single-entry chains also
  occur.
- Telemetry access API: `Telemetry.get("v1/gameData/<Var>").value` (single or double quotes both
  used). Arbitrary JS is allowed: ternaries, IIFEs, arrow functions with default-param locals,
  `Math.*`, `parseInt`, template literals, `padStart`, etc.
- A binding can return a **color string** (`'#FF0000'`) when bound to a color property, a
  number for numeric properties, `1`/`0` (truthy) for `general.visible`, or a string for text.

Bound property paths seen in the wild:

| Bound path | Meaning | Example expression |
|---|---|---|
| `text.text` | text content | gear/laptime formatters above |
| `text.fontColor` | font color | `(() => { var a = Telemetry.get('v1/gameData/SpeedKmh').value; if (isNaN(a)) { return '#2CC3C3C3'; } else {if(a == 0) return '#2CC3C3C3'; else return '#FFFFFF';}})();` |
| `general.visible` | show/hide | `Telemetry.get("v1/gameData/PitLimiter").value==1? 1:0` |
| `general.x` | position (moving needle strip) | `Math.max(0, Math.min(1053, (Telemetry.get("v1/gameData/CarSettings_CurrentDisplayedRPMPercent").value \|\| 0) / 100 * 1053))` |
| `general.backgroundColor` | background color | `Telemetry.get("v1/gameData/CarSettings_CurrentDisplayedRPMPercent").value > 93 ? '#FF0000':'#808080'` |
| `linearGauge.value` | bar fill | `Telemetry.get("v1/gameData/CarSettings_CurrentDisplayedRPMPercent").value` |
| `linearGauge.gaugeColor` | bar color | `... > 96 ? '#FF0000':'#FFFFFF'` |
| `circularGauge.value` | arc fill | `100 - Telemetry.get("v1/gameData/FuelRemainder").value` |
| `value.value` | DialGauge needle | `parseInt(Telemetry.get('v1/gameData/Rpm').value) / 1000.0` |
| `effect.blinkEnabled` | blink on/off | (empty string `""` in NFS8 — editor artifact; blink instead driven via `general.visible`) |

Reusable formatter idioms found in the official samples (verbatim):
- Fixed decimals: `((r=Number(_result),fc=((n,d)=>(([i,p=""])=>`` `${i}${d?`.${(p+("0".repeat(d))).slice(0,d)}`:""}` ``)(n.toString().split("."))))=>isNaN(r)?undefined:fc(r, 2))()`
- Lap time `MM:SS.mmm` with sentinel: `((r=Math.abs(_result),f=(a,b)=>Math.floor(a).toString().padStart(b,'0'),m=-3.4028234e+38,s=_result<0?'-':'')=>isNaN(r)?undefined:_result>m?`` `${s}${f(r/60,2)}:${f(r%60,2)}.${f(r%1*1000,3)}` ``:'--:--.---')()`
  (note the `-3.4028234e+38` = -FLT_MAX "no data" sentinel check)
- Gap `SS.hh`: same pattern with `'--.--'` fallback.

## 7. Device targeting (`window.idealDeviceInfos`)

`idealDeviceInfos` is an array of preferred devices; one entry in every sample.
Observed combinations:

| productType | hardwareVersion | Canvas | Device |
|---|---|---|---|
| `W18 Display` | `RS21-W18-HW RGB-DU-V11` | 780x248 | CS/KS Pro steering-wheel display |
| `W17 Display` | `RS21-W17-HW RGB-DU-V11` | 780x248 | (other RS wheel display, same panel) |
| `S09 Display` | `RS21-W08-HW SM-DU-V14` | 1280x720 | standalone dash unit (published under "CM2 dashes") |
| `Display` | `RS21-W08-HW SM-DU-V14` | 480x480 | Vision GS round wheel screen |

`deviceId` is `8` and `networkId` is `1` in every sample. The canvas size itself lives in
`general.width/height`, not in the device info — the device entry appears advisory (Pit House
uses it to match the dash to hardware on import).

## 8. Every telemetry variable path seen (verbatim, union of all 5 samples)

```
v1/gameData/ABSLevel
v1/gameData/BestLapTime
v1/gameData/BrakeBias
v1/gameData/CarCoordinates01
v1/gameData/CarCoordinates02
v1/gameData/CarCoordinates03
v1/gameData/CarSettings_CurrentDisplayedRPMPercent   // RPM as 0-100 percent, rev-light scaled
v1/gameData/CurrentLap
v1/gameData/CurrentLapTime
v1/gameData/CurrentPos
v1/gameData/ECUMap
v1/gameData/ERSStored
v1/gameData/EngineStarted            // 1/0
v1/gameData/Fuel
v1/gameData/FuelRemainder            // percent in NFS8 usage
v1/gameData/GAP                      // gap/delta, seconds (negative = gain)
v1/gameData/Gear                     // -1=R, 0=N, 1..n
v1/gameData/LastLapTime
v1/gameData/PitLimiter               // 1/0
v1/gameData/Rpm
v1/gameData/SpeedKmh
v1/gameData/SpeedMph
v1/gameData/TCLevel
v1/gameData/TrackId
v1/gameData/TrackLength
v1/gameData/TrackTemp
v1/gameData/TyrePressureFrontLeft
v1/gameData/TyrePressureFrontRight
v1/gameData/TyrePressureRearLeft
v1/gameData/TyrePressureRearRight
v1/gameData/patch/OpponentCount
v1/gameData/patch/TrackPositionPercent
```
Times are float seconds; `-3.4028234e+38` (-FLT_MAX) is used as the "no value" sentinel.

## 9. Hand-authoring a new CS Pro (780x248) dashboard — checklist

1. Create one JSON file `<Name>.mzdash` with root `type:"Window.qml"`, `version:"1.1.1"`,
   `id:0`, `name`, `lastModified` (unix seconds), and a fresh random `window.GUID`
   (32 alnum chars or `{uuid}` — both accepted).
2. Set `window.defaultScreenId: 0` and `window.idealDeviceInfos` to the W18 entry
   (`{"deviceId":8,"networkId":1,"hardwareVersion":"RS21-W18-HW RGB-DU-V11","productType":"W18 Display"}`).
3. Root and each Screen `general`: `x:0, y:0, width:780, height:248`, opaque background
   (`#FF000000`).
4. Add `children: [ Screen.qml ]`, then widget nodes inside the screen. Give every node the
   full common skeleton (all keys shown in section 3 — the official editor always writes them),
   a unique integer `id`, and empty `actions`/`macros`/`plugins`/`binding` where unused.
5. For images: save PNGs, rename each to `<md5>.png` (md5 of its bytes), place in
   `Resource/MD5/` beside the `.mzdash`, reference as `"MD5/<md5>.png"` in `image.src` /
   `needleImage` / `gaugeImage` / `backgroundImage`, and list every one in root `imageResources`.
6. Bind telemetry with `binding["text.text"] = { "type":"METHOD_CHAINING", "methods": [
   "Telemetry.get(\"v1/gameData/Rpm\").value", "<optional JS formatter using _result>" ] }`.
7. Fonts: stick to families installed on the target PC (e.g. Roboto, Bebas Neue); there is no
   embedding.
8. Import via MOZA Pit House > Dashboards > Import, selecting the `.mzdash` (keep the
   `Resource/` folder next to it if images are used; community zips ship them together).

## 10. Open questions / unverified

- Semantics of `actions`, `macros`, `plugins` (empty `{}`/`[]` in all five samples) — likely
  button actions / macro hooks in newer Dash Studio versions.
- How multi-screen switching is triggered at runtime (wheel button assignment lives outside the
  file, in Pit House).
- Whether Pit House's importer copies adjacent `Resource/` automatically or requires the zip
  layout; the AZOM SimHub plugin docs confirm Pit House keeps an on-disk ".mzdash source folder"
  that third-party tools scan recursively.
- `effect.gravitySensorEnabled` (false everywhere) — presumably rotates the dash with the wheel.
- Exact list of additional widget types supported by the Dash Studio editor beyond the eight
  observed (`Window/Screen/Rectangle/Text/Image/LinearGauge/CircularGauge/DialGauge`).
