# NVIDIA vision system specification

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

A fixed industrial camera observes both nests after drip settle. Preliminary optics use a controlled backlight to reveal the liquid boundary and diffuse front lighting for gross bottle condition/spill evidence. The field of view must cover both bottles plus 10% calibration margin; lens selection uses sensor width × working distance / field width and remains open until bottle envelope, camera sensor and mounting distance are measured.

Model architecture: a detector/segmenter finds both bottle ROIs and gross visible defects; a calibrated fill-line estimator classifies under/in-range/over per ROI. The PLC receives bounded status and confidence only. This is not legal metrology, leak integrity testing or safety. Trigger jitter, exposure, glare, foam and transparent/product-color variations are explicit validation factors.
