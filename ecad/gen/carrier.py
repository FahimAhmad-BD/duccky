"""Duccky v1.0 trunk carrier board: circuit definition.

Run:  python carrier.py   (writes ecad/carrier/carrier.kicad_sch)

Component values trace to the datasheet sections cited next to each block and are
summarised in docs/02_electrical.md section 4. Net names are the design record:
every pin connects by label, so the schematic doubles as a readable netlist.
"""
from pathlib import Path

from kicadlib import load_symbol, make_symbol
from schgen import NC, Block, Part, Schematic

OUT = Path(__file__).resolve().parents[1] / "carrier"

# Footprints
R0402, C0402, C0603, C0805, C1206, C1210 = (
    "Resistor_SMD:R_0402_1005Metric", "Capacitor_SMD:C_0402_1005Metric",
    "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric",
    "Capacitor_SMD:C_1206_3216Metric", "Capacitor_SMD:C_1210_3225Metric")
R2010 = "Resistor_SMD:R_2010_5025Metric"

SYM = {k: load_symbol(v) for k, v in {
    "R": "Device:R", "C": "Device:C", "L": "Device:L", "FLAG": "power:PWR_FLAG",
    "BUCK12": "Regulator_Switching:TPS568215RNN", "BUCK3": "Regulator_Switching:TPS62933",
    "CHG": "Battery_Management:BQ25887RGE", "AMP": "Audio:MAX98357A",
    "BUF": "74xGxx:74LVC2G241", "ADC": "Analog_ADC:ADS1115IDGS",
    "LDO": "Regulator_Linear:TLV75533PDBV", "USBC": "Connector:USB_C_Receptacle_USB2.0_16P",
    "HDR40": "Connector_Generic:Conn_02x20_Odd_Even",
    "C2": "Connector_Generic:Conn_01x02", "C3": "Connector_Generic:Conn_01x03",
    "C10": "Connector_Generic:Conn_01x10", "MH": "Mechanical:MountingHole",
}.items()}

# Custom symbols (pinouts from the cited datasheets)
SYM["EFUSE"] = make_symbol(
    "duccky:TPS25982", "U", "TPS259824LNRGE",
    "duccky:Texas_RGE0024M_TPS25982", "https://www.ti.com/lit/ds/symlink/tps25982.pdf",
    "15 A eFuse, 2.7 to 24 V, OVLO 16.9 V, active current limit (TI SLVSEI3D Table 5-1)",
    left=[("1", "IN", "power_in"), ("2", "IN", "passive"), ("3", "IN", "passive"), ("16", "IN", "passive"),
          ("25", "IN_PAD", "passive"), None, ("6", "EN/UVLO", "input"), ("12", "LDSTRT", "input"),
          None, ("4", "GND", "power_in"), ("5", "GND", "passive"), ("14", "GND", "passive"), ("26", "GND_PAD", "passive")],
    right=[("17", "OUT", "power_out"), ("18", "OUT", "passive"), ("19", "OUT", "passive"), ("20", "OUT", "passive"),
           ("21", "OUT", "passive"), ("22", "OUT", "passive"), ("23", "OUT", "passive"), ("24", "OUT", "passive"),
           ("13", "PG", "open_collector"), ("9", "IMON", "output"), ("8", "ILIM", "passive"),
           ("7", "ITIMER", "passive"), ("15", "dVdt", "passive"), ("10", "RETRY_DLY", "passive"), ("11", "NRETRY", "passive")],
    width=20.32)
SYM["IMU"] = make_symbol(
    "duccky:BNO085", "U", "BNO085", "Package_LGA:LGA-28_5.2x3.8mm_P0.5mm",
    "https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf",
    "9 axis IMU with sensor fusion (CEVA 1000-3927 v1.17 Figure 1-6)",
    left=[("3", "VDD", "power_in"), ("28", "VDDIO", "power_in"), ("9", "CAP", "passive"), None,
          ("4", "BOOTN", "input"), ("5", "PS1", "input"), ("6", "PS0/WAKE", "input"), ("18", "H_CSN", "input"),
          ("17", "SA0", "input"), ("10", "CLKSEL0", "input"), ("11", "NRST", "input"), None,
          ("2", "GND", "power_in"), ("25", "GND", "passive")],
    right=[("19", "H_SCL", "bidirectional"), ("20", "H_SDA", "bidirectional"), ("14", "H_INTN", "output"), None,
           ("15", "ENV_SCL", "bidirectional"), ("16", "ENV_SDA", "bidirectional"), None,
           ("27", "XIN32", "input"), ("26", "XOUT32/CLKSEL1", "passive"), None,
           ("1", "RESV_NC", "no_connect"), ("7", "RESV_NC", "no_connect"), ("8", "RESV_NC", "no_connect"),
           ("12", "RESV_NC", "no_connect"), ("13", "RESV_NC", "no_connect"), ("21", "RESV_NC", "no_connect"),
           ("22", "RESV_NC", "no_connect"), ("23", "RESV_NC", "no_connect"), ("24", "RESV_NC", "no_connect")],
    width=20.32)

_count = {}


def ref(prefix):
    _count[prefix] = _count.get(prefix, 0) + 1
    return f"{prefix}{_count[prefix]}"


def R(value, a, b, fp=R0402, **kw):
    return Part(ref("R"), SYM["R"], value, fp, {1: a, 2: b}, **kw)


def C(value, a, b="GND", fp=C0402, **kw):
    return Part(ref("C"), SYM["C"], value, fp, {1: a, 2: b}, **kw)


def L(value, a, b, fp, mpn):
    return Part(ref("L"), SYM["L"], value, fp, {1: a, 2: b}, fields={"MPN": mpn})


def FLAG(net):
    return Part(ref("#FLG"), SYM["FLAG"], "PWR_FLAG", "", {1: net})


def build():
    sch = Schematic("carrier", "Duccky v1.0 trunk carrier board", "A", paper="A0")
    W = 1120

    # ---- Battery input, main switch and eFuse (TI TPS25982, SLVSEI3D sections 8.2.2.2 to 8.2.2.8)
    b = Block(sch, "1  Battery input and eFuse (TPS259824LNRGE)", 20, 20, W)
    b.add(Part(ref("J"), SYM["C2"], "XT30PW-M battery", "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal",
               {1: "VBAT", 2: "GND"}, fields={"MPN": "Amass XT30PW-M"}))
    b.add(Part(ref("J"), SYM["C2"], "Cell sense: MID, NTC", "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal",
               {1: "BAT_MID", 2: "BAT_NTC"}, fields={"MPN": "JST SM02B-GHS-TB"}))
    b.add(Part(ref("J"), SYM["C2"], "Main switch", "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal",
               {1: "VBAT", 2: "PWR_SW"}, fields={"MPN": "JST SM02B-GHS-TB"}))
    for _ in range(2):
        b.add(C("10uF 25V", "VBAT", fp=C1206))
    b.add(Part(ref("U"), SYM["EFUSE"], "TPS259824LNRGE", "duccky:Texas_RGE0024M_TPS25982",
               {1: "VBAT", 2: "VBAT", 3: "VBAT", 16: "VBAT", 25: "VBAT",
                4: "GND", 5: "GND", 14: "GND", 26: "GND",
                17: "VSYS", 18: "VSYS", 19: "VSYS", 20: "VSYS", 21: "VSYS", 22: "VSYS", 23: "VSYS", 24: "VSYS",
                6: "EFUSE_EN", 12: "GND", 13: NC, 9: "IMON", 8: "EFUSE_ILIM", 7: "EFUSE_ITIMER",
                15: "EFUSE_DVDT", 10: "GND", 11: "GND"}))
    # UVLO: 1.2 V x (1 M + 232 k) / 232 k = 6.37 V rising, 5.84 V falling (Equation 17)
    b.add(R("1M", "PWR_SW", "EFUSE_EN"))
    b.add(R("232k", "EFUSE_EN", "GND"))
    b.add(R("100", "EFUSE_ILIM", "GND"))                       # 14.7 A typical, 12.85 A minimum (Eq. 16)
    b.add(C("4.7nF", "EFUSE_ITIMER"))                          # 2 ms overcurrent blanking (Eq. 30)
    b.add(C("10nF", "EFUSE_DVDT"))                             # 0.46 V/ms output slew (Eq. 24)
    b.add(R("887", "IMON", "GND"))                             # 14.7 A -> 3.21 V into the ADC (Eq. 18)
    b.add(C("1nF", "IMON"))
    for _ in range(2):
        b.add(C("10uF 25V", "VSYS", fp=C1206))
    y = b.bottom() + 10

    # ---- Servo rail 5.0 V, 12 A (TI TPS56C215, SLVSD05H Table 6-3 and Table 7-2)
    b = Block(sch, "2  Servo rail 5.0 V 12 A (TPS56C215RNNR); EN is the hardware torque enable", 20, y, W)
    b.add(Part(ref("U"), SYM["BUCK12"], "TPS56C215RNNR", "Package_DFN_QFN:Texas_RNN0018A",
               {2: "VSYS", 11: "VSYS", 3: "GND", 4: "GND", 5: "GND", 8: "GND", 9: "GND", 10: "GND", 12: "GND",
                6: "SW_SERVO", 7: "SW_SERVO", 1: "BOOT_SERVO", 13: "FB_SERVO", 14: NC, 15: "TORQUE_EN",
                16: NC, 17: "VREG5_SERVO", 18: "MODE_SERVO"},
               fields={"MPN": "TPS56C215RNNR", "Note": "Symbol TPS568215RNN, pin to pin compatible per TI"}))
    b.add(R("100k", "TORQUE_EN", "GND"))                       # rail stays off until the runtime enables it
    b.add(C("0.1uF", "BOOT_SERVO", "SW_SERVO"))
    b.add(C("4.7uF", "VREG5_SERVO"))
    b.add(R("120k", "VREG5_SERVO", "MODE_SERVO"))              # FCCM, ILIM (12 A), 800 kHz
    b.add(R("20k", "MODE_SERVO", "GND"))
    b.add(L("2.2uH", "SW_SERVO", "V5_SERVO", "Inductor_SMD:L_Coilcraft_XAL7030-222", "Coilcraft XAL7030-222"))
    b.add(R("73.2k", "V5_SERVO", "FB_SERVO"))                  # 0.6 x (1 + 73.2/10) = 4.99 V (Eq. 6)
    b.add(R("10k", "FB_SERVO", "GND"))
    b.add(C("150pF", "V5_SERVO", "FB_SERVO"))                  # CFF 100 to 220 pF (Table 7-2)
    for _ in range(4):
        b.add(C("10uF 25V", "VSYS", fp=C1206))                 # 40 uF input (7.2.2.2.5)
    for _ in range(4):
        b.add(C("47uF 10V", "V5_SERVO", fp=C1210))             # 88 to 500 uF output (Table 7-2)
    y = b.bottom() + 10

    # ---- Compute rail 5.0 V, 3 A (TI TPS62933, SLUSEA4D Figure 10-1 and Table 10-2)
    b = Block(sch, "3  Compute rail 5.0 V 3 A (TPS62933DRLR) and 3.3 V LDO (TLV75533PDBVR)", 20, y, W)
    b.add(Part(ref("U"), SYM["BUCK3"], "TPS62933DRLR", "Package_TO_SOT_SMD:SOT-583-8",
               {3: "VSYS", 4: "GND", 5: "SW_SYS", 6: "BST_SYS", 8: "FB_SYS", 7: "SS_SYS", 2: NC, 1: NC},
               fields={"MPN": "TPS62933DRLR"}))
    b.add(C("0.1uF", "BST_SYS", "SW_SYS"))
    b.add(C("33nF", "SS_SYS"))                                 # 5 ms soft start
    b.add(L("6.8uH", "SW_SYS", "V5_SYS", "Inductor_SMD:L_Coilcraft_XAL5030-XXX", "6.8 uH, Isat >= 5.8 A"))
    b.add(R("53.6k", "V5_SYS", "FB_SYS"))
    b.add(R("10.2k", "FB_SYS", "GND"))
    for _ in range(2):
        b.add(C("10uF 25V", "VSYS", fp=C1206))
    b.add(C("0.1uF", "VSYS"))
    for _ in range(2):
        b.add(C("22uF 10V", "V5_SYS", fp=C1206))
    b.add(C("0.1uF", "V5_SYS"))
    b.add(Part(ref("U"), SYM["LDO"], "TLV75533PDBVR", "Package_TO_SOT_SMD:SOT-23-5",
               {1: "V5_SYS", 2: "GND", 3: "V5_SYS", 4: NC, 5: "3V3"}, fields={"MPN": "TLV75533PDBVR"}))
    b.add(C("1uF", "V5_SYS"))
    b.add(C("1uF", "3V3"))
    for net in ("GND", "V5_SYS", "V5_SERVO"):
        b.add(FLAG(net))
    y = b.bottom() + 10

    # ---- USB-C charge input and BQ25887 (TI SLUSD89B Figure 69)
    b = Block(sch, "4  USB-C charge input and 2S charger (BQ25887RGER)", 20, y, W)
    b.add(Part(ref("J"), SYM["USBC"], "USB-C charge", "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
               {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "USB_CC1", "B5": "USB_CC2",
                "A6": NC, "A7": NC, "B6": NC, "B7": NC, "A8": NC, "B8": NC,
                "A1": "GND", "B1": "GND", "A12": "GND", "B12": "GND", "SH": "GND"},
               fields={"MPN": "GCT USB4105-GF-A"}))
    b.add(R("5.1k", "USB_CC1", "GND"))                         # sink advertisement
    b.add(R("5.1k", "USB_CC2", "GND"))
    b.add(FLAG("VBUS"))
    b.add(Part(ref("U"), SYM["CHG"], "BQ25887RGER", "Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
               {23: "VBUS", 21: "CHG_PMID", 22: "CHG_PMID", 17: "CHG_SW", 18: "CHG_SW", 12: "CHG_BTST",
                11: "CHG_REGN", 15: "CHG_SNS", 16: "CHG_SNS", 13: "VBAT", 14: "VBAT",
                9: "CHG_MID", 10: "CHG_CBSET", 7: "CHG_TS", 8: "CHG_ILIM",
                4: "I2C4_SDA", 5: "I2C4_SCL", 6: "CHG_INT", 1: "CHG_PG", 2: NC, 3: "GND", 24: "GND",
                19: "GND", 20: "GND", 25: "GND"}, fields={"MPN": "BQ25887RGER"}))
    b.add(C("1uF 25V", "VBUS", fp=C0603))
    for _ in range(2):
        b.add(C("22uF 25V", "CHG_PMID", fp=C1206))             # 44 uF recommended on PMID (9.2.2.2)
    b.add(L("1uH", "CHG_PMID", "CHG_SW", "Inductor_SMD:L_1008_2520Metric", "Murata DFE252012F-1R0M"))
    b.add(C("47nF", "CHG_BTST", "CHG_SW"))
    b.add(C("4.7uF", "CHG_REGN"))
    for _ in range(2):
        b.add(C("22uF 16V", "CHG_SNS", fp=C1206))              # 44 uF on SNS (9.2.2.3)
    b.add(C("10uF 16V", "VBAT", fp=C0805))
    b.add(R("300", "BAT_MID", "CHG_MID"))                      # reverse cell protection (Figure 69 note)
    b.add(R("47", "BAT_MID", "CHG_CBSET", fp=R2010))           # 4.2 / 48 = 88 mA balancing, 0.36 W
    b.add(R("5.23k", "CHG_REGN", "CHG_TS"))                    # 103AT-2 window (8.2, RT1 and RT2)
    b.add(R("30.1k", "CHG_TS", "GND"))
    b.add(R("0", "BAT_NTC", "CHG_TS"))
    b.add(R("750", "CHG_ILIM", "GND"))                         # 1110 / 750 = 1.48 A input limit
    b.add(R("10k", "CHG_INT", "3V3"))
    b.add(R("10k", "CHG_PG", "3V3"))
    y = b.bottom() + 10

    # ---- Computer header (Radxa ZERO 3W, DCK-02 section 3.3)
    b = Block(sch, "5  Radxa ZERO 3W socket, debug UART and analog monitor (ADS1115IDGSR)", 20, y, W)
    hdr = {1: NC, 17: NC, 2: "V5_SYS", 4: "V5_SYS",
           6: "GND", 9: "GND", 14: "GND", 20: "GND", 25: "GND", 30: "GND", 34: "GND", 39: "GND",
           3: "UART3_RX", 5: "UART3_TX", 16: "UART4_RX", 18: "UART4_TX", 33: "UART5_RX", 32: "UART5_TX",
           7: "BUS1_DIR", 11: "BUS2_DIR", 15: "BUS3_DIR", 27: "I2C4_SDA", 28: "I2C4_SCL",
           29: "I2C5_SCL", 31: "I2C5_SDA", 12: "I2S_SCLK", 35: "I2S_LRCK", 40: "I2S_SDO", 38: "I2S_SDI",
           36: "TORQUE_EN", 22: "IMU_INT", 37: "IMU_RST", 19: "TOF_INT", 23: "TOF_LPN",
           21: "AMP_SD", 24: "CHG_INT", 8: "DBG_TX", 10: "DBG_RX", 13: NC, 26: NC}
    b.add(Part(ref("J"), SYM["HDR40"], "Radxa ZERO 3W", "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical", hdr))
    b.add(Part(ref("J"), SYM["C3"], "Debug UART", "Connector_JST:JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal",
               {1: "DBG_TX", 2: "DBG_RX", 3: "GND"}, fields={"MPN": "JST SM03B-SRSS-TB"}))
    b.add(Part(ref("U"), SYM["ADC"], "ADS1115IDGSR", "Package_SO:TSSOP-10_3x3mm_P0.5mm",
               {1: "GND", 2: NC, 3: "GND", 4: "IMON", 5: "VSYS_SENSE", 6: "V5_SERVO_SENSE", 7: "BAT_MID_SENSE",
                8: "3V3", 9: "I2C4_SDA", 10: "I2C4_SCL"}, fields={"MPN": "ADS1115IDGSR"}))
    b.add(C("0.1uF", "3V3"))
    b.add(R("100k", "VSYS", "VSYS_SENSE"))                     # 8.4 V -> 2.08 V
    b.add(R("33k", "VSYS_SENSE", "GND"))
    b.add(R("10k", "V5_SERVO", "V5_SERVO_SENSE"))              # 5.0 V -> 2.5 V
    b.add(R("10k", "V5_SERVO_SENSE", "GND"))
    b.add(R("100k", "BAT_MID", "BAT_MID_SENSE"))               # 4.2 V -> 2.1 V
    b.add(R("100k", "BAT_MID_SENSE", "GND"))
    b.add(R("2.2k", "I2C5_SDA", "3V3"))
    b.add(R("2.2k", "I2C5_SCL", "3V3"))
    b.add(R("2.2k", "I2C4_SDA", "3V3", dnp=True))              # ZERO 3W has pull-ups on pins 27 and 28
    b.add(R("2.2k", "I2C4_SCL", "3V3", dnp=True))
    y = b.bottom() + 10

    # ---- Servo bus: three half duplex TTL chains (74LVC2G241, ROBOTIS 3.3 V TTL bus)
    b = Block(sch, "6  Servo bus: three half duplex TTL chains (74LVC2G241DCUR)", 20, y, W)
    for n in (1, 2, 3):
        uart = {1: "UART3", 2: "UART4", 3: "UART5"}[n]
        b.add(Part(ref("U"), SYM["BUF"], "74LVC2G241DCUR", "Package_SO:VSSOP-8_2.3x2mm_P0.5mm",
                   {1: f"BUS{n}_DIR", 2: f"{uart}_TX", 6: f"BUS{n}_DATA",
                    7: f"BUS{n}_DIR", 5: f"BUS{n}_DATA", 3: f"{uart}_RX", 8: "3V3", 4: "GND"},
                   fields={"MPN": "SN74LVC2G241DCUR"}))
        b.add(C("0.1uF", "3V3"))
        b.add(R("10k", f"BUS{n}_DIR", "3V3"))                  # default: receive, transmitter off
        b.add(R("10k", f"BUS{n}_DATA", "3V3"))                 # bus idle high
        for k in (1, 2):
            b.add(Part(ref("J"), SYM["C3"], f"Servo chain {n}", "Connector_JST:JST_EH_B3B-EH-A_1x03_P2.50mm_Vertical",
                       {1: "GND", 2: "V5_SERVO", 3: f"BUS{n}_DATA"}, fields={"MPN": "JST B3B-EH-A"}))
    y = b.bottom() + 10

    # ---- Audio out and IMU
    b = Block(sch, "7  Speaker amplifier (MAX98357AETE+T) and trunk IMU (BNO085)", 20, y, W)
    b.add(Part(ref("U"), SYM["AMP"], "MAX98357AETE+T", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm",
               {1: "I2S_SDO", 16: "I2S_SCLK", 14: "I2S_LRCK", 4: "AMP_SDMODE", 2: "V5_SYS",
                7: "V5_SYS", 8: "V5_SYS", 3: "GND", 11: "GND", 15: "GND", 17: "GND",
                9: "SPK_P", 10: "SPK_N", 5: NC, 6: NC, 12: NC, 13: NC}, fields={"MPN": "MAX98357AETE+T"}))
    b.add(R("634k", "AMP_SD", "AMP_SDMODE"))                   # (L+R)/2 at 3.3 V logic (Table 6); low = shutdown
    b.add(C("0.1uF", "V5_SYS"))
    b.add(C("10uF", "V5_SYS", fp=C0805))
    b.add(Part(ref("J"), SYM["C2"], "Speaker CMS-18132-18SP", "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal",
               {1: "SPK_P", 2: "SPK_N"}, fields={"MPN": "JST SM02B-GHS-TB"}))
    b.add(Part(ref("U"), SYM["IMU"], "BNO085", "Package_LGA:LGA-28_5.2x3.8mm_P0.5mm",
               {3: "3V3", 28: "3V3", 9: "IMU_CAP", 4: "IMU_BOOTN", 5: "GND", 6: "GND", 18: "GND", 17: "GND",
                10: "IMU_CLKSEL0", 11: "IMU_RST", 2: "GND", 25: "GND",
                19: "I2C4_SCL", 20: "I2C4_SDA", 14: "IMU_INT", 15: "IMU_ENV_SCL", 16: "IMU_ENV_SDA",
                27: NC, 26: NC}, fields={"MPN": "BNO085"}))
    b.add(C("0.1uF", "3V3"))
    b.add(C("0.1uF", "3V3"))
    b.add(C("0.1uF", "IMU_CAP"))
    b.add(R("10k", "IMU_BOOTN", "3V3"))
    b.add(R("10k", "IMU_CLKSEL0", "3V3"))                      # internal oscillator: CLKSEL0 = 1, CLKSEL1 open
    b.add(R("10k", "IMU_RST", "3V3"))
    b.add(R("10k", "IMU_INT", "3V3"))
    b.add(R("2.2k", "IMU_ENV_SCL", "3V3"))                     # required even with no sensor attached
    b.add(R("2.2k", "IMU_ENV_SDA", "3V3"))
    y = b.bottom() + 10

    # ---- Head board link and mounting
    b = Block(sch, "8  Head board link (camera FPC runs direct from the computer) and mounting", 20, y, W)
    b.add(Part(ref("J"), SYM["C10"], "Head board", "Connector_JST:JST_GH_SM10B-GHS-TB_1x10-1MP_P1.25mm_Horizontal",
               {1: "V5_SYS", 2: "GND", 3: "I2C5_SDA", 4: "I2C5_SCL", 5: "TOF_INT", 6: "TOF_LPN",
                7: "I2S_SCLK", 8: "I2S_LRCK", 9: "I2S_SDI", 10: "GND"}, fields={"MPN": "JST SM10B-GHS-TB"}))
    for _ in range(4):
        b.add(Part(ref("H"), SYM["MH"], "M2.5", "MountingHole:MountingHole_2.7mm_M2.5", {}))

    sch.write(OUT / "carrier.kicad_sch")
    return sch


LIB_TABLES = {
    "sym-lib-table": '(sym_lib_table\n\t(version 7)\n\t(lib (name "duccky") (type "KiCad") '
                     '(uri "${KIPRJMOD}/../lib/duccky.kicad_sym") (options "") (descr "Duccky custom symbols"))\n)\n',
    "fp-lib-table": '(fp_lib_table\n\t(version 7)\n\t(lib (name "duccky") (type "KiCad") '
                    '(uri "${KIPRJMOD}/../lib/duccky.pretty") (options "") (descr "Duccky custom footprints"))\n)\n',
}


if __name__ == "__main__":
    import library
    OUT.mkdir(parents=True, exist_ok=True)
    library.write_symbols([SYM["EFUSE"], SYM["IMU"]])
    library.write_footprints()
    for name, text in LIB_TABLES.items():
        (OUT / name).write_text(text, encoding="utf-8")
    pro = OUT / "carrier.kicad_pro"
    if not pro.exists():
        pro.write_text('{\n  "meta": {"filename": "carrier.kicad_pro", "version": 3}\n}\n', encoding="utf-8")
    s = build()
    print(f"{len(s.parts)} parts written to {OUT / 'carrier.kicad_sch'}")
