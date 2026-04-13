# Active Filter design program
**Version 1.0 - Professionelt værktøj til design og analyse af aktive analoge filtre**

## 1. INTRODUKTION
Dette program er udviklet til design, analyse og simulering af aktive analoge filtre. Systemet
understøtter Butterworth og Chebyshev approksimationer og er opdelt i to specialiserede moduler:
- **Sallen-Key:** Modul til Lavpas (LP) og Højpas (HP) designs.
- **Multiple Feedback (MFB):** Modul til Båndpas (BP) designs.

Aktive filtre spiller fortsat en central rolle i moderne elektronikdesign,
på trods af den massive udbredelse af digitale filtre(IIR/FIR). 
Mens software-baserede filtre tilbyder fleksibilitet, findes der stadig
mange applikationer hvor aktive hardware-filtre er uundværlige.

Typiske anvendelsesområder inkluderer:
• Anti-aliasing før A/D-konvertere
• Båndpasfiltre i RF-modtagere og sendere
• Equalizere i audioforstærkere og studieudstyr
• Strømforsyningsfiltrering og støjundertrykkelse
• Biotech signalbehandling (EKG, EEG)
• Sensorinterface og tilstandsovervågning
• Hastighedskritiske realtidsapplikationer

Aktive filtre tilbyder unikke fordele: lav outputimpedans, forstærkning,
justerbare parametre uden komponentudskiftning, og minimal belastning af
signalkilder. De undgår desuden behovet for tunge og dyre spoler.

## 1.1 PAKKENS INDHOLD OG FORMATER
For at sikre maksimal fleksibilitet i det tekniske arbejdsflow, inkluderer denne pakke:
- **Python Program:** Den fulde pakke med grafisk brugerflade (GUI) til lokal kørsel.
- **HTML/Webapp Version:** En browser-baseret udgave til hurtig adgang uden installation.
- **MATLAB Version:** Scripts og funktioner til direkte brug i professionelle simuleringsmiljøer.

## 2. INSTALLATION OG SYSTEMKRAV
For at køre programpakken skal Python være installeret sammen med følgende biblioteker:
- **PySide6:** Håndterer brugerfladen.
- **NumPy:** Håndterer matematiske beregninger.
- **Matplotlib:** Genererer de tekniske grafer.

Installation via terminal:
`pip install PySide6 numpy matplotlib`

## 3. FILSTRUKTUR
For at systemet fungerer korrekt, skal følgende tre filer placeres i den samme mappe:
- `filter_designer_main.py` (Hovedmenu / Launcher)
- `sklphp.py` (Sallen-Key modul til Lavpas og Højpas)
- `mfbp.py` (Multiple Feedback modul til Båndpas)

**VIGTIGT:** Start altid programmet ved at køre `activefilter.py`.

## 4. BESKRIVELSE AF MODULER
### Sallen-Key (LP / HP)
- Bruges til Lavpas- og Højpas-designs.
- Ideelt til Unity Gain (0 dB) applikationer.
- Meget stabilt ved lave Q-faktorer.

### Multiple Feedback (BP)
- Bruges udelukkende til Båndpas-designs.
- Inkluderer "Auto-Gain Compensation", der modvirker det naturlige tab ved centerfrekvensen.
- Velegnet til højere Q-faktorer (smalle båndbredder).

## 5. TRIN-FOR-TRIN DESIGNGUIDE
1. Start Launcheren og vælg den ønskede filtertype.
2. Indtast specifikationer: Knækfrekvens (fc) eller båndgrænser (fn, fø) samt ønsket dæmpning.
3. Vælg komponent-normalisering: Vælg en E-række (f.eks. E24 eller E96).
4. Klik på "Beregn Filter Design": Programmet udregner filterorden og komponentværdier.
5. Kontroller stabilitet: Se statusfeltet for advarsler om høje Q-faktorer.

## 6. FORKLARING AF TEKNISKE GRAFER
Programmet genererer fire visuelle analyser:
- **Magnitude (Bodeplot):** Viser forstærkning i dB over frekvens.
- **Fase / Delay:** Viser signalets faseforskydning og forsinkelse.
- **S-Plan (Poler):** Viser filterets poler. Alle krydser skal være i venstre halvplan.
- **Gruppeløbetid:** Viser tidsforsinkelsen gennem filtret i ms. Toppe indikerer resonans.

## 7. SPICE EKSPORT OG SIMULERING
Programmet kan eksportere en .cir netliste til brug i LTspice eller PSpice.
- Netlisten bruger ideelle OPAMP-modeller (E-kilder) med et gain på 1.000.000.
- Ved praktisk brug bør "IDEAL_OP" udskiftes med en specifik model (f.eks. TL072 eller OP27).

## 8. GUIDE TIL VALG AF OPERATIONSFORSTÆRKER
Valget af OPAMP afhænger af din applikation. 
VALG AF OPERATIONSFORSTÆRKER TYPE

1. Rail-to-Rail Operationsforstærker (MCP6002, LMV321)
Karakteristika:

    Input/output kan swinge tæt på V+ og V- forsyninger
    Maksimalt dynamisk output-område ved lav spænding
    Ofte CMOS-teknologi med lavt strømforbrug

Typiske anvendelser:

    Single-supply systemer (0-3.3V eller 0-5V)
    Batteridrevne enheder og IoT-sensorer
    ADC-buffering for maksimal udnyttelse af range
    Portable audio og sensor signal-conditioning

Når du skal vælge den:

    Forsyningsspænding er lav (< 5V)
    Du har brug for maksimalt output-swing
    Design uden negativ forsyning (single-supply)

2. JFET-Input Operationsforstærker (TL072, TL084)
Karakteristika:

    Meget høj input-impedans (Gigaohm-området)
    Lav input bias-strøm (picoampere)
    Lav støj i mellemfrekvens-området
    God slew rate sammenlignet med bipolare typer

Typiske anvendelser:

    Aktive filtre og integrator-kredsløb
    Buffer-trin til høj-impedans sensorer
    Audio forforstærkere og mixere
    Sample-and-hold kredsløb

Når du skal vælge den:

    Kilden har høj output-impedans
    Lav input bias-strøm er kritisk
    Du skal minimere loading af signalkilden

3. Præcisions Operationsforstærker (OP07, OP177)
Karakteristika:

    Ekstremt lav offset-spænding (mikrovolt)
    Lav drift over temperatur og tid
    Høj CMRR og PSRR (støjafvisning)
    God linearitet og lav forvrængning

Typiske anvendelser:

    Præcisions måleinstrumenter og DMM
    Strøm-sensing med shunt-modstande
    Sensor-interface (termoelementer, strain gauge)
    Laboratorieudstyr og kalibreringskredsløb

Når du skal vælge den:

    Præcision er vigtigere end hastighed/strøm
    Målinger kræver mikrovolt-nøjagtighed
    Temperaturdrift skal minimeres

4. Højhastigheds Operationsforstærker (AD8051, LMH6629)
Karakteristika:

    Høj slew rate (>100 V/µs) og bred båndbredde
    Lav forvrængning ved høje frekvenser
    Ofte current-feedback arkitektur
    Kræver omhyggelig PCB-layout for stabilitet

Typiske anvendelser:

    Video-forstærkere og ADC-drivere
    Kommunikationssystemer og RF-mellemtrin
    Pulsforstærkning og hurtig switching
    Oscilloskoper og testudstyr

Når du skal vælge den:

    Signalfrekvens > 1 MHz eller hurtige pulser
    Du har brug for høj slew rate
    Båndbredde skal bevares ved højt gain

5. Lavstøjs Operationsforstærker (NE5532, OP27)
Karakteristika:

    Minimere termisk og 1/f støj (nV/√Hz)
    Lav total harmonic distortion (THD)
    God støjfigur i audio-frekvensbåndet
    Ofte bipolær input-trin for lav spændingsstøj

Typiske anvendelser:

    Mikrofonforstærkere og pickup preamps
    Medicinsk udstyr (EKG, EEG, biopotentialer)
    Hi-fi audio og professionelle mixere
    Lav-niveau sensorforstærkning

Når du skal vælge den:

    Signal-til-støj-forhold er kritisk
    Du forstærker meget små signaler (< mV)
    Audio-kvalitet eller målepræcision er vigtig

6. Lavenergi / Single-Supply Op-Amp (LM324, TLV2462)
Karakteristika:

    Meget lavt strømforbrug (µA pr. kanal)
    Fungerer med enkelt forsyning (0V til Vcc)
    Input kan ofte gå til negativ rail (GND)
    Ofte rail-to-rail output ved lav strøm

Typiske anvendelser:

    Batteridrevne sensorer og IoT-nodes
    Always-on overvågning (røgdetektorer)
    Portable medicinske enheder
    Energy harvesting systemer

Når du skal vælge den:

    Batterilevetid er kritisk (måneder/år)
    Systemet kører fra enkelt battericelle
    Båndbredde-krav er moderate (< 100 kHz)

7. Audio / Hi-Fi Operationsforstærker (OPA2134, NE5534)
Karakteristika:

    Lav THD+N (< 0.001%) i audible-området
    God fase-linearitet og transient-respons
    Høj output-strøm til lav-impedans belastning
    Optimeret for 20 Hz - 20 kHz frekvensrespons

Typiske anvendelser:

    Forforstærkere og tonekontroller
    Aktive højttalere og subwoofere
    Professionel audio (mixere, interfaces)
    Guitar-effekter og instrumentforstærkere

Når du skal vælge den:

    Lydkvalitet er primær designparameter
    Du skal drive hovedtelefoner eller linje-out
    Lav forvrængning ved højt output-niveau

8. Højspændings Operationsforstærker (OPA454, PA85)
Karakteristika:

    Tåler forsyningsspændinger op til ±50V eller mere
    Kan levere høj output-spænding (tens of volts)
    Ofte beskyttet mod kortslutning og overtemp
    Større fysisk pakning for varmeafledning

Typiske anvendelser:

    Piezo-aktuatorer og ultralyd-drivere
    Industrielle styringer og motor-drivers
    HV sensor-interface og testudstyr
    Elektrostatiske applikationer

Når du skal vælge den:

    Output skal swinge > ±15V
    Du driver piezo, relay eller HV-aktuator
    Systemet kræver industriel spændingsrange

9. CMOS-Input Operationsforstærker (LMC6482, TLC2272)
Karakteristika:

    Ultrahøj input-impedans (Teraohm)
    Lav input bias-strøm (femto- til picoampere)
    Rail-to-rail input og output muligt
    Lavt strømforbrug med moderne CMOS-proces

Typiske anvendelser:

    pH-elektroder og kemiske sensorer
    Elektrometer og ladningsforstærkere
    Fotodiode-transimpedans forstærkere
    Kapacitive sensorer og touch-interface

Når du skal vælge den:

    Input-strøm skal minimeres (fA-området)
    Kilde-impedans er meget høj (> 100 MΩ)
    Lav spændingsdrift med rail-to-rail behov

10. Current-Feedback / CMOD Op-Amp (AD844, LM6181)
Karakteristika:

    Slew rate uafhængig af lukket sløjfe-gain
    Høj båndbredde selv ved højt gain
    Lavere input-impedans på inverterende indgang
    Kræver specifik feedback-modstand for stabilitet

Typiske anvendelser:

    Video distribution og buffering
    Pulsgeneratorer og hurtig switching
    RF-mellemtrin og kommunikation
    Professionel audio med høj hastighed

Når du skal vælge den:

    Du skal have konstant båndbredde ved variabelt gain
    Slew rate > 500 V/µs er nødvendigt
    Applikationen kræver høj hastighed ved højt gain

10. Rail-to-Rail Op-Amps (MCP6002, LMV321)
MCP6001, MCP6002, MCP6004, MCP6021, MCP6022, MCP6024, MCP6L01, MCP6L02, 
LMV321, LMV358, LMV324, LMV7219, LMV611, LMV641, LMV772, LMV841, LMV842, 
TLV2371, TLV2372, TLV2462, TLV2472, TLV272, TLV9001, TLV9002, TLV9062, 
AD8605, AD8606, AD8608, AD8628, AD8638, AD8639, ADA4661, ADA4691, 
OPA2333, OPA2350, OPA333, OPA335, OPA340, OPA344, OPA365, OPA376, 
MAX44246, MAX44260, MAX999, MAX4230, MAX4238, MAX4239, MAX44205, 
TS912, TSX922, TSX923, TSZ121, TSZ122, NCS2001, NCS2002, NCS210, NCS214

11. JFET-Input Op-Amps (TL072, TL084)
TL071, TL072, TL074, TL081, TL082, TL084, LF351, LF353, LF356, LF357, 
LF411, LF412, LF441, LF442, OPA132, OPA134, OPA2132, OPA2134, OPA1642, 
AD823, AD825, AD826, AD827, AD843, AD845, AD847, AD8610, AD8620, 
NJM4580, NJM4558, NJM2068, NJM4565, BA4560, BA4580, BA4565, RC4558, 
CA3140, CA3130, ICL7652, ICL7653, HA5134, HA5144, HA5221, HA5222

12. Præcisions/Low-Offset Op-Amps (OP07, OP177)
OP07, OP177, OP277, OP377, OP477, OP27, OP37, OP1177, OP184, OP284, 
ADA4522, ADA4528, ADA4052, ADA4500, ADA4505, ADA4622, ADA4625, ADA4627, 
LTC2050, LTC2057, LTC2063, LTC2054, LTC2055, LT1012, LT1013, LT1014, 
LT1028, LT1128, LT1677, LT1678, LT1793, LT1880, LT1881, LT1882, 
MAX4239, MAX44205, MAX4208, MAX4209, MAX4210, MAX4211, MAX44260, 
OPA227, OPA228, OPA277, OPA2188, OPA2189, OPA2192, OPA2196, OPA2197, 
LM108, LM112, LM108A, LM308, LM312, LM725, LM741A, LM741C, LM741E

13. Højhastigheds/High-Speed Op-Amps (AD8051, LMH6629)
AD8051, AD8052, AD8055, AD8056, AD8057, AD8058, AD8001, AD8009, AD8041, 
AD8042, AD8044, AD8045, AD8047, AD8048, AD8065, AD8066, AD8067, AD8072, 
LMH6629, LMH6702, LMH6624, LMH6642, LMH6643, LMH6644, LMH6645, LMH6646, 
THS3091, THS3095, THS4031, THS4032, THS4051, THS4052, THS4061, THS4062, 
OPA690, OPA695, OPA847, OPA848, OPA858, OPA859, OPA657, OPA659, OPA691, 
MAX435, MAX436, MAX437, MAX438, MAX439, MAX4450, MAX4451, MAX4452, 
EL5160, EL2070, EL2071, EL2072, EL2073, EL2074, EL2075, EL2076, EL2077, 
CLC400, CLC449, CLC450, CLC451, CLC452, CLC453, CLC454, CLC455, CLC456

14. Lavstøjs/Low-Noise Op-Amps (NE5532, OP27)
NE5532, NE5534, SA5532, SA5534, NJM4580, NJM4558, NJM2068, NJM4565, 
OP27, OP37, OP270, OP271, OP370, OP371, OPA211, OPA2134, OPA1611, 
OPA1612, OPA1641, OPA1642, OPA1652, OPA1656, OPA1662, OPA1678, OPA1679, 
AD797, AD743, AD745, AD795, AD829, AD8610, AD8620, ADA4895, ADA4896, 
ADA4897, ADA4898, ADA4899, LT1028, LT1128, LT1115, LT1007, LT1037, 
MAX977, MAX4140, MAX4141, MAX4142, MAX4143, MAX4144, MAX4145, MAX4146, 
LM4562, LME49720, LME49710, LME49860, LME49990, BA4560, BA4580, BA4565

15. Lavenergi/Low-Power Single-Supply (LM324, TLV2462)
LM321, LM358, LM324, LM2902, LM2904, LMV321, LMV358, LMV324, LMV7219, 
MCP6021, MCP6022, MCP6024, MCP6L01, MCP6L02, MCP6V01, MCP6V02, MCP6V03, 
TLV2371, TLV2372, TLV2462, TLV2472, TLV272, TLV9001, TLV9002, TLV9062, 
LPV321, LPV358, LPV324, LPV521, LPV811, LPV821, NCS210, NCS214, NCS270, 
MAX44260, MAX44280, MAX4230, MAX4238, MAX4239, MAX44205, MAX44246, 
OPA333, OPA335, OPA340, OPA344, OPA365, OPA376, OPA2333, OPA2350, 
TS912, TSX922, TSX923, TSZ121, TSZ122, NCS2001, NCS2002, NCS2003

16. Audio/Hi-Fi Op-Amps (OPA2134, NE5534)
NE5532, NE5534, SA5532, SA5534, NJM4580, NJM4558, NJM2068, NJM4565, 
OPA2134, OPA134, OPA1642, OPA1611, OPA1612, OPA1652, OPA1656, OPA1662, 
LM4562, LME49720, LME49710, LME49860, LME49990, LM833, LM4562, LM49720, 
AD825, AD827, AD843, AD845, AD847, AD8610, AD8620, ADA4895, ADA4896, 
MAX4140, MAX977, MAX4141, MAX4142, MAX4143, MAX4144, MAX4145, MAX4146, 
BA4560, BA4580, BA4565, BA4558, RC4558, RC4560, NJM4558, NJM4580, 
TDA2030, TDA2050, LM1875, LM3886, LM4780, LM49810, OPA541, OPA547

17. Højspændings/High-Voltage Op-Amps (OPA454, PA85)
OPA454, OPA462, OPA541, OPA547, OPA549, OPA551, OPA552, PA85, PA124, 
PA03, PA04, PA05, PA09, PA12, PA22, PA24, PA25, PA26, PA33, PA34, 
LM675, LM1875, LM3886, LM4780, LM49810, THS3491, THS4031, THS4051, 
AD8033, AD8034, AD8035, AD8036, AD8037, AD8038, AD8039, AD8041, AD8042, 
LT1210, LT1227, LT1228, LT1229, LT1230, LT1231, LT1232, LT1233, LT1234, 
MAX435, MAX436, MAX437, MAX438, MAX439, MAX4450, MAX4451, MAX4452, 
EL2070, EL2071, EL2072, EL2073, EL2074, EL2075, EL2076, EL2077, EL5160

18. CMOS-Input Op-Amps (LMC6482, TLC2272)
LMC6481, LMC6482, LMC6484, LMC660, LMC661, LMC662, LMC663, LMC664, 
TLC2272, TLC2274, TLC2652, TLC2654, TLC272, TLC274, TLC277, TLC279, 
MCP6L01, MCP6L02, MCP6L03, MCP6L04, MCP6V01, MCP6V02, MCP6V03, MCP6V04, 
AD8603, AD8605, AD8606, AD8608, AD8628, AD8638, AD8639, ADA4661, ADA4691, 
MAX4230, MAX4238, MAX4239, MAX44205, MAX44246, MAX44260, MAX44280, 
TSX922, TSX923, TSZ121, TSZ122, NCS2001, NCS2002, NCS2003, NCS2004, 
OPA333, OPA335, OPA340, OPA344, OPA365, OPA376, OPA2333, OPA2350, OPA2365

19. Current-Feedback/CMOD Op-Amps (AD844, LM6181)
AD844, AD846, AD847, AD848, AD849, AD8001, AD8009, AD8041, AD8042, 
LM6181, LM6211, LM6212, LM6213, LM6214, LM6215, LM6216, LM6217, LM6218, 
THS3001, THS3091, THS3095, THS4031, THS4051, THS4061, THS4062, THS4071, 
OPA690, OPA695, OPA847, OPA848, OPA858, OPA859, OPA657, OPA659, OPA691, 
EL2070, EL2071, EL2072, EL2073, EL2074, EL2075, EL2076, EL2077, EL5160, 
CLC400, CLC449, CLC450, CLC451, CLC452, CLC453, CLC454, CLC455, CLC456, 
MAX435, MAX436, MAX437, MAX438, MAX439, MAX4450, MAX4451, MAX4452

20. Zero-Drift/Chopper-Stabilized Op-Amps
LTC2050, LTC2057, LTC2063, LTC2054, LTC2055, LTC2066, LTC2067, LTC2068, 
ADA4522, ADA4528, ADA4052, ADA4500, ADA4505, ADA4622, ADA4625, ADA4627, 
MAX4239, MAX44205, MAX4208, MAX4209, MAX4210, MAX4211, MAX44260, 
OPA333, OPA335, OPA2188, OPA2189, OPA2192, OPA2196, OPA2197, OPA2333, 
TSZ121, TSZ122, TSZ321, TSZ322, NCS210, NCS214, NCS270, NCS271, 
MCP6V01, MCP6V02, MCP6V03, MCP6V04, MCP6V11, MCP6V12, MCP6V13, MCP6V14, 
ISL28022, ISL28023, ISL28024, ISL28025, ISL28026, ISL28027, ISL28028

21. Power Op-Amps (LM675, OPA541)
LM675, LM1875, LM3886, LM4780, LM49810, OPA541, OPA547, OPA549, OPA551, 
OPA552, PA03, PA04, PA05, PA09, PA12, PA22, PA24, PA25, PA26, PA33, 
PA34, PA85, PA124, TDA2030, TDA2050, TDA7293, TDA7294, TDA7375, TDA7377, 
THS3491, THS4031, THS4051, AD8033, AD8034, AD8035, AD8036, AD8037, 
LT1210, LT1227, LT1228, LT1229, LT1230, LT1231, LT1232, LT1233, LT1234

22. General Purpose Op-Amps (LM741, LM358)
LM741, LM741A, LM741C, LM741E, μA741, MC1741, MC1458, RC4558, RC4560, 
LM358, LM324, LM2902, LM2904, NJM4558, NJM4580, BA4558, BA4560, BA4580, 
CA3140, CA3130, ICL7652, ICL7653, HA5134, HA5144, HA5221, HA5222, 
TL062, TL064, TL072, TL074, TL082, TL084, LF353, LF356, LF412, LF442, 
MC33171, MC33172, MC33174, MC33178, MC33179, MC33272, MC33274, MC34071, 
NCS210, NCS214, NCS270, NCS271, NCS2001, NCS2002, NCS2003, NCS2004, 
TS912, TS922, TS924, TSX922, TSX923, TSZ121, TSZ122, TSZ321, TSZ322

23. Sammenligningstabel

Type                	  Primær parameter  	Strøm    	Forsyning    	Hovedapplikation

Rail-to-Rail       	  Output swing      	Lav      	1.8-5V       	Single-supply, ADC
JFET-Input         	  Input impedans    	Medium   	±5-±15V      	Filtre, buffer
Præcision          	  Offset/Drift     	Medium   	±5-±15V      	Måleinstrumenter
Højhastighed        	  Slew rate/BW      	Højt     	±5-±15V      	Video, RF, puls
Lavstøjs           	  Støjfigur         	Medium   	±5-±15V      	Audio, bio-sensor
Lavenergi           	  Strømforbrug      	Meget lav 	1.8-5V      	IoT, batteri
Audio/Hi-Fi         	  THD+N/Linearitet  	Medium   	±5-±15V      	Lydforstærkning
Højspænding         	  Vsupply max       	Højt     	±25-±100V   	Piezo, industriel
CMOS-Input          	  Bias strøm        	Lav      	1.8-16V      	pH, elektrometer
Current-Feedback          Hastighed@Gain    	Højt     	±5-±15V      	Video, kommunikation
Zero-Drift          	  Offset drift      	Lav      	1.8-5.5V    	Præcisionsmåling
Power Op-Amp        	  Output strøm      	Højt     	±10-±50V     	Motor, audio sluttrin

24. Valg-guide - Start med at spørge:

I. Hvad er forsyningsspændingen?
   < 3.3V → Rail-to-Rail, Low Voltage, CMOS, Zero-Drift
   ±5V til ±15V → Bipolar, JFET, Precision, Audio, High-Speed
   > ±15V → High-Voltage, Power Op-Amps

II.Hvor vigtigt er strømforbruget?
   Kritisk (µA/nA) → Low Power, CMOS, Zero-Drift, MCP/TLV-serier
   Mindre vigtigt → Bipolar, JFET, High-Speed for bedre performance

III.Hvilken hastighed/båndbredde kræves?
   < 100 kHz → De fleste typer OK (LM358, TL072, OP07)
   100 kHz - 10 MHz → NE5532, OPA2134, AD823, TL082
   > 10 MHz → AD8051, LMH6629, THS3091, OPA690, AD844

IV.Hvor præcis skal målingen være?
   Millivolt-niveau → LM358, TL072, LM741 OK
   Mikrovolt-niveau → OP07, OP177, ADA4522, LTC2050, MAX4239
   Nanovolt-niveau → Zero-drift chopper: ADA4528, LTC2063, OPA2188

V. Hvad er kilde-impedansen?
   Lav (< 1kΩ) → Bipolar (NE5532, OP27) for lavest spændingsstøj
   Medium (1k-100k) → De fleste typer OK, vælg efter andre parametre
   Høj (> 1MΩ) → JFET (TL072) eller CMOS (LMC6482) for lav bias-strøm

VI.Hvilken belastning skal drives?
   Høj strøm (> 50mA) → Power op-amp: LM675, OPA541, TDA2030
   Lav strøm (< 10mA) → Standard output er tilstrækkeligt
   Kapacitiv belastning → Vælg type med stabilitet ved kapacitiv load



## 9. FEJLFINDING
- **Knapper virker ikke:** Kontroller at filerne er navngivet korrekt og ligger i samme mappe.
- **Ulogiske resultater:** Tjek at stopbåndsfrekvensen er sat korrekt i forhold til passbåndet.
