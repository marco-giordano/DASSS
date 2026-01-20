# **Global Acoustic Standards and Parametric Definitions for Synthetic Siren Generation**


## **3\. North American Standards: The Sweep Paradigm**

The North American emergency signalling landscape is dominated by the frequency-sweeping "Wail" and "Yelp" tones. These are defined primarily by the Society of Automotive Engineers (SAE) and codified into law by state regulations such as California Title 13\.

### **3.1 SAE J1849: The Baseline Standard**

SAE J1849 "Emergency Vehicle Sirens" provides the laboratory performance requirements. It is the reference standard for most US manufacturers (Federal Signal, Whelen, Code 3).4

#### **3.1.1 Acoustical Requirements**

* **Frequency Range:** The fundamental frequency must sweep within the range of **500 Hz to 1600 Hz** (nominally). Some specific manufacturer implementations may range from 700 Hz to 1500 Hz, but the broad SAE specification covers the 500-1600 Hz band.3  
* **Sound Pressure Level (SPL):** A Class A siren must produce a minimum of **120 dB** on the acoustic axis at a distance of 3 meters.7 While DASSS generates normalized audio, this SPL requirement implies a high amplitude and saturation level in the synthesis model.

#### **3.1.2 Mode Definitions**

The SAE standard and manufacturers define specific modulation rates for the primary modes.

* **Wail:**  
  * **Description:** A slow, continuous automatic cycling of increasing and decreasing frequencies.  
  * **Cycle Rate:** **10 to 30 cycles per minute (CPM)**.7 This translates to a period of **2.0 to 6.0 seconds**.  
  * **DASSS Parameter Mapping:**  
    * frequency\_range: { "min": 500, "max": 1600 }  
    * period\_range: { "min": 2.0, "max": 6.0 }  
    * waveform: "square" (standard electronic) or "sawtooth" (mechanical simulation).  
* **Yelp:**  
  * **Description:** A rapid, continuous automatic cycling.  
  * **Cycle Rate:** **150 to 250 CPM**.7 This translates to a period of **0.24 to 0.4 seconds**.  
  * **DASSS Parameter Mapping:**  
    * frequency\_range: { "min": 500, "max": 1600 }  
    * period\_range: { "min": 0.24, "max": 0.4 }  
    * waveform: "square"

### **3.2 California Title 13: Strict Compliance**

California's Title 13, Article 8, is more prescriptive than the voluntary SAE standards. It explicitly prohibits certain sounds and strictly defines the cycle rates for Wail and Yelp.

* **Wail Constraint:** "Not less than 10 nor more than 30 oscillations per minute".7  
* **Yelp Constraint:** "Not less than 150 nor more than 250 oscillations per minute".7  
* **Prohibited Sounds:** Title 13 explicitly states that a sound cycling faster than 400 CPM is *not* a siren (often categorizing "Phaser" or "Piercer" tones as auxiliary or non-compliant for primary warning).9  
* **Hi-Lo:** Title 13 defines "Hi-Lo" as a "nonsiren sound" alternating between fixed high and low frequencies. It is not a primary warning signal in California but is permitted for specific evacuation warnings (e.g., wildfires).9

### **3.3 GSA KKK-A-1822F: The Federal Ambulance Specification**

The "Star of Life" ambulance specification (KKK-A-1822F) aligns closely with SAE J1849 but adds specific requirements for ambulance mounting and audibility.11

* **Requirement:** Ambulances must be equipped with a siren compliant with SAE J1849.13  
* **Implication for DASSS:** Generating a "KKK-A-1822F" compliant siren essentially means generating an SAE J1849 siren. However, the metadata in the JSON should reflect this dual compliance.

### **3.4 Manufacturer-Specific Profiles (US)**

To increase the diversity of the dataset, DASSS should include definitions that mimic specific hardware.

#### **3.4.1 Federal Signal**

* **Q-Siren (Electro-Mechanical):** The "Q" is the gold standard for fire apparatus. It is a mechanical siren.  
  * **Characteristics:** Slow rise, very slow coast-down.  
  * **DASSS Mapping:** Use mechanical\_asymmetry: true. mechanical\_rise\_exponent: 0.5 (fast wind up), mechanical\_fall\_exponent: 2.5 (long coast). Frequency peaks around 1200 Hz.14  
* **Rumbler:** A low-frequency intersection clearing device.  
  * **Frequency:** **182 Hz to 400 Hz**.15  
  * **Operation:** Tracks the primary siren tone but 75% lower in frequency (two octaves down).  
  * **DASSS Mapping:** Create a separate mode "Rumbler" with frequency\_range { "min": 180, "max": 400 }.

#### **3.4.2 Whelen Engineering**

* **Piercer:** A high-speed, synthetic tone used for heavy traffic.  
  * **Frequency:** **750 Hz to 1700 Hz**.16  
  * **Cycle Rate:** **800 CPM** (\~0.075s period). This is much faster than Yelp.  
  * **DASSS Mapping:** Mode "piercer", period: 0.075.

#### **3.4.3 Code 3**

* **Banshee System:** Features "dual tone" and low frequency.  
* **HyperYelp:** A faster yelp variant.  
  * **Cycle Rate:** Defined as faster than standard Yelp, often used in "Hit-N-Go" mode.17

## ---

## **4\. European Standards: The Interval Paradigm**

Unlike the continuous sweeps of the US, European signalling traditionally relies on alternating tones with precise musical intervals (Two-Tone). This distinctiveness aids in localization and differentiates emergency services from other noise sources.

## 4.1. Germany: The "Martin Horn" (DIN 14610)
The German standard is the most iconic "European" siren. It is legally defined to mimic the classic pneumatic compressed-air horns produced by the Max B. Martin company.

Structure: Two alternating tones.

Frequencies: 435 Hz (Low) and 580 Hz (High).

Interval: A precise Perfect Fourth (musical ratio 4:3).

Cycle: Typically a 4-note sequence (L-H-L-H) over 3 seconds for pneumatic, or simple alternation for electronic.

Waveform: TRAPEZOID or RECTANGLE (to simulate the brassy harmonics of air horns).

## 4.2. France: Service-Specific Intervals (NFS 32-001)
France is unique because the acoustic standard NFS 32-001 assigns specific musical intervals to different services. You cannot use a generic "French Siren"; you must simulate the specific agency.

Base Frequency: All start at 435 Hz (Tone A).

Police: 435 Hz & 580 Hz (Perfect Fourth). Faster cadence (~50-60 cycles/min).

Gendarmerie: 435 Hz & 732 Hz (Major Sixth). Very distinctive wide jump.

Fire (Sapeurs-Pompiers): 435 Hz & 488 Hz (Major Second). A dissonant, "buzzy" interval.

Ambulance (SAMU/UMH): 435 Hz & 651 Hz (Perfect Fifth).

## 4.3. Italy: The "Bitonale" (Article 177 CdS)
Italian law (Codice della Strada) mandates very specific frequency pairs depending on the urgency level.

Emergency (Emergenza): 466 Hz & 622 Hz.

Rescue (Soccorso): 392 Hz & 660 Hz.

Mechanical: Older vehicles use the "La Sonora" mechanical siren, which is a continuous high-pitched whistle (up to 2500 Hz) rather than a two-tone .

## 4.4. The Netherlands: Prio 1
Two-Tone: 375 Hz & 500 Hz (Perfect Fourth).

Slow Whoop: Used specifically for evacuation signals, sweeping 500 Hz to 1200 Hz .

## 4.5. United Kingdom: The Home Office Specification
The UK has transitioned largely to US-style sirens (Wail/Yelp) but retains a "European" flavor in its specific "Two-Tone" settings, often referred to as "Blues and Twos".

* **Traditional Two-Tone:**  
  * **Frequencies:** **466 Hz** and **622 Hz**.23  
  * **Interval:** Perfect Fourth (466 \* 1.33 ≈ 622).  
* **Modern Electronic (Wail/Yelp):**  
  * **Frequency Range:** Typically **500 Hz \- 1800 Hz**, similar to US but often with a sharper attack.  
  * **Cycle Rates:** Similar to SAE, but often labelled "Expat" or "UK Wail" in controllers.

## ---

## **5\. Asian Standards: Distinctive Patterns**

### **5.1 China: GB 8108-2014**

The Chinese National Standard GB 8108-2014 "Vehicle Electronic Sirens" governs all emergency vehicles.27

* **Test Frequencies:** The standard explicitly tests speakers at **500 Hz, 1000 Hz, and 1500 Hz**.27  
* **Tone Definitions:** While the snippet doesn't explicitly list the sweep parameters, typical implementation in China (based on the frequencies tested and "International Standard" modes in controllers exported from China) follows:  
  * **Police (Bi-tonal/Wail):** **650 Hz \- 1450 Hz** (Approximate based on similar Taiwan standards and market products).  
  * **Cycle:** **4-6 seconds** for Wail-type.

### **5.2 Japan: The "Peo-Peo" and "Woo-Woo"**

Japan utilizes very distinct siren sounds that are culturally ingrained and strictly regulated.

* **Ambulance ("Peo-Peo"):**  
  * **Frequencies:** **770 Hz** and **960 Hz**.28  
  * **Pattern:** Repeating two-tone.  
  * **Period:** **1.3 seconds** total cycle (0.65s low, 0.65s high).28  
* **Fire Truck ("Woo-Woo"):**  
  * **Characteristics:** A slow, wailing mechanical simulation.  
  * **Frequency:** **150 Hz to 850 Hz**?.29  
  * **Cycle:** **6 seconds** (4s sound, 2s silence/fading).29  
* **Police:**  
  * **Frequency:** **870 Hz ± 50 Hz**.29  
  * **Pattern:** 4s or 8s cycles.

## ---

## **6\. Oceania Standards: Harmonization and Specificity**

### **6.1 Australia**

Australia largely harmonizes with US and European standards but has specific Design Rules (ADR).

* **ADR 94/00:** Governs audible warnings.  
* **Common Tones:** Wail and Yelp are standard.  
* **Standard Emergency Warning Signal (SEWS):** While primarily a broadcast signal for disasters, it is a defined standard tone (sawtooth, 500-1200 Hz sweep).30  
* **Vehicle Specs:** Police sirens typically 110-120 dB. Frequencies 500-2000 Hz.31

### **6.2 New Zealand**

* **NZS 4512:** Fire detection standards often cite specific siren tones.  
* **Road Usage:** Generally adopts US-style Wail/Yelp/Phaser.32


#### **Bibliografia**

1. Emergency vehicle sirens \- police, ambulance and fire \- Right Driver Mock Theory Tests, accesso eseguito il giorno gennaio 20, 2026, [https://mocktheorytest.com/resources/why-are-police-sirens-different/](https://mocktheorytest.com/resources/why-are-police-sirens-different/)  
2. Cutting Through the Noise: Sirens and Emergency Vehicle Detection \- Acentech, accesso eseguito il giorno gennaio 20, 2026, [https://www.acentech.com/resources/cutting-through-the-noise-sirens-and-emergency-vehicle-detection/](https://www.acentech.com/resources/cutting-through-the-noise-sirens-and-emergency-vehicle-detection/)  
3. marco-giordano/dasss  
4. SAE J1849 Emergency Vehicle Sirens \- EUROLAB, accesso eseguito il giorno gennaio 20, 2026, [https://www.eurolab.net/en/testler/aydinlatma-ve-isaret-urunleri-testleri/sae-j1849-acil-durum-arac-sirenleri/](https://www.eurolab.net/en/testler/aydinlatma-ve-isaret-urunleri-testleri/sae-j1849-acil-durum-arac-sirenleri/)  
5. J1849\_202002 : Emergency Vehicle Sirens \- SAE International, accesso eseguito il giorno gennaio 20, 2026, [https://www.sae.org/standards/j1849\_202002-emergency-vehicle-sirens](https://www.sae.org/standards/j1849_202002-emergency-vehicle-sirens)  
6. Sound Solutions: Choosing the Right Siren for Your Public Safety Fleet \- Police, accesso eseguito il giorno gennaio 20, 2026, [https://www.government-fleet.com/10234309/sound-solutions-choosing-the-right-siren-for-your-public-safety-fleet](https://www.government-fleet.com/10234309/sound-solutions-choosing-the-right-siren-for-your-public-safety-fleet)  
7. Cal. Code Regs. Tit. 13, § 1028 \- Performance Requirements | State Regulations | US Law, accesso eseguito il giorno gennaio 20, 2026, [https://www.law.cornell.edu/regulations/california/13-CCR-1028](https://www.law.cornell.edu/regulations/california/13-CCR-1028)  
8. Siren Volume \- A Technical Discussion \- Sigma Safety, accesso eseguito il giorno gennaio 20, 2026, [https://sigmasafety.ca/news/siren-volume-technical-discussion/](https://sigmasafety.ca/news/siren-volume-technical-discussion/)  
9. Cal. Code Regs. Tit. 13, § 1021 \- Definitions | State Regulations \- Law.Cornell.Edu, accesso eseguito il giorno gennaio 20, 2026, [https://www.law.cornell.edu/regulations/california/13-CCR-1021](https://www.law.cornell.edu/regulations/california/13-CCR-1021)  
10. California Code, Vehicle Code \- VEH § 27002 \- Codes \- FindLaw, accesso eseguito il giorno gennaio 20, 2026, [https://codes.findlaw.com/ca/vehicle-code/veh-sect-27002/](https://codes.findlaw.com/ca/vehicle-code/veh-sect-27002/)  
11. SPECIFICATION DOCUMENT EXHIBIT A \- Ogden City, accesso eseguito il giorno gennaio 20, 2026, [https://www.ogdencity.gov/DocumentCenter/View/20628/Ambulance-Purchase-RFP---Exhibit-A--Specification-Document---FINAL-05-27-2022](https://www.ogdencity.gov/DocumentCenter/View/20628/Ambulance-Purchase-RFP---Exhibit-A--Specification-Document---FINAL-05-27-2022)  
12. Federal Specification for the Star-of-Life Ambulance KKK-A-1822F Dated 1 August 2007 Change Notice 9 \- Florida Department of Health, accesso eseguito il giorno gennaio 20, 2026, [https://www.floridahealth.gov/wp-content/uploads/2025/08/kkk-a-1822f-change-notice-9.pdf](https://www.floridahealth.gov/wp-content/uploads/2025/08/kkk-a-1822f-change-notice-9.pdf)  
13. KKK-A-1822F \- Change Notice 13 | PDF | Ac Power Plugs And Sockets | Electrical Wiring, accesso eseguito il giorno gennaio 20, 2026, [https://www.scribd.com/document/690179379/KKK-A-1822F-Change-Notice-13](https://www.scribd.com/document/690179379/KKK-A-1822F-Change-Notice-13)  
14. e-Q2B Electronic Siren System \- Federal Signal, accesso eseguito il giorno gennaio 20, 2026, [https://www.fedsig.com/sites/default/files/resource\_library\_document/e-Q2B%20Electronic%20Siren%20Manual%20l%20255394.pdf](https://www.fedsig.com/sites/default/files/resource_library_document/e-Q2B%20Electronic%20Siren%20Manual%20l%20255394.pdf)  
15. Rumbler siren \- Wikipedia, accesso eseguito il giorno gennaio 20, 2026, [https://en.wikipedia.org/wiki/Rumbler\_siren](https://en.wikipedia.org/wiki/Rumbler_siren)  
16. A u to m o tive: S iren s/S w itch es \- WHELEN DEUTSCHLAND Distribution, accesso eseguito il giorno gennaio 20, 2026, [https://www.bluelights-berlin.de/media/1796/file/static/doc/euro-1-siren-whelen-din-ton\_2407.pdf](https://www.bluelights-berlin.de/media/1796/file/static/doc/euro-1-siren-whelen-din-ton_2407.pdf)  
17. V-Con® Siren \- with Light Control \- Wail, Yelp, Hi-Lo, Air Horn | Shop Darley, accesso eseguito il giorno gennaio 20, 2026, [https://shop.darley.com/product/vcon-siren-with-light-control-wail-yelp-hilo-air-horn/01t2E00000QZdSVQA1](https://shop.darley.com/product/vcon-siren-with-light-control-wail-yelp-hilo-air-horn/01t2E00000QZdSVQA1)  
18. MARTIN-HORN® 2298 GM » Max B. Martin GmbH & Co. KG, accesso eseguito il giorno gennaio 20, 2026, [https://www.maxbmartin.de/en/products/martin-hornr/martin-hornr-2298-gm](https://www.maxbmartin.de/en/products/martin-hornr/martin-hornr-2298-gm)  
19. Safety in action \- Max B. Martin, accesso eseguito il giorno gennaio 20, 2026, [https://www.maxbmartin.de/fileadmin/produkte/MARTIN-Horn-2298-gm/Max-B-Martin\_22\_Produktblatt-MH\_2298GM\_EN.pdf](https://www.maxbmartin.de/fileadmin/produkte/MARTIN-Horn-2298-gm/Max-B-Martin_22_Produktblatt-MH_2298GM_EN.pdf)  
20. New siren tones optimised for increased detectability distances of emergency vehicles \- UPCommons, accesso eseguito il giorno gennaio 20, 2026, [https://upcommons.upc.edu/bitstreams/055a6b60-278d-428b-b18b-31f30306c9fc/download](https://upcommons.upc.edu/bitstreams/055a6b60-278d-428b-b18b-31f30306c9fc/download)  
21. Detection of the sirens of priority vehicles (police, ambulance, fire brigade...) \- Teensy Forum, accesso eseguito il giorno gennaio 20, 2026, [https://forum.pjrc.com/index.php?threads/detection-of-the-sirens-of-priority-vehicles-police-ambulance-fire-brigade.74291/](https://forum.pjrc.com/index.php?threads/detection-of-the-sirens-of-priority-vehicles-police-ambulance-fire-brigade.74291/)  
22. Heavy Duty Combination \- Multi-Tone Siren with Xenon Flash \- Tme.eu, accesso eseguito il giorno gennaio 20, 2026, [https://www.tme.eu/Document/9af70583725e433cef36d6cbea455c7b/WER-439-SERIES-EN.pdf](https://www.tme.eu/Document/9af70583725e433cef36d6cbea455c7b/WER-439-SERIES-EN.pdf)  
23. Le Sirene: tra mito e ambulanze \- ilSicilia.it, accesso eseguito il giorno gennaio 20, 2026, [https://ilsicilia.it/le-sirene-tra-mito-e-ambulanze/](https://ilsicilia.it/le-sirene-tra-mito-e-ambulanze/)  
24. Mains Operated Air Raid Sirens Page 1 of 2 \- RINGBELL.CO.UK, accesso eseguito il giorno gennaio 20, 2026, [https://www.ringbell.co.uk/ukwmo/Page216.htm](https://www.ringbell.co.uk/ukwmo/Page216.htm)  
25. Dutch Emergency Vehicle Siren \- Netherlands \- Fiammhorns.com, accesso eseguito il giorno gennaio 20, 2026, [https://www.fiammhorns.com/24v-priority-vehicles-fiamm/Dutch-emergency-siren-FIAMM-951028-PS10-EMER-N](https://www.fiammhorns.com/24v-priority-vehicles-fiamm/Dutch-emergency-siren-FIAMM-951028-PS10-EMER-N)  
26. SDC100W, accesso eseguito il giorno gennaio 20, 2026, [https://www.simarud.no/files/simarud/Documents/Cell2\_SDC100W\_SpecSheet.pdf](https://www.simarud.no/files/simarud/Documents/Cell2_SDC100W_SpecSheet.pdf)  
27. GB 8108-2014 PDF English, accesso eseguito il giorno gennaio 20, 2026, [https://www.chinesestandard.net/PDF.aspx/GB8108-2014](https://www.chinesestandard.net/PDF.aspx/GB8108-2014)  
28. Ambulance Siren Detector using FFT on dsPIC \- Semantic Scholar, accesso eseguito il giorno gennaio 20, 2026, [https://pdfs.semanticscholar.org/c4cc/281380e4ae4903fc7dfbd316b14716383d7f.pdf](https://pdfs.semanticscholar.org/c4cc/281380e4ae4903fc7dfbd316b14716383d7f.pdf)  
29. Detecting Approach of Emergency Vehicles Using Siren Sound Processing \- Scribd, accesso eseguito il giorno gennaio 20, 2026, [https://www.scribd.com/document/884568243/Detecting-Approach-of-Emergency-Vehicles-Using-Siren-Sound-Processing](https://www.scribd.com/document/884568243/Detecting-Approach-of-Emergency-Vehicles-Using-Siren-Sound-Processing)  
30. As 2220.1-1989 Emergency Warning and Intercommunication | PDF | Copyright \- Scribd, accesso eseguito il giorno gennaio 20, 2026, [https://www.scribd.com/document/969704718/As-2220-1-1989-Emergency-Warning-and-Intercommunication](https://www.scribd.com/document/969704718/As-2220-1-1989-Emergency-Warning-and-Intercommunication)  
31. Police Vs. Ambulance Sirens In Australia: What You Need To Know \- Nimc, accesso eseguito il giorno gennaio 20, 2026, [https://vault.nimc.gov.ng/blog/police-vs-ambulance-sirens-in-australia-what-you-need-to-know-1764798188](https://vault.nimc.gov.ng/blog/police-vs-ambulance-sirens-in-australia-what-you-need-to-know-1764798188)  
32. accesso eseguito il giorno gennaio 20, 2026, [https://www.drivingtests.co.nz/resources/emergency-vehicle-sirens-how-loud-are-they-and-what-type-of-sirens-are-there/\#:\~:text=New%20Zealand%20has%20generally%20adopted,with%20phaser%20being%20the%20fastest.](https://www.drivingtests.co.nz/resources/emergency-vehicle-sirens-how-loud-are-they-and-what-type-of-sirens-are-there/#:~:text=New%20Zealand%20has%20generally%20adopted,with%20phaser%20being%20the%20fastest.)