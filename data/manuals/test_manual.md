# MX-104 CNC Milling Machine — OEM Service Manual (Excerpt)
Manufacturer: Axiom Industrial Systems | Model: MX-104 | Rev: 3.2

---

## Section 4: Cooling System

### 4.1 Overview
The MX-104 uses a closed-loop liquid cooling system to regulate spindle and drive temperatures during operation.
Nominal operating temperature range: 35°C–65°C. If spindle temperature exceeds 75°C, the machine triggers a thermal
fault (Error Code E-09) and halts operation.

### 4.2 Coolant Flow Rate
Minimum required flow rate: 3.5 L/min. Flow sensors are located on the inlet (P1) and outlet (P2) ports.
If P1 and P2 readings differ by more than 0.5 L/min, check for partial blockage in the cooling loop.

### 4.3 Fan Assembly
The primary cooling fan (Part #FAN-220) operates at 2800 RPM under normal load.
RPM below 2400 indicates degradation. Replace fan assembly if RPM drops below 2200.
Fan bearing lifespan: ~8000 operating hours. Log replacement in the maintenance record.

### 4.4 Lubrication of Cooling Pump
The cooling pump shaft requires lubrication every 500 operating hours using ISO VG 46 oil.
Insufficient lubrication increases pump load and indirectly raises system temperature.

---

## Section 7: Spindle Maintenance

### 7.1 Spindle Bearing Inspection
Inspect spindle bearings every 1000 operating hours. Signs of wear: unusual vibration (>2.5 mm/s RMS),
increased noise, or temperature anomaly at the spindle head.

### 7.2 Spindle Runout
Maximum allowable spindle runout: 0.005 mm. Use a dial test indicator to measure.
Runout above 0.008 mm requires immediate bearing replacement.

### 7.3 Spindle Overload
If spindle motor draws current above 18A continuously for more than 30 seconds, the overload relay trips.
Check workpiece clamping, tool condition, and feed rate before resetting.

---

## Section 11: Error Codes

| Code  | Description                        | First Action                              |
|-------|------------------------------------|-------------------------------------------|
| E-01  | Spindle overload                   | Check tool wear and feed rate             |
| E-05  | Coolant flow fault                 | Inspect flow sensors P1/P2               |
| E-09  | Thermal fault — spindle overheat   | Inspect cooling fan, coolant level        |
| E-12  | Bearing vibration threshold breach | Inspect spindle bearings                  |
| E-17  | Lubrication pressure low           | Refill lubrication reservoir              |

---

## Section 12: Scheduled Maintenance Intervals

| Interval         | Task                                      |
|------------------|-------------------------------------------|
| Every 250 hrs    | Check coolant level and clarity           |
| Every 500 hrs    | Lubricate cooling pump shaft              |
| Every 1000 hrs   | Inspect spindle bearings and fan RPM      |
| Every 2000 hrs   | Full spindle teardown and bearing repack  |
| Every 8000 hrs   | Replace fan assembly (Part #FAN-220)      |
