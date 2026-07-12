#!/usr/bin/env python3
"""Compile the ETS2 Truck Cluster dashboard for the MOZA CS Pro wheel screen.

Produces:
  dist/ETS2 Truck Cluster/ETS2 Truck Cluster.mzdash   (import this in Pit House)
  dist/ETS2 Truck Cluster/preview-*.png               (renders of the layout)
  dist/ETS2-Truck-Cluster.zip                         (community-style bundle)

The .mzdash format is plain JSON (reverse-engineered from official MOZA Dash
Community files, see docs/mzdash-format.md). The CS Pro screen is a
"W18 Display": 780x248. Telemetry paths come from MOZA's own channel catalog
(docs/ets2-telemetry.md); expressions are the Dash Studio METHOD_CHAINING
JavaScript documented in MOZA's Dash Studio tutorial.
"""

import copy
import json
import random
import shutil
import string
import time
import zipfile
from pathlib import Path

DASH_NAME = "ETS2 Truck Cluster"
OUT_DIR = Path(__file__).parent / "dist" / DASH_NAME

W, H = 780, 248
FONT = "Roboto"

# ---------------------------------------------------------------- colors ----
# .mzdash colors are #AARRGGBB (alpha first); expressions may return #RRGGBB.
BG = "#FF000000"
WHITE = "#FFFFFFFF"
GRAY = "#FF9E9E9E"      # secondary labels
FAINT = "#FF8A8A8A"     # informational readings
DIM = "#FF2E2E2E"       # inactive warning lamp (ghosted)
PANEL = "#FF0D0D0D"
PANEL_BORDER = "#FF333333"
BAR_BG = "#FF161616"
SEPARATOR = "#FF1F1F1F"
LIMIT_RING = "#FFD50000"

# expression-side (returned by JS, 6-digit is fine)
J_WHITE, J_GRAY, J_FAINT, J_DIM = "#FFFFFF", "#9E9E9E", "#8A8A8A", "#2E2E2E"
J_GREEN, J_AMBER, J_RED, J_CYAN, J_BLUE = (
    "#00E676", "#FFB300", "#FF1744", "#00E5FF", "#40C4FF")


def solid(c):
    return {"type": "SOLID", "color": c}


# ------------------------------------------------------- node skeletons -----
# Exact key sets copied from official W18 (CS/KS Pro) community dashboards.

def base_node(kind, name, x, y, w, h, bg="#00000000"):
    return {
        "type": kind,
        "id": 0,  # assigned later
        "name": name,
        "children": [],
        "general": {
            "x": x, "y": y, "width": w, "height": h,
            "visible": True, "locked": False,
            "backgroundColor": solid(bg),
            "borderColor": solid("#00000000"),
            "borderWidth": 0, "borderRadius": 0,
        },
        "borderStyle": {
            "allBorders": 0, "bordersTop": 0, "bordersBottom": 0,
            "bordersLeft": 0, "bordersRight": 0,
            "borderColor": solid("#00000000"),
            "allCornerRadius": 0, "radiusTopLeft": 0, "radiusTopRight": 0,
            "radiusBottomLeft": 0, "radiusBottomRight": 0,
        },
        # Shadow keys are added per node type below, mirroring exactly which
        # effect keys the official editor writes for each widget kind.
        "effect": {
            "opacity": 100, "rotation": 0, "blurRadius": 0,
            "blinkEnabled": False, "blinkDelay": 250,
            "gravitySensorEnabled": False,
        },
        "binding": {},
        "actions": {}, "macros": {}, "plugins": [],
    }


def outer_shadow():
    return {"blur": 0, "depth": 0, "direction": 0, "color": solid("#00000000")}


def rect(name, x, y, w, h, bg, border=None, border_w=0, radius=0):
    n = base_node("Rectangle.qml", name, x, y, w, h, bg)
    n["effect"]["outerShadow"] = outer_shadow()
    n["effect"]["innerShadow"] = {"blur": 0, "size": 0, "color": solid("#FFFFFF")}
    if border:
        n["general"]["borderColor"] = solid(border)
        n["general"]["borderWidth"] = border_w
        bs = n["borderStyle"]
        bs["borderColor"] = solid(border)
        bs["allBorders"] = border_w
        for k in ("bordersTop", "bordersBottom", "bordersLeft", "bordersRight"):
            bs[k] = border_w
    if radius:
        n["general"]["borderRadius"] = radius
        bs = n["borderStyle"]
        bs["allCornerRadius"] = radius
        for k in ("radiusTopLeft", "radiusTopRight",
                  "radiusBottomLeft", "radiusBottomRight"):
            bs[k] = radius
    return n


def text(name, x, y, w, h, s, size, color=WHITE, weight=500,
         halign="AlignCenter", valign="AlignCenter"):
    n = base_node("Text.qml", name, x, y, w, h)
    n["effect"]["outerShadow"] = outer_shadow()
    n["text"] = {
        "text": s, "fontFamily": FONT, "fontSize": size, "fontWeight": weight,
        "fontColor": solid(color),
        "horizontalAlignment": halign, "verticalAlignment": valign,
        "wrapText": False,
        "paddingTop": 0, "paddingBottom": 0, "paddingLeft": 0, "paddingRight": 0,
    }
    n["textEffect"] = {"shadowBlur": 0, "shadowDepth": 0, "shadowDirection": 0,
                       "shadowColor": solid("#00000000")}
    return n


def lgauge(name, x, y, w, h, color, bg=BAR_BG, vmin=0, vmax=100):
    n = base_node("LinearGauge.qml", name, x, y, w, h, bg)
    n["linearGauge"] = {
        "minimum": vmin, "maximum": vmax, "value": 0,
        "gaugeOrientation": "Horizontal", "gaugeAlignment": "AlignLeft",
        "gaugeColor": solid(color),
        "gaugeImage": "", "backgroundImage": "",
        "alternateStyle": {"useAlternateStyle": False,
                           "gaugeColor": solid("#03A200"), "gaugeImage": ""},
    }
    return n


def bind(node, prop, *methods):
    node["binding"][prop] = {"type": "METHOD_CHAINING", "methods": list(methods)}
    return node


# ------------------------------------------------- telemetry expressions ----
def T(ch):
    return f'Telemetry.get("v1/gameData/{ch}").value'


# Guard idiom: NaN when no game is running; -3.4028234e+38 (-FLT_MAX) is the
# "no data" sentinel used by Pit House.
def num(ch):
    return f'Number({T(ch)})'


GUARD = "(isNaN(v)||v<-1e30||v>1e30)"


def expr_speed(unit_ch):
    return (f'((v={num(unit_ch)})=>{GUARD}?"--"'
            f':Math.round(Math.abs(v)).toString())()')


def expr_speed_color(unit_ch, limit_factor):
    # Red digits when >2 over the navigation speed limit (limit arrives in
    # km/h from Pit House, despite the catalog documenting m/s — see README).
    return (f'((s={num(unit_ch)},l={num("NavigationSpeedLimit")}*{limit_factor})=>'
            f'(!isNaN(s)&&!isNaN(l)&&l>0.5&&l<1e30&&Math.abs(s)>l+2)'
            f'?"{J_RED}":"{J_WHITE}")()')


# Pit House feeds `Gear` from the raw gearbox index (SCS `truck.engine.gear`),
# not the dashboard gear (`truck.displayed.gear`), and MOZA's catalog has no
# display-gear channel. On a 12+2 crawler box the crawlers occupy raw 1-2, so
# the HUD's top gear 12 arrives here as 14. If your gearbox has crawler gears,
# set CRAWLER_GEARS (2 for the Scania/Volvo "12+2") and rebuild: raw 1..N show
# as C1..CN and higher gears are renumbered to match the in-game HUD.
CRAWLER_GEARS = 0

_FWD_GEAR_JS = (
    (f'(v<={CRAWLER_GEARS}?"C"+Math.round(v)'
     f':Math.round(v-{CRAWLER_GEARS}).toString())')
    if CRAWLER_GEARS else 'Math.round(v).toString()')

EXPR_GEAR = (f'((v={num("Gear")})=>{{if({GUARD})return"-";'
             'if(v==0)return"N";if(v==-1)return"R";'
             'if(v<0)return"R"+Math.abs(Math.round(v));'
             f'return {_FWD_GEAR_JS};}})()')

EXPR_GEAR_COLOR = (f'((v={num("Gear")})=>{GUARD}?"{J_GRAY}"'
                   f':(v<0?"{J_AMBER}":(v==0?"{J_GRAY}":"{J_GREEN}")))()')

RPM_PCT = num("CarSettings_CurrentDisplayedRPMPercent")
EXPR_RPM_VALUE = f'((v={RPM_PCT})=>(isNaN(v)||v<0)?0:Math.min(100,v))()'
EXPR_RPM_COLOR = (f'((v={RPM_PCT})=>v>90?"{J_RED}"'
                  f':(v>75?"{J_AMBER}":"{J_CYAN}"))()')
EXPR_RPM_TEXT = (f'((v={num("Rpm")})=>(isNaN(v)||v<0||v>1e30)?""'
                 ':Math.round(v)+" rpm")()')


def expr_odometer(to_mi=False):
    conv, u = ("*0.621371", "mi") if to_mi else ("", "km")
    return (f'((v={num("Odometer")}{conv})=>(isNaN(v)||v<0||v>1e30)?""'
            f':Math.round(v)+" {u}")()')


def expr_blinker(ch):
    return (f'((b={num(ch)},h={num("HazardWarning")})=>'
            '(b==1||h==1)?1:0)()')


def expr_limit_visible():
    l = num("NavigationSpeedLimit")
    return f'((v={l})=>(!isNaN(v)&&v>0.5&&v<1e30)?1:0)()'


def expr_limit_text(factor):
    l = num("NavigationSpeedLimit")
    return (f'((v={l})=>(!isNaN(v)&&v>0.5&&v<1e30)'
            f'?Math.round(v*{factor}).toString():"")()')


def expr_cruise(ch):
    return (f'((v={num(ch)})=>(!isNaN(v)&&v>0.5&&v<1e30)'
            '?"CRUISE "+Math.round(v):"CRUISE")()')


def expr_cruise_color(ch):
    return (f'((v={num(ch)})=>(!isNaN(v)&&v>0.5&&v<1e30)'
            f'?"{J_GREEN}":"{J_DIM}")()')


FUEL = num("FuelRemainder")
EXPR_FUEL_VALUE = f'((v={FUEL})=>(isNaN(v)||v<0)?0:Math.min(100,v))()'
EXPR_FUEL_COLOR = (f'((v={FUEL})=>(isNaN(v)||v<0)?"{J_DIM}"'
                   f':(v<=10?"{J_RED}":(v<=20?"{J_AMBER}":"{J_GREEN}")))()')
EXPR_FUEL_PCT = (f'((v={FUEL})=>(isNaN(v)||v<0||v>1e30)?"--%"'
                 ':Math.round(v)+"%")()')
EXPR_FUEL_LITERS = (f'((v={num("Fuel")})=>(isNaN(v)||v<0||v>1e30)?""'
                    ':Math.round(v)+" L")()')


def expr_range(to_mi=False):
    conv, u = ("*0.621371", "mi") if to_mi else ("", "km")
    return (f'((v={num("FuelRange")}{conv})=>(isNaN(v)||v<0||v>1e30)'
            f'?"-- {u}":Math.round(v)+" {u}")()')


def expr_range_color(to_mi=False):
    conv = "*0.621371" if to_mi else ""
    low = 62 if to_mi else 100
    return (f'((v={num("FuelRange")}{conv})=>(!isNaN(v)&&v>=0&&v<{low})'
            f'?"{J_AMBER}":"{J_FAINT}")()')


def lamp_color(cond, on=J_RED):
    return f'({cond})?"{on}":"{J_DIM}"'


EXPR_PARK = lamp_color(f'{num("ParkingBrake")}==1')
EXPR_AIR = (f'((e={num("AirPressEmergency")},w={num("AirPressWarning")})=>'
            f'e==1?"{J_RED}":(w==1?"{J_AMBER}":"{J_DIM}"))()')
EXPR_OIL = (f'((s={num("EngineStarted")},p={num("OilPressure")})=>'
            f'(s==1&&!isNaN(p)&&p>=0&&p<10)?"{J_RED}":"{J_DIM}")()')
EXPR_BATT = lamp_color(f'{num("BatteryWarningVolt")}==1')
EXPR_WATER_TEXT = (f'((v={num("WaterTemp")})=>{GUARD}?"--°C"'
                   ':Math.round(v)+"°C")()')
EXPR_WATER_COLOR = (f'((w={num("WaterTempWarning")},v={num("WaterTemp")})=>'
                    f'(w==1||v>105)?"{J_AMBER}":"{J_FAINT}")()')
EXPR_DMG_TEXT = (f'((e={num("EngineDamage")},g={num("GearBoxDamage")},'
                 'm=Math.max(isNaN(e)?0:e,isNaN(g)?0:g))=>'
                 '(m<0||m>100)?"DMG":"DMG "+Math.round(m)+"%")()')
EXPR_DMG_COLOR = (f'((e={num("EngineDamage")},g={num("GearBoxDamage")},'
                  'm=Math.max(isNaN(e)?0:e,isNaN(g)?0:g))=>'
                  f'm>25?"{J_RED}":(m>5?"{J_AMBER}":"{J_DIM}"))()')
EXPR_RET_TEXT = (f'((v={num("RetarderLevel")})=>(!isNaN(v)&&v>0&&v<1e30)'
                 '?"RET "+Math.round(v):"RET")()')
EXPR_RET_COLOR = (f'((v={num("RetarderLevel")})=>(!isNaN(v)&&v>0&&v<1e30)'
                  f'?"{J_CYAN}":"{J_DIM}")()')
EXPR_BEAM = (f'((h={num("HighBeamLight")},l={num("LowBeamLight")})=>'
             f'h==1?"{J_BLUE}":(l==1?"{J_GREEN}":"{J_DIM}"))()')
EXPR_EBRAKE = lamp_color(f'{num("EngineBrake")}==1', on=J_AMBER)
# The CargoDamage channel is NOT job cargo damage: the shared-memory plugin
# Pit House reads (SDK 1.5 struct) has no cargo-damage field, and its
# wearTrailer float is bound to TRAILER_CHANNEL_wear_chassis. So this value
# is trailer chassis wear 0-1 — label it TRLR and use wear-style thresholds.
EXPR_TRAILER_TEXT = (f'((v={num("CargoDamage")})=>(isNaN(v)||v<0||v>1)?"TRLR"'
                     ':"TRLR "+Math.round(v*100)+"%")()')
EXPR_TRAILER_COLOR = (f'((v={num("CargoDamage")}*100)=>'
                      f'(isNaN(v)||v<0||v>100)?"{J_DIM}"'
                      f':(v>25?"{J_RED}":(v>5?"{J_AMBER}":"{J_DIM}")))()')


# ----------------------------------------------------------- the layout -----
def build_screen(name, mph=False):
    """One full 780x248 screen. mph=False -> km/h, True -> mph variant."""
    speed_ch = "SpeedMph" if mph else "SpeedKmh"
    cruise_ch = "CruiseControlMph" if mph else "CruiseControl"
    # NavigationSpeedLimit is documented as m/s in MOZA's catalog, but Pit
    # House delivers it already converted to km/h (a 90 km/h road reads 90,
    # not 25 — multiplying by 3.6 displayed 324).
    limit_factor = 0.621371 if mph else 1.0
    unit_label = "mph" if mph else "km/h"

    scr = base_node("Screen.qml", name, 0, 0, W, H, BG)
    scr["guides"] = []
    scr["image"] = {"src": ""}
    kids = scr["children"]

    # --- RPM bar across the top, with 25/50/75% tick shadows -------------
    g = lgauge("RPM bar", 0, 0, W, 20, "#FF00E5FF")
    bind(g, "linearGauge.value", EXPR_RPM_VALUE)
    bind(g, "linearGauge.gaugeColor", EXPR_RPM_COLOR)
    kids.append(g)
    for i in (1, 2, 3):
        kids.append(rect(f"rpm tick {i}", round(W * i / 4) - 1, 0, 2, 20,
                         "#66000000"))

    # --- info line under the bar -----------------------------------------
    t = text("rpm readout", 10, 24, 130, 22, "", 18, GRAY, halign="AlignLeft")
    bind(t, "text.text", EXPR_RPM_TEXT)
    kids.append(t)
    t = text("odometer", 530, 24, 140, 20, "", 18, GRAY, halign="AlignRight")
    bind(t, "text.text", expr_odometer(to_mi=mph))
    kids.append(t)

    # --- turn indicators (also lit by hazards) ---------------------------
    t = text("blinker L", 157, 28, 46, 42, "◀", 32, "#FF00E676", weight=700)
    bind(t, "general.visible", expr_blinker("LBlinker"))
    kids.append(t)
    t = text("blinker R", 477, 28, 46, 42, "▶", 32, "#FF00E676", weight=700)
    bind(t, "general.visible", expr_blinker("RBlinker"))
    kids.append(t)

    # --- left column: speed limit sign + cruise control ------------------
    ring = rect("limit ring", 30, 52, 70, 70, WHITE, border=LIMIT_RING,
                border_w=6, radius=35)
    bind(ring, "general.visible", expr_limit_visible())
    kids.append(ring)
    t = text("limit value", 30, 52, 70, 70, "", 30, "#FF000000", weight=700)
    bind(t, "text.text", expr_limit_text(limit_factor))
    bind(t, "general.visible", expr_limit_visible())
    kids.append(t)

    t = text("cruise", 0, 138, 150, 30, "CRUISE", 22, DIM, weight=700)
    bind(t, "text.text", expr_cruise(cruise_ch))
    bind(t, "text.fontColor", expr_cruise_color(cruise_ch))
    kids.append(t)

    # --- center: speed ----------------------------------------------------
    t = text("speed", 150, 44, 380, 132, "--", 118, WHITE, weight=700)
    bind(t, "text.text", expr_speed(speed_ch))
    bind(t, "text.fontColor", expr_speed_color(speed_ch, limit_factor))
    kids.append(t)
    kids.append(text("speed unit", 150, 172, 380, 22, unit_label, 18, GRAY))

    # --- gear box ----------------------------------------------------------
    kids.append(rect("gear panel", 540, 44, 132, 132, PANEL,
                     border=PANEL_BORDER, border_w=2, radius=14))
    t = text("gear", 540, 44, 132, 132, "-", 96, GRAY, weight=700)
    bind(t, "text.text", EXPR_GEAR)
    bind(t, "text.fontColor", EXPR_GEAR_COLOR)
    kids.append(t)

    # --- right column: fuel -----------------------------------------------
    kids.append(text("fuel label", 686, 40, 86, 18, "FUEL", 16, GRAY))
    g = lgauge("fuel bar", 686, 62, 86, 20, "#FF00E676")
    bind(g, "linearGauge.value", EXPR_FUEL_VALUE)
    bind(g, "linearGauge.gaugeColor", EXPR_FUEL_COLOR)
    kids.append(g)
    t = text("fuel pct", 686, 90, 86, 38, "--%", 30, WHITE, weight=700)
    bind(t, "text.text", EXPR_FUEL_PCT)
    bind(t, "text.fontColor", EXPR_FUEL_COLOR)
    kids.append(t)
    t = text("fuel liters", 686, 130, 86, 20, "", 15, GRAY)
    bind(t, "text.text", EXPR_FUEL_LITERS)
    kids.append(t)
    t = text("fuel range", 686, 150, 86, 20, "", 15, FAINT)
    bind(t, "text.text", expr_range(to_mi=mph))
    bind(t, "text.fontColor", expr_range_color(to_mi=mph))
    kids.append(t)

    # --- bottom warning strip ----------------------------------------------
    kids.append(rect("separator", 0, 197, W, 2, SEPARATOR))

    def lamp(name, x, w, label, color_expr, text_expr=None, size=21,
             halign="AlignCenter"):
        t = text(name, x, 205, w, 38, label, size, DIM, weight=700,
                 halign=halign)
        bind(t, "text.fontColor", color_expr)
        if text_expr:
            bind(t, "text.text", text_expr)
        kids.append(t)

    lamp("park brake", 10, 30, "P", EXPR_PARK)
    lamp("air pressure", 50, 54, "AIR", EXPR_AIR)
    lamp("oil pressure", 112, 48, "OIL", EXPR_OIL)
    lamp("battery", 166, 62, "BATT", EXPR_BATT)
    lamp("water temp", 236, 80, "--°C", EXPR_WATER_COLOR, EXPR_WATER_TEXT,
         size=20)
    lamp("damage", 324, 96, "DMG", EXPR_DMG_COLOR, EXPR_DMG_TEXT, size=20)
    lamp("engine brake", 428, 44, "EB", EXPR_EBRAKE)
    lamp("retarder", 480, 72, "RET", EXPR_RET_COLOR, EXPR_RET_TEXT, size=20)
    lamp("trailer wear", 560, 112, "TRLR", EXPR_TRAILER_COLOR,
         EXPR_TRAILER_TEXT, size=20)
    lamp("beam", 686, 86, "BEAM", EXPR_BEAM, size=20)

    return scr


def build_dashboard():
    root = base_node("Window.qml", DASH_NAME, 0, 0, W, H, BG)
    # Window root uses the minimal effect block seen in official files.
    root["effect"] = {"gravitySensorEnabled": False, "rotation": 0}
    root["version"] = "1.1.1"
    root["lastModified"] = int(time.time())
    root["window"] = {
        "GUID": "".join(random.choices(string.ascii_letters + string.digits,
                                       k=32)),
        "defaultScreenId": 0,
        "idealDeviceInfos": [{
            "deviceId": 8, "networkId": 1,
            "hardwareVersion": "RS21-W18-HW RGB-DU-V11",
            "productType": "W18 Display",
        }],
    }
    root["imageResources"] = []
    root["children"] = [
        build_screen(f"{DASH_NAME} (km/h)", mph=False),
        build_screen(f"{DASH_NAME} (mph)", mph=True),
    ]

    next_id = 0
    def assign_ids(node):
        nonlocal next_id
        node["id"] = next_id
        next_id += 1
        for c in node["children"]:
            assign_ids(c)
    assign_ids(root)
    return root


# ------------------------------------------------------------- previews -----
def render_preview(path, state):
    """Approximate render of the layout with sample telemetry values."""
    from PIL import Image, ImageDraw, ImageFont

    S = 2  # supersample
    img = Image.new("RGB", (W * S, H * S), (0, 0, 0))
    d = ImageDraw.Draw(img)
    bold = next(p for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",     # macOS
        "C:/Windows/Fonts/arialbd.ttf",                          # Windows
    ) if Path(p).exists())

    def font(px):
        return ImageFont.truetype(bold, int(px * S * 0.92))

    def c(argb):  # "#AARRGGBB"/"#RRGGBB" -> rgb tuple
        hx = argb.lstrip("#")
        if len(hx) == 8:
            hx = hx[2:]
        return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))

    def box(x, y, w, h, col, radius=0, outline=None, ow=0):
        xy = [x * S, y * S, (x + w) * S, (y + h) * S]
        d.rounded_rectangle(xy, radius=radius * S, fill=col,
                            outline=outline, width=ow * S)

    def txt(x, y, w, h, s, px, col, halign="c"):
        f = font(px)
        bb = d.textbbox((0, 0), s, font=f)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        if halign == "c":
            tx = x * S + (w * S - tw) / 2
        elif halign == "l":
            tx = x * S
        else:
            tx = (x + w) * S - tw
        ty = y * S + (h * S - th) / 2 - bb[1]
        d.text((tx, ty), s, font=f, fill=col)

    v = state
    # rpm bar
    box(0, 0, W, 20, c(BAR_BG))
    pct = v["rpm_pct"]
    bar_c = c(J_RED) if pct > 90 else c(J_AMBER) if pct > 75 else c(J_CYAN)
    box(0, 0, W * pct / 100, 20, bar_c)
    for i in (1, 2, 3):
        box(round(W * i / 4) - 1, 0, 2, 20, (0, 0, 0))
    txt(10, 24, 130, 22, f"{v['rpm']} rpm", 18, c(GRAY), "l")
    txt(530, 24, 140, 20, f"{v['odo']} km", 18, c(GRAY), "r")
    def arrow(x, y, w, h, left):
        # drawn as a polygon: preview fonts may lack the ◀/▶ glyphs
        x0, x1 = (x + w * 0.8, x + w * 0.15) if left else (x + w * 0.2,
                                                           x + w * 0.85)
        d.polygon([(x1 * S, (y + h / 2) * S), (x0 * S, (y + h * 0.12) * S),
                   (x0 * S, (y + h * 0.88) * S)], fill=c(J_GREEN))

    if v["blink_l"]:
        arrow(157, 28, 46, 42, left=True)
    if v["blink_r"]:
        arrow(477, 28, 46, 42, left=False)
    if v["limit"]:
        box(30, 52, 70, 70, c(WHITE), radius=35, outline=c(LIMIT_RING), ow=6)
        txt(30, 52, 70, 70, str(v["limit"]), 30, (0, 0, 0))
    cruise_on = v["cruise"] > 0
    txt(0, 138, 150, 30, f"CRUISE {v['cruise']}" if cruise_on else "CRUISE",
        22, c(J_GREEN) if cruise_on else c(DIM))
    over = v["limit"] and v["speed"] > v["limit"] + 2
    txt(150, 44, 380, 132, str(v["speed"]), 118,
        c(J_RED) if over else c(WHITE))
    txt(150, 172, 380, 22, "km/h", 18, c(GRAY))
    box(540, 44, 132, 132, c(PANEL), radius=14, outline=c(PANEL_BORDER), ow=2)
    gear = v["gear"]
    gc = c(J_AMBER) if gear == "R" else c(GRAY) if gear == "N" else c(J_GREEN)
    txt(540, 44, 132, 132, gear, 96, gc)
    txt(686, 40, 86, 18, "FUEL", 16, c(GRAY))
    box(686, 62, 86, 20, c(BAR_BG))
    fp = v["fuel_pct"]
    fc = c(J_RED) if fp <= 10 else c(J_AMBER) if fp <= 20 else c(J_GREEN)
    box(686, 62, 86 * fp / 100, 20, fc)
    txt(686, 90, 86, 38, f"{fp}%", 30, fc)
    txt(686, 130, 86, 20, f"{v['fuel_l']} L", 15, c(GRAY))
    txt(686, 150, 86, 20, f"{v['range']} km", 15,
        c(J_AMBER) if v["range"] < 100 else c(FAINT))
    box(0, 197, W, 2, c(SEPARATOR))

    def lamp(x, w, label, on_col, active, px=21, halign="c"):
        txt(x, 205, w, 38, label, px, on_col if active else c(DIM), halign)

    lamp(10, 30, "P", c(J_RED), v["park"])
    lamp(50, 54, "AIR", c(J_AMBER) if v["air"] == 1 else c(J_RED),
         v["air"] > 0)
    lamp(112, 48, "OIL", c(J_RED), v["oil"])
    lamp(166, 62, "BATT", c(J_RED), v["batt"])
    lamp(236, 80, f"{v['water']}°C",
         c(J_AMBER) if v["water_warn"] else c(FAINT), True, 20)
    dmg = v["dmg"]
    lamp(324, 96, f"DMG {dmg}%",
         c(J_RED) if dmg > 25 else c(J_AMBER) if dmg > 5 else c(DIM),
         True, 20)
    lamp(428, 44, "EB", c(J_AMBER), v["ebrake"])
    lamp(480, 72, f"RET {v['ret']}" if v["ret"] else "RET", c(J_CYAN),
         v["ret"] > 0, 20)
    trailer = v["trailer"]
    lamp(560, 112, f"TRLR {trailer}%" if trailer else "TRLR",
         c(J_RED) if trailer > 25 else c(J_AMBER), trailer > 5, 20)
    lamp(686, 86, "BEAM", c(J_BLUE) if v["beam"] == 2 else c(J_GREEN),
         v["beam"] > 0, 20)

    img = img.resize((W * 2, H * 2), Image.LANCZOS)
    img.save(path)


STATE_CRUISING = dict(rpm=1250, rpm_pct=48, odo=182432, blink_l=False,
                      blink_r=False, limit=80, cruise=80, speed=79, gear="9",
                      fuel_pct=64, fuel_l=448, park=False, air=0, oil=False,
                      batt=False, water=86, water_warn=False, dmg=2,
                      ebrake=False, ret=0, beam=1, range=1470, trailer=0)

STATE_WARNINGS = dict(rpm=2210, rpm_pct=94, odo=182432, blink_l=True,
                      blink_r=False, limit=60, cruise=0, speed=67, gear="7",
                      fuel_pct=8, fuel_l=56, park=True, air=1, oil=False,
                      batt=True, water=107, water_warn=True, dmg=31,
                      ebrake=True, ret=3, beam=2, range=84, trailer=12)


# ----------------------------------------------------------------- main -----
def main():
    dash = build_dashboard()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mzdash_path = OUT_DIR / f"{DASH_NAME}.mzdash"
    mzdash_path.write_text(
        json.dumps(dash, indent=1, sort_keys=True, ensure_ascii=False),
        encoding="utf-8")
    print(f"wrote {mzdash_path} ({mzdash_path.stat().st_size} bytes)")

    render_preview(OUT_DIR / "preview-cruising.png", STATE_CRUISING)
    render_preview(OUT_DIR / "preview-warnings.png", STATE_WARNINGS)
    print("wrote previews")

    zip_path = OUT_DIR.parent / "ETS2-Truck-Cluster.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT_DIR.iterdir()):
            z.write(f, f"{DASH_NAME}/{f.name}")
    print(f"wrote {zip_path}")

    # sanity checks
    n_ids = []
    def walk(n):
        n_ids.append(n["id"])
        for ch in n["children"]:
            walk(ch)
    walk(dash)
    assert len(n_ids) == len(set(n_ids)), "duplicate node ids"
    reparsed = json.loads(mzdash_path.read_text(encoding="utf-8"))
    assert reparsed["general"]["width"] == W
    print(f"OK: {len(n_ids)} nodes, ids unique, JSON round-trips")


if __name__ == "__main__":
    main()
