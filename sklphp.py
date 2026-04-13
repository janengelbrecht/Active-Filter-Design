# =============================================================================
# INDLEDNING
# =============================================================================
# Programmet er udviklet til at designe aktive Sallen-Key-filtre af 2. orden
# (kaskadekoblede sektioner) med Butterworth- eller Chebyshev-approksimation.
# Det beregner nødvendig filterorden, poler, komponentværdier (modstande og
# kondensatorer), og tilpasser dem til E-rækker (E12, E24, E48, E96 for R;
# E6, E12 for C). Programmet viser Bode-plot (magnitude, fase, gruppeløbetid)
# samt pol-nuldiagram. Det kan eksportere SPICE-netlister (.cir-filer).
#
# BRUGSVEJLEDNING:
# 1. Vælg filtertype (Low-Pass/High-Pass) og approksimation (Butterworth/Cheb).
# 2. Indtast cutoff-frekvens (fc) og stopbåndsfrekvens (fs) med enheder.
# 3. Indtast dæmpning i pasbånd (for Butterworth: -3 dB ved fc; for Chebyshev:
#    ripple i dB) og stopbåndsdæmpning (As) i dB.
# 4. Vælg basiskondensatorværdi (startværdi for C2 i LP, C1=C2 i HP) og enhed.
# 5. Vælg E-række for kondensatorer (begrænser C-værdier) og for modstande.
# 6. Tryk "Beregn filter". Resultatet vises i tabel og grafer.
# 7. Eventuelt eksportér til SPICE.
# =============================================================================

import sys
import math
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QLabel, QComboBox,
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QGroupBox, QFileDialog, QCheckBox)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# =============================================================================
# KONSTANTER: E-rækker for modstande og kondensatorer (standardværdier)
# =============================================================================
# E6, E12, E24, E48, E96 er præcisionsrækker. Værdierne er normaliserede til
# 1-10 området. De bruges til at finde nærmeste praktiske komponentværdi.
E_SERIES = {
    'E6': [1.0, 1.5, 2.2, 3.3, 4.7, 6.8],
    'E12': [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2],
    'E24': [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
            3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1],
    'E48': [1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, 1.62, 1.69,
            1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, 2.61, 2.74, 2.87, 3.01,
            3.16, 3.32, 3.48, 3.65, 3.83, 4.02, 4.22, 4.42, 4.64, 4.87, 5.11, 5.36,
            5.62, 5.90, 6.19, 6.49, 6.81, 7.15, 7.50, 7.87, 8.25, 8.66, 9.09, 9.53],
}
# E96 genereres matematisk: 10^(i/96) for i=0..95, runder til 2 decimaler,
# fjerner dubletter og sorterer. Dette giver 96 værdier pr. dekade.
e96_list = [round(10**(i/96), 2) for i in range(96)]
E_SERIES['E96'] = sorted(list(set(e96_list)))

# =============================================================================
# FUNKTION: find_closest_e(value, series)
# Formål: Finder den nærmeste E-række-værdi inden for samme dekade som value.
# Metode: Normaliserer value til intervallet [1,10), finder nærmeste i listen,
#          og skalerer tilbage med den oprindelige dekade.
# Returnerer: Den nærmeste standardværdi (flydende decimal).
# =============================================================================
def find_closest_e(value, series):
    if series not in E_SERIES or value == 0:
        return value                     # Hvis ugyldig serie eller nul, returnér uændret
    magnitude = math.floor(math.log10(value))   # Eksponent (dekade)
    normalized = value / (10 ** magnitude)      # Normaliser til [1,10)
    closest = E_SERIES[series][0]               # Start med første værdi i rækken
    min_diff = abs(normalized - closest)        # Beregn differencen
    for v in E_SERIES[series]:                  # Gennemløb alle rækkeværdier
        diff = abs(normalized - v)
        if diff < min_diff:
            min_diff = diff
            closest = v
    return closest * (10 ** magnitude)          # Tilbageskalering

# =============================================================================
# FUNKTION: find_higher_e(value, series)
# Formål: Finder den mindste E-række-værdi, der er >= value (inden for dekade).
# Anvendes til at vælge C1 i LP-filtre, hvor C1 skal være >= 4*Q^2*C2.
# =============================================================================
def find_higher_e(value, series):
    if series not in E_SERIES or value == 0:
        return value
    magnitude = math.floor(math.log10(value))
    normalized = value / (10 ** magnitude)
    for v in E_SERIES[series]:
        if v >= normalized - 1e-9:              # Tillad lille numerisk tolerance
            return v * (10 ** magnitude)
    # Hvis ingen i denne dekade, gå til næste dekade (første værdi *10)
    return E_SERIES[series][0] * (10 ** (magnitude + 1))

# =============================================================================
# KLASSE: FilterPlotCanvas
# Formål: Indkapsler Matplotlib-figuren med 4 delplotter:
#         - Magnitude (dB) som funktion af frekvens
#         - Pol-nuldiagram (S-plan)
#         - Fase (grader)
#         - Gruppeløbetid (group delay) i ms
# Metoder: Ingen ud over konstruktøren. Tegningerne opdateres udefra.
# Data: .fig, .ax_mag, .ax_pz, .ax_phase, .ax_gd
# =============================================================================
class FilterPlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)          # Opret figur
        self.ax_mag = self.fig.add_subplot(221)                      # Magnitude (øverst venstre)
        self.ax_pz = self.fig.add_subplot(222)                       # Pol-nul (øverst højre)
        self.ax_phase = self.fig.add_subplot(223)                    # Fase (nederst venstre)
        self.ax_gd = self.fig.add_subplot(224)                       # Group delay (nederst højre)
        super().__init__(self.fig)                                   # Initialiser canvas
        self.fig.tight_layout(pad=3.0)                               # Justér layout med marginer

# =============================================================================
# HOVEDKLASSE: SallenKeyApp (QMainWindow)
# Formål: Styrer hele brugergrænsefladen, beregninger, tegninger og eksport.
# Metoder: setup_ui, update_ui_labels, to_base, format_eng, get_poles,
#          calculate, plot_bode, export_spice.
# Data: Gemmer sidste beregningsdata i self.last_calc_data til SPICE-eksport.
# =============================================================================
class SallenKeyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sallen-Key Filter design")              # Vinduestitel
        self.resize(1200, 950)                                       # Standardstørrelse
        central_widget = QWidget()                                   # Centralt widget
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)                    # Lodret hovedlayout
        self.last_calc_data = None                                   # Gemmer data til SPICE
        self.setup_ui(main_layout)                                   # Byg brugerfladen

    # -------------------------------------------------------------------------
    # setup_ui: Opretter alle grafiske elementer: indtastningsgrupper,
    #           knapper, tabel, canvas.
    # -------------------------------------------------------------------------
    def setup_ui(self, layout):
        top_layout = QHBoxLayout()                                   # Vandret øverste del

        # Gruppe: Filterspecifikationer
        specs_group = QGroupBox("Filter specifikationer")
        specs_layout = QGridLayout()
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Low-Pass (LP)", "High-Pass (HP)"]) # LP eller HP
        self.combo_approx = QComboBox()
        self.combo_approx.addItems(["Butterworth", "Chebyshev"])      # Approksimationstype
        self.combo_approx.currentTextChanged.connect(self.update_ui_labels) # Dynamisk labelændring

        self.input_fc = QLineEdit("1000")                            # Cutoff-frekvens
        self.combo_fc_unit = QComboBox()
        self.combo_fc_unit.addItems(["Hz", "kHz", "MHz"])             # Enhed for fc
        self.input_fs = QLineEdit("4000")                            # Stopbåndsfrekvens
        self.combo_fs_unit = QComboBox()
        self.combo_fs_unit.addItems(["Hz", "kHz", "MHz"])             # Enhed for fs

        self.label_ac = QLabel("Passband Atten (dB):")               # Label ændres dynamisk
        self.input_ac = QLineEdit("3")                               # Pasbåndsdæmpning/ripple
        self.input_as = QLineEdit("40")                              # Stopbåndsdæmpning (dB)

        # Placer alle specifikationsfelter i grid
        specs_layout.addWidget(QLabel("Type:"), 0, 0)
        specs_layout.addWidget(self.combo_type, 0, 1)
        specs_layout.addWidget(QLabel("Approksimation:"), 1, 0)
        specs_layout.addWidget(self.combo_approx, 1, 1)
        specs_layout.addWidget(QLabel("Cutoff (fc):"), 2, 0)
        specs_layout.addWidget(self.input_fc, 2, 1)
        specs_layout.addWidget(self.combo_fc_unit, 2, 2)
        specs_layout.addWidget(QLabel("Stopband (fs):"), 3, 0)
        specs_layout.addWidget(self.input_fs, 3, 1)
        specs_layout.addWidget(self.combo_fs_unit, 3, 2)
        specs_layout.addWidget(self.label_ac, 4, 0)
        specs_layout.addWidget(self.input_ac, 4, 1)
        specs_layout.addWidget(QLabel("Stopband Atten (dB):"), 5, 0)
        specs_layout.addWidget(self.input_as, 5, 1)
        specs_group.setLayout(specs_layout)
        top_layout.addWidget(specs_group)

        # Gruppe: Praktisk komponentvalg (E-rækker og basiskondensator)
        comp_group = QGroupBox("Praktisk Komponent Valg")
        comp_layout = QGridLayout()
        self.input_val = QLineEdit("10")                             # Basis C-værdi
        self.combo_val_unit = QComboBox()
        self.combo_val_unit.addItems(["nF", "uF", "pF"])             # Enhed for basis C
        self.combo_e_series_r = QComboBox()
        self.combo_e_series_r.addItems(["E12", "E24", "E48", "E96"]) # R-række
        self.combo_e_series_r.setCurrentText("E96")                  # Standard høj præcision
        self.combo_e_series_c = QComboBox()
        self.combo_e_series_c.addItems(["E6", "E12"])                # C-række (typisk E12)
        self.combo_e_series_c.setCurrentText("E12")

        comp_layout.addWidget(QLabel("Basis kondensator:"), 0, 0)
        comp_layout.addWidget(self.input_val, 0, 1)
        comp_layout.addWidget(self.combo_val_unit, 0, 2)
        comp_layout.addWidget(QLabel("C E-række grænse:"), 1, 0)
        comp_layout.addWidget(self.combo_e_series_c, 1, 1)
        comp_layout.addWidget(QLabel("R E-række grænse:"), 2, 0)
        comp_layout.addWidget(self.combo_e_series_r, 2, 1)
        comp_layout.addWidget(QLabel("(Kondensatorer tvinges til valgt E-række)"), 3, 0, 1, 3)
        comp_group.setLayout(comp_layout)
        top_layout.addWidget(comp_group)

        layout.addLayout(top_layout)                                 # Top-sektionen klar

        # Knapperække: Beregn, Eksportér SPICE, checkbox for E-række i SPICE
        btn_layout = QHBoxLayout()
        self.btn_calc = QPushButton("Beregn filter")
        self.btn_calc.clicked.connect(self.calculate)                # Kør beregning
        self.btn_spice = QPushButton("Eksportér SPICE (.cir)")
        self.btn_spice.setEnabled(False)                             # Først aktiveres efter beregning
        self.btn_spice.clicked.connect(self.export_spice)
        self.check_spice_std = QCheckBox("Brug E-række i SPICE")
        self.check_spice_std.setChecked(True)                        # Standard: brug E-rækkeværdier

        btn_layout.addWidget(self.btn_calc)
        btn_layout.addWidget(self.btn_spice)
        btn_layout.addWidget(self.check_spice_std)
        layout.addLayout(btn_layout)

        # Statuslinje med filterorden og stabilitetsadvarsel
        status_layout = QHBoxLayout()
        self.label_order = QLabel("Filter Orden: -")
        self.label_order.setStyleSheet("font-weight: bold; color: #2c6c91;")
        self.label_stability = QLabel("Stabilitet: Venter...")
        self.label_stability.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.label_order)
        status_layout.addWidget(self.label_stability)
        layout.addLayout(status_layout)

        # Tabel til visning af komponenter (R1,R2,C1,C2) for hver sektion
        self.table = QTableWidget(0, 4)                              # 0 rækker, 4 kolonner
        self.table.setHorizontalHeaderLabels(["Komponent", "Ideel / Krævet", "E-række Valg", "Q-faktor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMaximumHeight(150)
        layout.addWidget(self.table)

        # Canvas til grafer
        self.canvas = FilterPlotCanvas(self)
        layout.addWidget(self.canvas)

    # -------------------------------------------------------------------------
    # update_ui_labels: Dynamisk ændring af label og standardværdi for
    #                   pasbåndsdæmpning afhængig af Butterworth/Chebyshev.
    # -------------------------------------------------------------------------
    def update_ui_labels(self, text):
        if text == "Butterworth":
            self.label_ac.setText("Passband Atten (dB):")
            self.input_ac.setText("3")                               # -3 dB ved fc
        elif text == "Chebyshev":
            self.label_ac.setText("Chebyshev Ripple (dB):")
            self.input_ac.setText("1.0")                             # 1 dB ripple i pasbånd

    # -------------------------------------------------------------------------
    # to_base: Omregner indtastet værdi med enhed til basisenhed (Hz eller Farad).
    # -------------------------------------------------------------------------
    def to_base(self, val, unit):
        mult = {"Hz":1, "kHz":1e3, "MHz":1e6, "pF":1e-12, "nF":1e-9, "uF":1e-6}
        return val * mult.get(unit, 1)

    # -------------------------------------------------------------------------
    # format_eng: Konverterer en værdi til pæn ingeniørformateret streng
    #             med passende præfiks (kΩ, MΩ, nF, µF, pF).
    # -------------------------------------------------------------------------
    def format_eng(self, val, c_type):
        if val == 0:
            return "0"
        if c_type == 'R':                                            # Modstand
            if val >= 1e6:
                return f"{val/1e6:.2f} MΩ"
            elif val >= 1e3:
                return f"{val/1e3:.2f} kΩ"
            else:
                return f"{val:.2f} Ω"
        else:                                                        # Kondensator
            if val >= 1e-6:
                return f"{val*1e6:.2f} µF"
            elif val >= 1e-9:
                return f"{val*1e9:.2f} nF"
            else:
                return f"{val*1e12:.2f} pF"

    # -------------------------------------------------------------------------
    # get_poles: Beregner normaliserede poler (w0, Q) for Butterworth eller
    #            Chebyshev af given orden. For Chebyshev bruges ripple (ac_db)
    #            til at beregne epsilon.
    # Returnerer: Liste af dict med 'w0' og 'q'.
    # -------------------------------------------------------------------------
    def get_poles(self, order, approx, ac_db):
        poles = []
        if approx == "Butterworth":
            for k in range(1, (order // 2) + 1):
                # Butterworth-poler ligger på enhedscirklen i S-planet
                q = 1.0 / (2 * math.cos((2 * k - 1) * math.pi / (2 * order)))
                poles.append({'w0': 1.0, 'q': q})
        else:  # Chebyshev
            eps = math.sqrt(10**(ac_db/10) - 1)                      # Ripple-faktor
            a = math.asinh(1/eps) / order                            # Bestemmer polernes afstand fra imaginærakse
            for k in range(1, (order // 2) + 1):
                phi = (2 * k - 1) * math.pi / (2 * order)
                sigma = -math.sinh(a) * math.sin(phi)                # Real-del (negativ)
                omega = math.cosh(a) * math.cos(phi)                 # Imaginær-del
                w0 = math.sqrt(sigma**2 + omega**2)                  # Normaliseret vinkelfrekvens
                q = w0 / (-2 * sigma)                                # Kvalitetsfaktor (positiv)
                poles.append({'w0': w0, 'q': q})
        return poles

    # -------------------------------------------------------------------------
    # calculate: Hovedberegningsfunktion. Bestemmer orden, poler, komponenter,
    #            opdaterer tabel, stabilitetslabel og grafer.
    # -------------------------------------------------------------------------
    def calculate(self):
        try:
            fc = self.to_base(float(self.input_fc.text()), self.combo_fc_unit.currentText())
            fs = self.to_base(float(self.input_fs.text()), self.combo_fs_unit.currentText())
            ac = float(self.input_ac.text())
            as_ = float(self.input_as.text())
            val = self.to_base(float(self.input_val.text()), self.combo_val_unit.currentText())
        except:
            return                                                   # Hvis ugyldig indtastning, afbryd

        # Bestem frekvensforholdet afhængig af LP eller HP
        ratio = fs/fc if "LP" in self.combo_type.currentText() else fc/fs
        # Beregn nødvendig orden ud fra dæmpningskrav
        order_n = math.log10((10**(as_/10)-1)/(10**(ac/10)-1)) / (2 * math.log10(ratio))
        order = max(2, math.ceil(order_n))
        if order % 2 != 0:
            order += 1                                               # Sørg for lige orden (2. ordens sektioner)

        self.label_order.setText(f"Filter Orden: {order} ({order // 2} Sektioner)")

        poles = self.get_poles(order, self.combo_approx.currentText(), ac)
        self.table.setRowCount(0)                                    # Ryd tabellen
        spice_data = []

        r_series = self.combo_e_series_r.currentText()
        c_series = self.combo_e_series_c.currentText()
        max_q = 0

        # Gennemløb hvert 2. ordens polpar (en sektion pr. pol i listen)
        for i, p in enumerate(poles, 1):
            if "LP" in self.combo_type.currentText():
                w0_actual = 2 * math.pi * fc * p['w0']               # LP: w0 skaleres med fc
            else:
                w0_actual = (2 * math.pi * fc) / p['w0']             # HP: w0 = fc / w0_norm
            q = p['q']
            max_q = max(max_q, q)

            if "LP" in self.combo_type.currentText():
                # LP Sallen-Key: Vælg C2 som nærmeste E-værdi, beregn C1_min = 4*Q^2*C2
                c2_std = find_closest_e(val, c_series)
                c2_exact = c2_std
                c1_min = c2_std * 4 * (q**2)
                c1_std = find_higher_e(c1_min, c_series)             # C1 >= C1_min
                c1_exact = c1_min

                radicand = 1 - (4 * (q**2) * c2_std / c1_std)
                if radicand < 0:
                    radicand = 0
                factor = 1 / (2 * w0_actual * q * c2_std)
                r1_exact = factor * (1 - math.sqrt(radicand))
                r2_exact = factor * (1 + math.sqrt(radicand))
            else:
                # HP Sallen-Key: C1 = C2 = valgt E-værdi
                c1_std = c2_std = find_closest_e(val, c_series)
                c1_exact = c2_exact = c1_std
                r1_exact = 1 / (2 * w0_actual * q * c1_std)
                r2_exact = (2 * q) / (w0_actual * c1_std)

            # Find nærmeste E-rækkeværdier for modstandene
            r1_std = find_closest_e(r1_exact, r_series)
            r2_std = find_closest_e(r2_exact, r_series)

            # Udfyld tabellens rækker for R1, R2, C1, C2
            for n, exact, std in [("R"+str(i)+"1", r1_exact, r1_std),
                                  ("R"+str(i)+"2", r2_exact, r2_std),
                                  ("C"+str(i)+"1", c1_exact, c1_std),
                                  ("C"+str(i)+"2", c2_exact, c2_std)]:
                c_type = 'R' if 'R' in n else 'C'
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(n))
                exact_text = self.format_eng(exact, c_type)
                if n == f"C{i}1" and "LP" in self.combo_type.currentText():
                    exact_text = "Min: " + exact_text               # Marker minimumsværdi for C1 i LP
                self.table.setItem(row, 1, QTableWidgetItem(exact_text))
                std_item = QTableWidgetItem(self.format_eng(std, c_type))
                if c_type == 'C':
                    std_item.setForeground(Qt.darkGreen)            # Kondensatorer i grøn
                self.table.setItem(row, 2, std_item)
                self.table.setItem(row, 3, QTableWidgetItem(f"Q={q:.3f}"))

            spice_data.append({'exact': {'r1': r1_exact, 'r2': r2_exact,
                                         'c1': c1_std, 'c2': c2_std},
                               'std':   {'r1': r1_std, 'r2': r2_std,
                                         'c1': c1_std, 'c2': c2_std}})

        # Stabilitetsvurdering baseret på maksimal Q-værdi
        if max_q < 3.0:
            self.label_stability.setText(f"Stabilitet: God (Max Q = {max_q:.2f})")
            self.label_stability.setStyleSheet("font-weight: bold; color: #28a745;")
        else:
            self.label_stability.setText(f"Advarsel: Kritisk Q-faktor (Max Q = {max_q:.2f}) - Risiko for ringing!")
            self.label_stability.setStyleSheet("font-weight: bold; color: #ff8c00;")

        self.last_calc_data = {'fc': fc,
                               'type': "LP" if "LP" in self.combo_type.currentText() else "HP",
                               'stages': spice_data}
        self.btn_spice.setEnabled(True)                              # Aktivér SPICE-knap
        self.plot_bode(fc, poles, self.last_calc_data['type'])

    # -------------------------------------------------------------------------
    # plot_bode: Tegner Bode-diagrammer (magnitude, fase, gruppeløbetid) og
    #            pol-nuldiagram baseret på polerne og filtertype.
    # -------------------------------------------------------------------------
    def plot_bode(self, fc, poles, f_type):
        f = np.logspace(np.log10(fc/10), np.log10(fc*10), 1000)      # Frekvensakse logaritmisk
        w = 2 * np.pi * f
        s = 1j * w
        wc = 2 * np.pi * fc

        H = np.ones_like(s, dtype=complex)
        s_poles_norm = []                                            # Gem poler i S-plan (normaliseret)

        for p in poles:
            w0 = p['w0']
            q = p['q']
            alpha = -w0 / (2*q)                                      # Real-del af normaliseret pol
            beta = w0 * math.sqrt(abs(1 - 1/(4*q**2)))               # Imaginær-del
            s_poles_norm.append(alpha + 1j*beta)
            s_poles_norm.append(alpha - 1j*beta)

            w0_actual = wc * w0 if f_type == "LP" else wc / w0       # Skaleret polfrekvens
            if f_type == "LP":
                # LP overføringsfunktion: w0^2 / (s^2 + (w0/q)s + w0^2)
                H *= (w0_actual**2) / (s**2 + (w0_actual/q)*s + w0_actual**2)
            else:
                # HP overføringsfunktion: s^2 / (s^2 + (w0/q)s + w0^2)
                H *= (s**2) / (s**2 + (w0_actual/q)*s + w0_actual**2)

        mag_db = 20 * np.log10(np.maximum(np.abs(H), 1e-12))          # Magnitude i dB, undgå log(0)
        phase_rad = np.unwrap(np.angle(H))                           # Fase uden spring
        phase_deg = np.degrees(phase_rad)
        gd = -np.gradient(phase_rad, w) * 1000                        # Gruppeløbetid i ms

        # Magnitude-plot
        self.canvas.ax_mag.clear()
        self.canvas.ax_mag.semilogx(f, mag_db, color='#2c6c91', lw=2)
        self.canvas.ax_mag.set_title("Magnitude (dB)")
        self.canvas.ax_mag.set_ylabel("Gain [dB]")
        self.canvas.ax_mag.grid(True, which="both", ls='--')
        self.canvas.ax_mag.axvline(fc, color='r', ls='--', alpha=0.5) # Marker cutoff
        self.canvas.ax_mag.axhline(-3, color='g', ls=':', alpha=0.5)  # -3 dB reference

        # Fase-plot
        self.canvas.ax_phase.clear()
        self.canvas.ax_phase.semilogx(f, phase_deg, color='#4a9ed8', lw=2)
        self.canvas.ax_phase.set_title("Fase (grader)")
        self.canvas.ax_phase.set_xlabel("Frekvens [Hz]")
        self.canvas.ax_phase.set_ylabel("Fase [°]")
        self.canvas.ax_phase.grid(True, which="both", ls='--')
        self.canvas.ax_phase.axvline(fc, color='r', ls='--', alpha=0.5)

        # Pol-nuldiagram (kun poler, ingen nuller undtagen evt. HP nuller i origo)
        self.canvas.ax_pz.clear()
        theta = np.linspace(0, 2*np.pi, 100)
        self.canvas.ax_pz.plot(np.cos(theta), np.sin(theta), linestyle='--', color='lightgray') # Enhedscirkel
        for p in s_poles_norm:
            self.canvas.ax_pz.plot(np.real(p), np.imag(p), 'rx', markersize=10, markeredgewidth=2)
        self.canvas.ax_pz.set_title("Pol-Diagram (S-plan)")
        self.canvas.ax_pz.axhline(0, color='black', lw=1)
        self.canvas.ax_pz.axvline(0, color='black', lw=1)
        self.canvas.ax_pz.grid(True, ls='--')
        self.canvas.ax_pz.set_aspect('equal')

        # Gruppeløbetid
        self.canvas.ax_gd.clear()
        self.canvas.ax_gd.semilogx(f, gd, color='#d9534f', lw=2)
        self.canvas.ax_gd.set_title("Gruppeløbetid (Group Delay)")
        self.canvas.ax_gd.set_xlabel("Frekvens [Hz]")
        self.canvas.ax_gd.set_ylabel("Delay [ms]")
        self.canvas.ax_gd.grid(True, which="both", ls='--')
        self.canvas.ax_gd.axvline(fc, color='r', ls='--', alpha=0.5)

        self.canvas.fig.tight_layout(pad=2.0)
        self.canvas.draw()

    # -------------------------------------------------------------------------
    # export_spice: Gemmer en SPICE-netliste (.cir) med enten eksakte eller
    #               E-række-baserede komponentværdier.
    # -------------------------------------------------------------------------
    def export_spice(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Gem SPICE Netliste", "filter.cir", "SPICE (*.cir)")
        if not file_path:
            return

        d = self.last_calc_data
        use_std = self.check_spice_std.isChecked()
        header_text = "E-række R-værdier" if use_std else "Eksakte matematiske R-værdier (C er standard)"
        net = [f"* Sallen-Key {d['type']} Filter ({header_text})", "Vin n0 0 AC 1"]

        for i, s in enumerate(d['stages'], 1):
            vals = s['std'] if use_std else s['exact']
            p_node = f"n{i-1}"                                        # Indgangsnode for sektion i
            mid = f"n{i}m"                                            # Mellemnode (mellem R1/R2 eller C1/C2)
            pos = f"n{i}p"                                            # Ikke-inverterende indgang på opamp
            out = "OUT" if i == len(d['stages']) else f"n{i}"         # Udgangsnode

            if d['type'] == "LP":
                net += [f"R{i}1 {p_node} {mid} {vals['r1']:.2f}",
                        f"R{i}2 {mid} {pos} {vals['r2']:.2f}",
                        f"C{i}1 {mid} {out} {vals['c1']:.4e}",
                        f"C{i}2 {pos} 0 {vals['c2']:.4e}"]
            else:  # HP
                net += [f"C{i}1 {p_node} {mid} {vals['c1']:.4e}",
                        f"C{i}2 {mid} {pos} {vals['c2']:.4e}",
                        f"R{i}1 {mid} {out} {vals['r1']:.2f}",
                        f"R{i}2 {pos} 0 {vals['r2']:.2f}"]
            # Spændingsstyret spændingskilde (ideal opamp)
            net.append(f"E{i} {out} 0 {pos} {out} 1E6")

        net += [".ac dec 100 10 1Meg"]                                 # AC-sweep 10 Hz til 1 MHz
        net += [f".meas AC Gain_ved_fc FIND vdb(OUT) AT {d['fc']}", ".end"]

        with open(file_path, 'w') as f:
            f.write("\n".join(net))
        QMessageBox.information(self, "Færdig", f"Netliste gemt med {header_text}.")


# =============================================================================
# Hovedprogram: Starter QApplication og viser hovedvinduet.
# =============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)                                       # Opret Qt-applikation
    window = SallenKeyApp()                                            # Opret hovedvindue
    window.show()                                                      # Vis vinduet
    sys.exit(app.exec())                                               # Start event-loop