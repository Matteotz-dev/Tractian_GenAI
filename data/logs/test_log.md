# Maintenance Log — Machine: MX-104 | Company: Apex Manufacturing

---

## Incident #LOG-0041
**Date:** 2024-03-12
**Machine:** MX-104
**Technician:** R. Souza
**Issue:** Machine halted mid-job with Error E-09 (thermal fault). Spindle temperature reached 81°C.
**Diagnosis:** Fan RPM measured at 2150 — below minimum threshold of 2200. Coolant level was adequate.
**Resolution:** Replaced fan assembly (Part #FAN-220). Machine returned to normal operation.
**Downtime:** 3.5 hours

---

## Incident #LOG-0055
**Date:** 2024-05-28
**Machine:** MX-104
**Technician:** D. Lima
**Issue:** Recurring E-09 errors over two days. Temperature not critically high (72°C) but triggering intermittent faults.
**Diagnosis:** Coolant flow sensors showed P1=3.2 L/min, P2=2.6 L/min — delta of 0.6 L/min exceeding 0.5 threshold.
Partial blockage found in cooling loop at elbow joint near the spindle head.
**Resolution:** Flushed cooling loop, cleared debris blockage. Flow rates normalized (P1=3.7, P2=3.6).
**Downtime:** 1.5 hours

---

## Incident #LOG-0063
**Date:** 2024-07-09
**Machine:** MX-104
**Technician:** R. Souza
**Issue:** E-09 fault after 4 hours of operation on a high-load job. Spindle temperature hit 78°C.
**Diagnosis:** Pump lubrication overdue — last logged at 420 hours, currently at 530 hours.
Pump running under increased load, raising system temperature.
**Resolution:** Lubricated cooling pump shaft with ISO VG 46. Temperature stabilized within 30 minutes.
**Downtime:** 1 hour

---

## Incident #LOG-0071
**Date:** 2024-09-15
**Machine:** MX-104
**Technician:** A. Costa
**Issue:** E-12 fault triggered. Vibration alarm during spindle run-up.
**Diagnosis:** Spindle vibration measured at 3.1 mm/s RMS (threshold: 2.5 mm/s). Bearing inspection showed
early-stage wear on front bearing.
**Resolution:** Replaced front spindle bearing. Vibration returned to 1.2 mm/s RMS post-replacement.
**Downtime:** 6 hours

---

## Incident #LOG-0078
**Date:** 2024-11-02
**Machine:** MX-104
**Technician:** D. Lima
**Issue:** Machine overheating after approximately 2 hours of runtime. Temperature climbing steadily to 77°C.
**Diagnosis:** Fan RPM read 2380 — still above 2200 minimum but degraded from nominal 2800 RPM.
Coolant level normal. No blockage detected. Fan assessed as approaching end of life.
**Resolution:** Replaced fan assembly (Part #FAN-220) as a precautionary measure. RPM restored to 2790.
**Downtime:** 2 hours
**Note:** This is the second fan replacement in 8 months. Review whether operating hours are being logged
correctly for scheduled replacement intervals.
