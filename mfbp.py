# -*- coding: utf-8 -*-
"""
================================================================================
MULTIPLE FEEDBACK BANDPASS FILTER DESIGNER
================================================================================

PROGRAMMETS FORMÅL:
    Dette program er udviklet til at designe aktive båndpasfiltre af typen
    "Multiple Feedback" (MFB). MFB-topologien er velegnet til båndpasfiltre
    med moderat Q-værdi (typisk < 20) og god stabilitet.

HVAD PROGRAMMET UDFØRER:
    1. Beregner filterets orden baseret på brugerens specifikationer
    2. Opdeler filteret i andenordens biquad-sektioner
    3. Beregner optimale komponentværdier (modstande og kondensatorer)
    4. Tilpasser værdier til standard E-rækker (E12, E24, E48, E96)
    5. Visualiserer frekvensrespons (dB, fase, gruppeløbetid)
    6. Viser poler i s-planet
    7. Eksporterer SPICE-netliste til simulering

ANVENDELSESMULIGHEDER:
    - Kommunikationsteknik (båndselektive filtre)
    - Måleteknik (signalbehandling)
    - Lydteknisk udstyr (equalizere)
    - Undervisning i analog elektronik

BRUGSVEJLEDNING:
    1. Indtast passbåndets grænsefrekvenser (fn og fø)
    2. Indtast stopbåndets grænsefrekvenser (fsn og fsø)
    3. Vælg approksimation (Butterworth eller Chebyshev)
    4. Angiv dæmpning i passbånd/ripple samt stopbåndsdæmpning
    5. Vælg ønsket spændingsforstærkning
    6. Vælg basiskondensatorværdi og E-rækker
    7. Tryk "Beregn Filter Design"
    8. Ved behov: Eksportér SPICE-netliste

================================================================================
"""

import sys                      # Systemfunktioner (kommandolinjeargumenter)
import math                     # Matematiske funktioner (log, cos, sinh, etc.)
import numpy as np              # NumPy til numerisk array-behandling
from PySide6.QtWidgets import ( # Qt6-widgets til brugergrænsefladen
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QGridLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QGroupBox, QFileDialog, QCheckBox
)
from PySide6.QtCore import Qt   # Qt-kerner funktionalitet (konstanter, events)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure  # Matplotlib til plotting


# ==============================================================================
# KONSTANTER OG GLOBALE DATASTRUKTURER
# ==============================================================================

# E_SERIES: Dictionary der indeholder standard E-rækker for komponentværdier.
#            Hver række repræsenterer tilladte værdier pr. dekade.
#            Anvendes til at vælge praktisk realiserbare komponenter.
E_SERIES = {
    'E6': [1.0, 1.5, 2.2, 3.3, 4.7, 6.8],  # 6 værdier pr. dekade (20% tol.)
    'E12': [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2],  # 10%
    'E24': [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 
            3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1],  # 5%
    'E48': [1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, 1.62, 1.69, 
            1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, 2.61, 2.74, 2.87, 3.01, 
            3.16, 3.32, 3.48, 3.65, 3.83, 4.02, 4.22, 4.42, 4.64, 4.87, 5.11, 5.36, 
            5.62, 5.90, 6.19, 6.49, 6.81, 7.15, 7.50, 7.87, 8.25, 8.66, 9.09, 9.53],  # 2%
}

# Generer E96-rækken programmatisk baseret på formlen 10^(i/96) for i=0..95
# Dette giver 96 værdier pr. dekade (1% tolerance)
e96_list = [round(10**(i/96), 2) for i in range(96)]  # List comprehension
E_SERIES['E96'] = sorted(list(set(e96_list)))  # Fjern evt. dubletter og sortér


def find_closest_e(value, series):
    """
    FUNKTIONENS FORMÅL:
        Find den nærmeste standardkomponentværdi i en given E-række.
    
    PARAMETRE:
        value: float - Den beregnede ideelle værdi
        series: string - E-rækkens navn ('E6', 'E12', 'E24', 'E48', 'E96')
    
    RETURNERER:
        float - Den nærmeste standardværdi (med korrekt dekademultiplikator)
    
    ARBEJDSGANG:
        1. Normaliser værdien til intervallet [1, 10) ved at fratrække dekaden
        2. Find den nærmeste normaliserede værdi i E-rækken
        3. Ganges dekaden tilbage på den fundne normaliserede værdi
    """
    # Hvis E-rækken ikke findes eller værdien er 0, returnér originalværdien
    if series not in E_SERIES or value == 0:
        return value
    
    # Beregn dekademultiplikatoren (10^x) så værdien normaliseres til [1, 10)
    # math.floor: afrund nedad, math.log10: 10-talslogaritme
    magnitude = math.floor(math.log10(value))
    
    # Normaliser værdien: divider med dekademultiplikatoren
    normalized = value / (10 ** magnitude)
    
    # Start med første værdi i E-rækken som foreløbigt bedste bud
    closest = E_SERIES[series][0]
    
    # Beregn initial afstand (absolut differens)
    min_diff = abs(normalized - closest)
    
    # Iterér gennem alle værdier i E-rækken for at finde den nærmeste
    for v in E_SERIES[series]:
        diff = abs(normalized - v)  # Absolut afstand
        if diff < min_diff:         # Hvis denne er tættere på end tidligere...
            min_diff = diff         # Opdater minimumsafstanden
            closest = v             # Opdater den nærmeste værdi
    
    # Ganger dekademultiplikatoren tilbage på den fundne standardværdi
    return closest * (10 ** magnitude)


# ==============================================================================
# KLASSE: FilterPlotCanvas
# ==============================================================================

class FilterPlotCanvas(FigureCanvas):
    """
    KLASSENS FORMÅL:
        Indkapsler matplotlib-figurer til visning af filterrespons.
        Opretter et 2x2 plot-layout med:
            - Magnitude (dB) som funktion af frekvens
            - Poler i s-planet
            - Fase (grader) som funktion af frekvens
            - Gruppeløbetid (ms) som funktion af frekvens
    
    NEDARVNING:
        Arver fra FigureCanvasQTAgg, som muliggør integration af
        matplotlib-figurer i Qt-grænsefladen.
    
    ATTRIBUTTER:
        fig: Figure - Matplotlib-figuren der indeholder alle subplots
        ax_mag: Axes - Subplot til magnituderespons
        ax_pz: Axes - Subplot til pol-nuldiagram
        ax_phase: Axes - Subplot til fagerespons
        ax_gd: Axes - Subplot til gruppeløbetid
    
    METODER:
        __init__: Konstruktør, opretter figuren og alle akser
    """
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        """
        KONSTRUKTØRENS FORMÅL:
            Initialiserer plot-canvas'et med fire subplots i et 2x2 grid.
        
        PARAMETRE:
            parent: QWidget - Forældrewidget (default None)
            width: int - Bredde af figuren i tommer (default 8)
            height: int - Højde af figuren i tommer (default 6)
            dpi: int - Opløsning i dots per inch (default 100)
        
        DATA PÅVIRKET:
            Opretter og initialiserer alle attributter for klassen.
        """
        # Opret en ny Matplotlib-figur med angivet størrelse og opløsning
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        
        # Tilføj fire subplots i et 2x2 grid (rækker, kolonner, position)
        # 221 = 2 rækker, 2 kolonner, subplot nr. 1 (øverst venstre)
        self.ax_mag = self.fig.add_subplot(221)    # Magnitude-subplot
        
        # 222 = 2 rækker, 2 kolonner, subplot nr. 2 (øverst højre)
        self.ax_pz = self.fig.add_subplot(222)     # Pol-nul-subplot
        
        # 223 = 2 rækker, 2 kolonner, subplot nr. 3 (nederst venstre)
        self.ax_phase = self.fig.add_subplot(223)  # Fase-subplot
        
        # 224 = 2 rækker, 2 kolonner, subplot nr. 4 (nederst højre)
        self.ax_gd = self.fig.add_subplot(224)     # Gruppeløbetid-subplot
        
        # Kald konstruktøren af superklassen (FigureCanvasQTAgg)
        # Dette forbinder figuren med Qt-canvas'et
        super().__init__(self.fig)
        
        # Justér layoutet med 3 punkts margen mellem subplots
        self.fig.tight_layout(pad=3.0)


# ==============================================================================
# KLASSE: MFBApp (Hovedapplikation)
# ==============================================================================

class MFBApp(QMainWindow):
    """
    KLASSENS FORMÅL:
        Hovedvinduet for Multiple Feedback Bandpass Filter Designer.
        Indeholder hele brugergrænsefladen og al beregningslogik.
    
    NEDARVNING:
        Arver fra QMainWindow, som er Qt's primære vinduesklasse.
    
    ATTRIBUTTER (UI-komponenter):
        combo_approx: QComboBox - Vælg Butterworth/Chebyshev
        input_fn, input_fo: QLineEdit - Passbåndsgrænser
        input_fsn, input_fso: QLineEdit - Stopbåndsgrænser
        input_ac, input_as: QLineEdit - Dæmpningskrav
        input_gain: QLineEdit - Ønsket forstærkning
        combo_e_series_r, combo_e_series_c: QComboBox - E-rækkevalg
        table: QTableWidget - Viser komponentværdier
        canvas: FilterPlotCanvas - Plot-område
        btn_calc, btn_spice: QPushButton - Beregn og eksportér
        last_calc_data: dict - Gemmer seneste beregningsresultater
    
    METODER:
        setup_ui: Opretter hele brugergrænsefladen
        update_ui_labels: Opdaterer labels baseret på approksimationstype
        to_base: Konverterer værdi med enhed til basisenhed (F, Hz, etc.)
        format_eng: Formaterer værdi med SI-præfiks (k, M, µ, n, p)
        get_poles: Beregner poler for LP-prototyptilfælde
        calculate: Hovedberegningsfunktion
        plot_bode: Tegner Bode-diagrammer
        export_spice: Eksporterer SPICE-netliste
    """
    
    def __init__(self):
        """
        KONSTRUKTØRENS FORMÅL:
            Initialiserer hovedvinduet med titel, størrelse og grænseflade.
        
        DATA PÅVIRKET:
            Opretter hele brugergrænsefladen via setup_ui()
            Initialiserer last_calc_data til None (ingen data endnu)
        """
        super().__init__()  # Kald QMainWindow's konstruktør
        
        # Sæt vinduestitel
        self.setWindowTitle("Multiple Feedback Bandpass Filter Designer")
        
        # Sæt standardstørrelse: bredde 1240 pixels, højde 950 pixels
        self.resize(1240, 950)
        
        # Opret centralt widget (beholder for alt indhold)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Opret lodret layout som hovedlayout
        main_layout = QVBoxLayout(central_widget)
        
        # Initialiser attribut til lagring af seneste beregningsdata
        # None indikerer at der ikke er udført nogen beregning endnu
        self.last_calc_data = None
        
        # Kald metode der opbygger hele brugergrænsefladen
        self.setup_ui(main_layout)
    
    def setup_ui(self, layout):
        """
        METODENS FORMÅL:
            Opretter og arrangerer alle UI-komponenter i hovedvinduet.
        
        PARAMETRE:
            layout: QVBoxLayout - Det lodrette hovedlayout der skal udfyldes
        
        DATA PÅVIRKET:
            Opretter alle widgets og tilføjer dem til layout'et.
            Forbinder knappers clicked-signaler til deres slots.
        
        UI-STRUKTUR:
            - Øverste række: Specifikationsgruppe og komponentgruppe
            - Anden række: Beregningsknapper og status
            - Tredje række: Ordens- og stabilitetsinformation
            - Fjerde række: Tabel med komponentværdier
            - Femte række: Plot-canvas
        """
        # ========== ØVERSTE RÆKKE: Specifikationer og komponentvalg ==========
        top_layout = QHBoxLayout()  # Vandret layout til de to grupper
        
        # --- Gruppe 1: Filter-specifikationer (venstre side) ---
        specs_group = QGroupBox("Filter specifikationer (Bandpass)")
        specs_layout = QGridLayout()  # Grid-layout for struktureret opstilling
        
        # Opret dropdown til approksimationstype
        self.combo_approx = QComboBox()
        self.combo_approx.addItems(["Butterworth", "Chebyshev"])
        # Forbind ændringssignal til opdatering af labels
        self.combo_approx.currentTextChanged.connect(self.update_ui_labels)
        
        # Indtastningsfelter for passbånd (fn = nedre, fo = øvre grænse)
        self.input_fn = QLineEdit("900")   # Standard 900 Hz
        self.input_fo = QLineEdit("1100")  # Standard 1100 Hz
        
        # Enhedsvælger for frekvens (Hz, kHz, MHz)
        self.combo_p_unit = QComboBox()
        self.combo_p_unit.addItems(["Hz", "kHz", "MHz"])
        
        # Indtastningsfelter for stopbånd (fsn = nedre, fso = øvre grænse)
        self.input_fsn = QLineEdit("300")
        self.input_fso = QLineEdit("3300")
        
        # Enhedsvælger for stopbåndsfrekvenser
        self.combo_s_unit = QComboBox()
        self.combo_s_unit.addItems(["Hz", "kHz", "MHz"])
        
        # Label for passbåndsdæmpning (ændres dynamisk)
        self.label_ac = QLabel("Passband Atten (dB):")
        self.input_ac = QLineEdit("3.0")   # Standard 3 dB (Butterworth)
        
        # Indtastningsfelt for stopbåndsdæmpning
        self.input_as = QLineEdit("40")    # Standard 40 dB
        
        # Indtastningsfelt for ønsket forstærkning
        self.input_gain = QLineEdit("1.0") # Standard forstærkning 1 (0 dB)
        
        # Tilføj widgets til grid-layout (række, kolonne, rækkespænd, kolonnespænd)
        specs_layout.addWidget(QLabel("Approksimation:"), 0, 0)
        specs_layout.addWidget(self.combo_approx, 0, 1, 1, 2)  # Spænder over 2 kolonner
        
        specs_layout.addWidget(QLabel("Passband (fn - fø):"), 1, 0)
        specs_layout.addWidget(self.input_fn, 1, 1)
        specs_layout.addWidget(self.input_fo, 1, 2)
        specs_layout.addWidget(self.combo_p_unit, 1, 3)
        
        specs_layout.addWidget(QLabel("Stopband (fsn - fsø):"), 2, 0)
        specs_layout.addWidget(self.input_fsn, 2, 1)
        specs_layout.addWidget(self.input_fso, 2, 2)
        specs_layout.addWidget(self.combo_s_unit, 2, 3)
        
        specs_layout.addWidget(self.label_ac, 3, 0)
        specs_layout.addWidget(self.input_ac, 3, 1, 1, 2)
        
        specs_layout.addWidget(QLabel("Stopband Atten (dB):"), 4, 0)
        specs_layout.addWidget(self.input_as, 4, 1, 1, 2)
        
        specs_layout.addWidget(QLabel("Ønsket Gain (V/V):"), 5, 0)
        specs_layout.addWidget(self.input_gain, 5, 1, 1, 2)
        
        specs_group.setLayout(specs_layout)
        top_layout.addWidget(specs_group)  # Tilføj til øverste vandrette layout
        
        # --- Gruppe 2: Praktisk komponentvalg (højre side) ---
        comp_group = QGroupBox("Praktisk Komponent Valg")
        comp_layout = QGridLayout()
        
        # Indtastningsfelt for basiskondensatorværdi (C1 = C2)
        self.input_val = QLineEdit("10")
        
        # Enhedsvælger for kondensator (pF, nF, µF)
        self.combo_val_unit = QComboBox()
        self.combo_val_unit.addItems(["nF", "uF", "pF"])
        
        # Dropdown til modstands E-række (E12, E24, E48, E96)
        self.combo_e_series_r = QComboBox()
        self.combo_e_series_r.addItems(["E12", "E24", "E48", "E96"])
        self.combo_e_series_r.setCurrentText("E96")  # Standard 1% præcision
        
        # Dropdown til kondensator E-række (E6, E12)
        self.combo_e_series_c = QComboBox()
        self.combo_e_series_c.addItems(["E6", "E12"])
        self.combo_e_series_c.setCurrentText("E12")  # Standard 10% præcision
        
        comp_layout.addWidget(QLabel("Basis kondensator (C1=C2):"), 0, 0)
        comp_layout.addWidget(self.input_val, 0, 1)
        comp_layout.addWidget(self.combo_val_unit, 0, 2)
        comp_layout.addWidget(QLabel("C E-række:"), 1, 0)
        comp_layout.addWidget(self.combo_e_series_c, 1, 1, 1, 2)
        comp_layout.addWidget(QLabel("R E-række:"), 2, 0)
        comp_layout.addWidget(self.combo_e_series_r, 2, 1, 1, 2)
        
        comp_group.setLayout(comp_layout)
        top_layout.addWidget(comp_group)
        
        # Tilføj den øverste række til hovedlayoutet
        layout.addLayout(top_layout)
        
        # ========== ANDEN RÆKKE: Knapper ==========
        btn_layout = QHBoxLayout()  # Vandret layout til knapper
        
        # Beregningsknap
        self.btn_calc = QPushButton("Beregn Filter Design")
        self.btn_calc.clicked.connect(self.calculate)  # Forbind til calculate()
        
        # SPICE-eksportknap (deaktiveret indtil beregning er udført)
        self.btn_spice = QPushButton("Eksportér SPICE Netliste")
        self.btn_spice.setEnabled(False)  # Start deaktiveret
        self.btn_spice.clicked.connect(self.export_spice)  # Forbind til export_spice()
        
        # Checkboks for brug af E-række i SPICE-eksport
        self.check_spice_std = QCheckBox("Brug E-række i SPICE")
        self.check_spice_std.setChecked(True)  # Standard: brug standardværdier
        
        btn_layout.addWidget(self.btn_calc)
        btn_layout.addWidget(self.btn_spice)
        btn_layout.addWidget(self.check_spice_std)
        layout.addLayout(btn_layout)
        
        # ========== TREDJE RÆKKE: Statuslinje ==========
        status_layout = QHBoxLayout()
        
        # Label til visning af filterorden
        self.label_order = QLabel("Filter Orden: -")
        self.label_order.setStyleSheet("font-weight: bold; color: #2c6c91;")
        
        # Label til visning af stabilitetsvurdering
        self.label_stability = QLabel("Stabilitet: -")
        self.label_stability.setStyleSheet("font-weight: bold;")
        
        status_layout.addWidget(self.label_order)
        status_layout.addWidget(self.label_stability)
        layout.addLayout(status_layout)
        
        # ========== FJERDE RÆKKE: Komponenttabel ==========
        # Opret tabel med 0 rækker og 4 kolonner
        self.table = QTableWidget(0, 4)
        
        # Sæt overskrifter for de 4 kolonner
        self.table.setHorizontalHeaderLabels(
            ["Komponent", "Ideel Værdi", "E-række Valg", "Sektion Info"]
        )
        
        # Stræk kolonnerne så de fylder tabellens bredde
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Begræns tabelhøjden til 200 pixels
        self.table.setMaximumHeight(200)
        layout.addWidget(self.table)
        
        # ========== FEMTE RÆKKE: Plot-canvas ==========
        # Opret canvas til grafisk visning
        self.canvas = FilterPlotCanvas(self)
        layout.addWidget(self.canvas)
    
    def update_ui_labels(self, text):
        """
        METODENS FORMÅL:
            Opdaterer UI-labels baseret på valgt approksimationstype.
        
        PARAMETRE:
            text: string - Den aktuelt valgte approksimation ("Butterworth" eller
                  "Chebyshev")
        
        DATA PÅVIRKET:
            Ændrer label_acs tekst og sætter en standardværdi i input_ac.
        
        LOGIK:
            Butterworth: Passbåndsdæmpning er 3 dB ved grænsefrekvensen
            Chebyshev: Passbåndsripple angives (typisk 0.1 dB til 3 dB)
        """
        if text == "Butterworth":
            # Butterworth: Flest muligt fladt passbånd, -3 dB ved fc
            self.label_ac.setText("Passband Atten (dB):")
            self.input_ac.setText("3.0")  # Standard 3 dB dæmpning
        else:  # text == "Chebyshev"
            # Chebyshev: Stejlere overgang, men ripple i passbåndet
            self.label_ac.setText("Chebyshev Ripple (dB):")
            self.input_ac.setText("1.0")  # Standard 1 dB ripple
    
    def to_base(self, val, unit):
        """
        METODENS FORMÅL:
            Konverterer en værdi med SI-præfiks til basisenheden.
        
        PARAMETRE:
            val: float - Den numeriske værdi (f.eks. 10)
            unit: string - Enheden (Hz, kHz, MHz, pF, nF, uF)
        
        RETURNERER:
            float - Værdien i basisenhed (Hz for frekvens, Farad for kapacitans)
        
        EKSEMPEL:
            to_base(10, "kHz") -> 10000.0 (10 * 1000 = 10000 Hz)
            to_base(4.7, "nF") -> 4.7e-9 (4.7 * 10^-9 = 0.0000000047 F)
        """
        # Dictionary der kortlægger enhedsstreng til multiplikationsfaktor
        mult = {
            "Hz": 1,        # Hertz - basis for frekvens
            "kHz": 1e3,     # Kilohertz (10^3)
            "MHz": 1e6,     # Megahertz (10^6)
            "pF": 1e-12,    # Picofarad (10^-12)
            "nF": 1e-9,     # Nanofarad (10^-9)
            "uF": 1e-6      # Mikrofarad (10^-6)
        }
        
        # Hent multiplikator fra dictionary, brug 1 som standard (sikkerhed)
        # Returnér val * multiplikator (konvertering til basisenhed)
        return val * mult.get(unit, 1)
    
    def format_eng(self, val, c_type):
        """
        METODENS FORMÅL:
            Formaterer en værdi med passende SI-præfiks for menneskelig læsning.
        
        PARAMETRE:
            val: float - Værdien i basisenhed (ohm eller farad)
            c_type: string - 'R' for modstand, 'C' for kondensator
        
        RETURNERER:
            string - Formatteret værdi med enhed (f.eks. "4.70 kΩ" eller "10.0 nF")
        
        LOGIK:
            Modstande: < 1 kΩ -> Ω, 1 kΩ - 1 MΩ -> kΩ, >= 1 MΩ -> MΩ
            Kondensatorer: < 1 nF -> pF, 1 nF - 1 µF -> nF, >= 1 µF -> µF
        """
        # Håndter specialtilfældet med værdi 0
        if val == 0:
            return "0"
        
        if c_type == 'R':  # Formatering for modstande (ohm)
            if val >= 1e6:                         # >= 1 MΩ
                return f"{val/1e6:.2f} MΩ"        # Megaohm
            elif val >= 1e3:                       # >= 1 kΩ
                return f"{val/1e3:.2f} kΩ"        # Kiloohm
            else:                                   # < 1 kΩ
                return f"{val:.2f} Ω"              # Ohm
        else:  # c_type == 'C' - Formatering for kondensatorer (farad)
            if val >= 1e-6:                         # >= 1 µF
                return f"{val*1e6:.2f} µF"         # Mikrofarad
            elif val >= 1e-9:                       # >= 1 nF
                return f"{val*1e9:.2f} nF"         # Nanofarad
            else:                                   # < 1 nF
                return f"{val*1e12:.2f} pF"        # Picofarad
    
    def get_poles(self, order, approx, ac_db):
        """
        METODENS FORMÅL:
            Beregner polerne for et lavpasprototypefilter.
        
        PARAMETRE:
            order: int - Filterets orden (antal poler)
            approx: string - Approksimationstype ("Butterworth" eller "Chebyshev")
            ac_db: float - Dæmpning ved grænsefrekvens (Butterworth: 3 dB,
                          Chebyshev: ripple i dB)
        
        RETURNERER:
            list - Liste af dictionaries med 'w0' (kantfrekvens) og 'q' (kvalitetsfaktor)
        
        MATEMATISK BAGGRUND:
            Butterworth: Polerne ligger på en cirkel med radius 1.
                         Q = 1/(2*cos(θ)) hvor θ = (2k-1)π/(2n)
            
            Chebyshev: Polerne ligger på en ellipse.
                       Først beregnes ε = sqrt(10^(ripple/10) - 1)
                       Derefter a = asinh(1/ε)/n
                       Polernes koordinater: σ = -sinh(a)*sin(φ), ω = cosh(a)*cos(φ)
        """
        poles = []  # Tom liste til at samle polerne
        
        if approx == "Butterworth":
            # BUTTERWORTH: Polerne er jævnt fordelt på en cirkel
            for k in range(1, (order // 2) + 1):
                # Beregn vinkel: θ = (2k-1)π/(2n)
                theta = (2 * k - 1) * math.pi / (2 * order)
                
                # Q = 1/(2*cos(θ)) - kvalitetsfaktor for sektionen
                q = 1.0 / (2 * math.cos(theta))
                
                # Tilføj pol med normaliseret vinkelfrekvens 1 og beregnet Q
                poles.append({'w0': 1.0, 'q': q})
        
        else:  # approx == "Chebyshev"
            # CHEBYSHEV: Beregn epsilon ud fra ripple-kravet
            # ε = sqrt(10^(ripple/10) - 1)
            eps = math.sqrt(10**(ac_db/10) - 1)
            
            # Beregn a = asinh(1/ε)/n
            # asinh: invers hyperbolsk sinus (area sinus hyperbolicus)
            a = math.asinh(1/eps) / order
            
            # Iterér over polpar (kun andenordens sektioner)
            for k in range(1, (order // 2) + 1):
                # Vinkel: φ = (2k-1)π/(2n)
                phi = (2 * k - 1) * math.pi / (2 * order)
                
                # Reel del (dæmpning): σ = -sinh(a)*sin(φ)
                sigma = -math.sinh(a) * math.sin(phi)
                
                # Imaginær del (frekvens): ω = cosh(a)*cos(φ)
                omega = math.cosh(a) * math.cos(phi)
                
                # Normaliseret vinkelfrekvens: w0 = √(σ² + ω²)
                w0 = math.sqrt(sigma**2 + omega**2)
                
                # Kvalitetsfaktor: q = w0 / (-2σ)
                q = w0 / (-2 * sigma)
                
                # Tilføj pol med beregnede værdier
                poles.append({'w0': w0, 'q': q})
        
        return poles
    
    def calculate(self):
        """
        METODENS FORMÅL:
            Hovedberegningsfunktion for filterdesign.
            Udfører ordenberegning, sektionsopdeling, komponentberegning.
        
        DATA PÅVIRKET:
            - Udfylder tabellen med komponentværdier
            - Opdaterer statuslabels (orden, stabilitet)
            - Gemmer resultater i last_calc_data
            - Aktiverer SPICE-eksportknappen
            - Kalder plot_bode() for grafisk visning
        
        FEJLHÅNDTERING:
            Fanger undtagelser ved ugyldige input og viser fejlmeddelelse.
        """
        # ========== TRIN 1: Aflæs og valider inputparametre ==========
        try:
            # Konverter passbåndsfrekvenser til Hz
            fn = self.to_base(float(self.input_fn.text()), 
                              self.combo_p_unit.currentText())
            fo = self.to_base(float(self.input_fo.text()), 
                              self.combo_p_unit.currentText())
            
            # Konverter stopbåndsfrekvenser til Hz
            fsn = self.to_base(float(self.input_fsn.text()), 
                               self.combo_s_unit.currentText())
            fso = self.to_base(float(self.input_fso.text()), 
                               self.combo_s_unit.currentText())
            
            # Aflæs dæmpningsparametre og forstærkning
            ac = float(self.input_ac.text())       # Passbåndsdæmpning/ripple
            as_ = float(self.input_as.text())      # Stopbåndsdæmpning
            total_gain = float(self.input_gain.text())  # Ønsket V/V forstærkning
            
            # Aflæs basiskondensator og konverter til Farad
            val = self.to_base(float(self.input_val.text()), 
                               self.combo_val_unit.currentText())
            
            # Valider input (tjek for fysisk meningsfulde værdier)
            if ac <= 0:
                raise ValueError("Ac skal være > 0")
            
            # Beregn båndbredder
            bw_pass = fo - fn                     # Passbåndsbredde i Hz
            bw_stop = fso - fsn                   # Stopbåndsbredde i Hz
            
            # Tjek at båndbredderne er meningsfulde
            if bw_pass <= 0 or bw_stop <= bw_pass:
                raise ValueError("Ugyldig båndbredde")
                
        except Exception as e:
            # Vis fejlmeddelelse i en dialogboks
            QMessageBox.critical(self, "Input Fejl", 
                                 f"Kontroller venligst dine indtastninger.\nFejl: {e}")
            return  # Afbryd beregningen
        
        # ========== TRIN 2: Beregn centerfrekvens og båndbredder i rad/s ==========
        # Centerfrekvens (geometrisk middelværdi af passbåndsgrænser)
        f0_center = math.sqrt(fn * fo)
        
        # Vinkelfrekvens for center (radians per sekund)
        w0_center = 2 * math.pi * f0_center
        
        # Passbåndsbredde i rad/s
        bw_rad = 2 * math.pi * bw_pass
        
        # Forhold mellem stopbånds- og passbåndsbredde
        ratio = bw_stop / bw_pass
        
        # ========== TRIN 3: Beregn nødvendig filterorden ==========
        # Ordenformel for båndpasfilter (baseret på dæmpningskrav)
        # n = log((10^(As/10)-1)/(10^(Ac/10)-1)) / (2 * log(ratio))
        order_n = math.log10((10**(as_/10)-1)/(10**(ac/10)-1)) / (2 * math.log10(ratio))
        
        # Runde op til nærmeste heltal (orden skal være et heltal)
        order_lp = max(1, math.ceil(order_n))
        
        # Båndpasfilter kræver lige orden (2 poler pr. sektion)
        if order_lp % 2 != 0:
            order_lp += 1  # Gør ordenen lige ved at lægge 1 til
        
        # ========== TRIN 4: Beregn lavpasprototypens poler ==========
        lp_poles = self.get_poles(order_lp, self.combo_approx.currentText(), ac)
        
        # ========== TRIN 5: Transformér lavpas-poler til båndpas-poler ==========
        bp_biquads = []  # Liste til båndpas-biquad-sektioner
        
        for p in lp_poles:
            # Hent lavpas-sektionens parametre
            w0_lp = p['w0']      # Normaliseret vinkelfrekvens
            q_lp = p['q']        # Kvalitetsfaktor
            
            # Beregn polens reelle og imaginære del
            # For et andenordens system: s = -α ± jβ
            alpha = w0_lp / (2 * q_lp)      # Reel del (dæmpning)
            beta = w0_lp * math.sqrt(abs(1 - 1/(4 * q_lp**2)))  # Imag. del
            
            # Lavpas-pol som komplekst tal
            p_lp = complex(-alpha, beta)
            
            # Løs karakteristisk ligning for båndpas-transformationen:
            # s^2 - (p_lp * bw) * s + w0_center^2 = 0
            # Koefficienter: a = 1, b = -p_lp * bw_rad, c = w0_center^2
            roots = np.roots([1, -p_lp * bw_rad, w0_center**2])
            
            # For hver rod (hver båndpas-pol) beregn w0 og Q
            for r in roots:
                wk = abs(r)                 # Vinkelfrekvens for båndpas-sektionen
                qk = wk / (-2 * r.real)     # Q for båndpas-sektionen
                bp_biquads.append({'w0': wk, 'q': qk})
        
        # Sortér sektioner efter stigende Q (stabilste først)
        bp_biquads.sort(key=lambda x: x['q'])
        
        # Antal biquad-sektioner
        num_sections = len(bp_biquads)
        
        # ========== TRIN 6: Forstærkningskompensation ==========
        # Beregn det naturlige tab ved centerfrekvensen
        s_at_f0 = 1j * w0_center  # Kompleks frekvens ved centerfrekvens
        H_total_at_f0 = 1.0 + 0j   # Initialiser total overføringsfunktion
        
        for bq in bp_biquads:
            wk = bq['w0']          # Sektionens vinkelfrekvens
            qk = bq['q']           # Sektionens Q
            
            # MFB-biquads overføringsfunktion (normaliseret gain = 1 ved peak)
            # H(s) = ( (wk/qk)*s ) / ( s² + (wk/qk)*s + wk² )
            H_section = ((wk/qk)*s_at_f0) / (s_at_f0**2 + (wk/qk)*s_at_f0 + wk**2)
            H_total_at_f0 *= H_section  # Kaskadekobl sektionerne
        
        # Naturligt tab ved centerfrekvens (absolut værdi)
        natural_loss = abs(H_total_at_f0)
        
        # Beregn nødvendig forstærkning pr. sektion for at opnå total gain
        # Da sektionerne er identiske (for nu), fordeles gain jævnt
        Ak_target = (total_gain / natural_loss)**(1/num_sections)
        
        # ========== TRIN 7: Ryd tabellen og initialiser data ==========
        self.table.setRowCount(0)      # Fjern alle eksisterende rækker
        spice_data = []                # Liste til SPICE-eksportdata
        max_q = 0                      # Spor den højeste Q-værdi
        
        # Hent valgte E-rækker fra UI
        r_series = self.combo_e_series_r.currentText()
        c_series = self.combo_e_series_c.currentText()
        
        # ========== TRIN 8: Beregn komponenter for hver sektion ==========
        for i, bq in enumerate(bp_biquads, 1):  # i starter ved 1
            wk = bq['w0']    # Sektionens vinkelfrekvens (rad/s)
            qk = bq['q']     # Sektionens kvalitetsfaktor
            max_q = max(max_q, qk)  # Opdater maksimal Q
            
            # Vælg standard kondensatorværdi fra valgt E-række
            c_std = find_closest_e(val, c_series)
            
            # ===== MFB-komponentligninger =====
            # For et MFB båndpasfilter gælder:
            # R3 = 2Q / (ω0 * C)
            r3_exact = 2 * qk / (wk * c_std)
            
            # R1 = Q / (A_k * ω0 * C)   (A_k er gain for sektionen)
            r1_exact = qk / (Ak_target * wk * c_std)
            
            # Beregn nævneren for R2: 2Q² - A_k
            denom = (2 * qk**2 - Ak_target)
            
            if denom <= 0:
                # Gain er for højt til denne sektions Q - justér lokalt
                # Max gain for en MFB-sektion er begrænset af 2Q²
                local_Ak = 1.8 * qk**2  # Reducer gain en smule for sikkerhed
                r1_exact = qk / (local_Ak * wk * c_std)
                r2_exact = qk / (wk * c_std * (2 * qk**2 - local_Ak))
                info_text = f"Q={qk:.2f} (Gain begrænset)"
            else:
                # Normal tilfælde - R2 kan beregnes direkte
                # R2 = Q / (ω0 * C * (2Q² - A_k))
                r2_exact = qk / (wk * c_std * denom)
                info_text = f"Q={qk:.2f}, Ak={Ak_target:.2f}"
            
            # Liste over komponenter til denne sektion
            # Format: (navn, ideel værdi, standardværdi, type)
            comps = [
                (f"R{i}1", r1_exact, find_closest_e(r1_exact, r_series), 'R'),
                (f"R{i}2", r2_exact, find_closest_e(r2_exact, r_series), 'R'),
                (f"R{i}3", r3_exact, find_closest_e(r3_exact, r_series), 'R'),
                (f"C{i}1", c_std, c_std, 'C'),
                (f"C{i}2", c_std, c_std, 'C')
            ]
            
            # Tilføj hver komponent til tabellen
            for navn, ideel, std, typ in comps:
                row = self.table.rowCount()          # Næste ledige række
                self.table.insertRow(row)            # Indsæt ny række
                self.table.setItem(row, 0, QTableWidgetItem(navn))
                self.table.setItem(row, 1, QTableWidgetItem(self.format_eng(ideel, typ)))
                self.table.setItem(row, 2, QTableWidgetItem(self.format_eng(std, typ)))
                
                # Tilføj info-tekst ved R1 for hver sektion
                if "R1" in navn:
                    self.table.setItem(row, 3, QTableWidgetItem(info_text))
            
            # Gem data til SPICE-eksport
            spice_data.append({
                'std': {
                    'r1': find_closest_e(r1_exact, r_series),
                    'r2': find_closest_e(r2_exact, r_series),
                    'r3': find_closest_e(r3_exact, r_series),
                    'c1': c_std,
                    'c2': c_std
                },
                'exact': {
                    'r1': r1_exact,
                    'r2': r2_exact,
                    'r3': r3_exact,
                    'c1': c_std,
                    'c2': c_std
                },
                'Ak': Ak_target,
                'w0': wk,
                'q': qk
            })
        
        # ========== TRIN 9: Opdater statusinformation ==========
        # Vis filterorden (2 poler pr. sektion)
        self.label_order.setText(f"Filter Orden: {num_sections*2} ({num_sections} Sektioner)")
        
        # Vurder stabilitet baseret på maksimal Q-værdi
        if max_q < 8:
            self.label_stability.setText(f"Stabilitet: God (Max Q={max_q:.1f})")
            self.label_stability.setStyleSheet("color: green;")  # Grøn tekst
        else:
            self.label_stability.setText(
                f"Advarsel: Højt Q ({max_q:.1f}) - Brug 1% tolerancer"
            )
            self.label_stability.setStyleSheet("color: orange;")  # Orange tekst
        
        # Gem beregningsdata til senere brug (SPICE-eksport, plotting)
        self.last_calc_data = {
            'f0': f0_center,     # Centerfrekvens i Hz
            'fn': fn,            # Nedre passbåndsgrænse
            'fo': fo,            # Øvre passbåndsgrænse
            'stages': spice_data # Sektionsdata
        }
        
        # Aktivér SPICE-eksportknappen (nu er der data at eksportere)
        self.btn_spice.setEnabled(True)
        
        # Generer og vis Bode-diagrammer
        self.plot_bode()
    
    def plot_bode(self):
        """
        METODENS FORMÅL:
            Tegner Bode-diagrammer for det designede filter.
        
        DATA PÅVIRKET:
            Opdaterer canvas'ets fire subplots med:
            - Magnituderespons (dB)
            - Fagerespons (grader)
            - Gruppeløbetid (ms)
            - Poler i s-planet
        
        FORUDSÆTNING:
            last_calc_data skal indeholde gyldige beregningsdata.
        """
        # Hent beregningsdata fra gemt struktur
        d = self.last_calc_data
        
        # Opret frekvensarray (logaritmisk fordelt)
        # Fra fn/10 til fo*10, 1000 punkter
        f = np.logspace(np.log10(d['fn']/10), np.log10(d['fo']*10), 1000)
        
        # Konverter til vinkelfrekvens (rad/s)
        w = 2 * np.pi * f
        
        # Kompleks frekvensvariabel s = jω
        s = 1j * w
        
        # Initialiser overføringsfunktion H(s) = 1
        H = np.ones_like(s, dtype=complex)
        
        # Liste til poler (til pol-nul-diagram)
        poles = []
        
        # Beregn total overføringsfunktion ved kaskadekobling
        for st in d['stages']:
            wk = st['w0']        # Sektionens vinkelfrekvens
            qk = st['q']         # Sektionens Q
            Ak = st['Ak']        # Sektionens forstærkning
            
            # MFB båndpas overføringsfunktion for sektionen
            # H(s) = -Ak * (wk/qk) * s / (s² + (wk/qk)*s + wk²)
            H_section = (-Ak * (wk/qk) * s) / (s**2 + (wk/qk)*s + wk**2)
            H *= H_section  # Kaskadekobl (multiplikation)
            
            # Beregn polens koordinater til pol-nul-diagram
            # For et andenordens system: s = -α ± jβ
            alpha = -wk/(2*qk)                 # Reel del
            beta = wk * math.sqrt(abs(1 - 1/(4*qk**2)))  # Imaginær del
            poles.extend([alpha + 1j*beta, alpha - 1j*beta])
        
        # ===== Beregn responser =====
        # Magnitude i decibel (20 * log10(|H|))
        mag = 20 * np.log10(np.abs(H) + 1e-12)  # +1e-12 undgår log(0)
        
        # Fase i grader (afviklet for kontinuerlig kurve)
        phase = np.degrees(np.unwrap(np.angle(H)))
        
        # Gruppeløbetid: -dφ/dω (i millisekunder)
        # np.gradient beregner numerisk differens
        gd = -np.gradient(np.unwrap(np.angle(H)), w) * 1000
        
        # ===== Tegn magnitude-subplot (øverst venstre) =====
        self.canvas.ax_mag.clear()  # Ryd tidligere indhold
        self.canvas.ax_mag.semilogx(f, mag, color='blue')  # Blå kurve
        self.canvas.ax_mag.set_title("Magnitude (dB)")
        self.canvas.ax_mag.grid(True, which="both", ls="-", alpha=0.5)  # Gitter
        self.canvas.ax_mag.axvline(d['f0'], color='green', ls='--')  # Centerfrekvens
        
        # ===== Tegn fase-subplot (nederst venstre) =====
        self.canvas.ax_phase.clear()
        self.canvas.ax_phase.semilogx(f, phase, color='purple')  # Lilla kurve
        self.canvas.ax_phase.set_title("Fase (°) / Gruppeløbetid (ms)")
        self.canvas.ax_phase.grid(True, which="both", ls="-", alpha=0.5)
        
        # ===== Tegn gruppeløbetid-subplot (nederst højre) =====
        self.canvas.ax_gd.clear()
        self.canvas.ax_gd.semilogx(f, gd, color='red')  # Rød kurve
        self.canvas.ax_gd.set_title("Group Delay (ms)")
        self.canvas.ax_gd.grid(True, which="both", ls="-", alpha=0.5)
        
        # ===== Tegn pol-nul-diagram (øverst højre) =====
        self.canvas.ax_pz.clear()
        # Tegn koordinatsystem: vandret (realakse) og lodret (imaginærakse)
        self.canvas.ax_pz.axhline(0, color='black')   # Realakse
        self.canvas.ax_pz.axvline(0, color='black')   # Imaginærakse
        
        # Plot poler som røde krydser (x)
        self.canvas.ax_pz.scatter([p.real for p in poles], 
                                   [p.imag for p in poles], 
                                   marker='x', color='red')
        self.canvas.ax_pz.set_title("S-Plan (Poler)")
        self.canvas.ax_pz.grid(True)  # Tilføj gitter
        
        # Opdater canvas'et (gen-tegn)
        self.canvas.draw()
    
    def export_spice(self):
        """
        METODENS FORMÅL:
            Eksporterer en SPICE-netliste til fil for simulering.
        
        DATA PÅVIRKET:
            Opretter en .cir-fil med kredsløbsbeskrivelse.
        
        FILFORMAT:
            Standard SPICE netlist-format med:
            - Modstande: R<navn> <knude1> <knude2> <værdi>
            - Kondensatorer: C<navn> <knude1> <knude2> <værdi>
            - Underkredsløb for ideel operationsforstærker
        
        BRUGERGRÆNSEFLADE:
            Åbner en fil-dialog til at vælge gemmested.
        """
        # Åbn dialog til at vælge filplacering
        path, _ = QFileDialog.getSaveFileName(
            self, "Gem SPICE", "mfb_filter.cir", "Netliste (*.cir)"
        )
        
        # Hvis brugeren annullerer, afbryd
        if not path:
            return
        
        # Hent beregningsdata
        d = self.last_calc_data
        
        # Tjek om der skal bruges standardværdier eller eksakte værdier
        use_std = self.check_spice_std.isChecked()
        
        # Start netlisten med kommentar og signalkilde
        net = [
            "* MFB Bandpass Netliste",  # Kommentarlinje (starter med *)
            "Vin n0 0 AC 1"             # AC-signalkilde, 1V amplitude
        ]
        
        # Generér netlist for hver sektion
        for i, st in enumerate(d['stages'], 1):
            # Vælg standard- eller eksakte værdier
            v = st['std'] if use_std else st['exact']
            
            # Definer knuder (nodes)
            # n0 = input, n1, n2, ... nN = output for sidste sektion
            inn = f"n{i-1}"  # Indgangsknude for denne sektion
            
            # Udgangsknude: sidste sektion hedder VOUT, ellers nX
            out = f"n{i}" if i < len(d['stages']) else "VOUT"
            
            # Interne knuder: mid (mellem R1 og R2/C1) og inv (op-amp inverterende)
            mid = f"n{i}m"
            inv = f"n{i}inv"
            
            # Tilføj komponenter til netlisten
            net.extend([
                f"R{i}1 {inn} {mid} {v['r1']:.2f}",      # Indgangsmodstand
                f"R{i}2 {mid} 0 {v['r2']:.2f}",           # Modstand til jord
                f"R{i}3 {inv} {out} {v['r3']:.2f}",       # Tilbagekoblingsmodstand
                f"C{i}1 {mid} {out} {v['c1']:.4e}",       # Kondensator C1
                f"C{i}2 {mid} {inv} {v['c2']:.4e}",       # Kondensator C2
                f"XOP{i} 0 {inv} {out} IDEAL_OP"          # Op-amp instans
            ])
        
        # Tilføj model for ideel operationsforstærker
        net.extend([
            "* Ideel OP-AMP model",
            ".subckt IDEAL_OP 1 2 3",    # Knuder: 1=+, 2=-, 3=udgang
            "E1 3 0 1 2 1E6",            # Spændingsstyret spændingskilde, gain=1e6
            ".ends",                      # Afslut underkredsløb
            ".ac dec 100 10 1Meg",        # AC-analyse: 100 punkter pr. dekade, 10 Hz til 1 MHz
            ".end"                        # Afslut netlisten
        ])
        
        # Skriv netlisten til fil
        with open(path, 'w') as f:
            f.write("\n".join(net))  # Sammenføj linjer med newline


# ==============================================================================
# PROGRAMINDTANGSPUNKT (main)
# ==============================================================================

if __name__ == "__main__":
    """
    PROGRAMINDTANGSPUNKT:
        Udføres kun når scriptet køres direkte (ikke ved import).
    
    FUNKTION:
        - Opretter QApplication-instans (nødvendig for Qt)
        - Opretter hovedvinduet (MFBApp)
        - Viser vinduet
        - Starter Qt-event-loop'en (app.exec())
    """
    # Opret Qt-applikation med kommandolinjeargumenter
    app = QApplication(sys.argv)
    
    # Opret hovedvinduet
    window = MFBApp()
    
    # Gør vinduet synligt
    window.show()
    
    # Start event-loop'en og afslut med den returnerede statuskode
    sys.exit(app.exec())