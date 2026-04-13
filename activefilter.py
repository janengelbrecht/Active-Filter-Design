# -*- coding: utf-8 -*-
"""
activefilter.py - Hovedmenu til aktiv filter design suite.

========================================
INDLEDNING – PROGRAMMETS FORMÅL OG ANVENDELSE
========================================

Dette program er en launcher (et startværktøj) til en suite af
aktive filter-designværktøjer. Det er udviklet til ingeniører og
teknikere, der arbejder med analoge aktive filtre (Sallen-Key og
Multiple Feedback topologier).

Programmet giver en grafisk menu, hvorfra brugeren kan starte
to underprogrammer:

    sklphp.py – design af Sallen-Key low-pass og high-pass filtre.

    mfbp.py – design af Multiple Feedback bandpas-filtre.

Underprogrammerne forventes at ligge i samme mappe som
activefilter.py. De udfører selv beregninger, viser grafer
(magnitude, fase, S-plan, gruppeløbetid) og eksporterer SPICE-netlister.

========================================
KORT BRUGSVEJLEDNING
========================================

1. Kør activefilter.py med Python (kræver PySide6 installeret).

2. Læs den indledende informationsboks.

3. Klik på én af de to store knapper for at starte ønsket designværktøj.

4. Det valgte program åbner i et nyt vindue (som en separat proces).

5. Hvis en fil mangler, vises en fejlmeddelelse.

========================================
MODULBESKRIVELSE
========================================

Dette modul opretter et grafisk vindue (Qt), der fungerer som launcher
for to selvstændige designværktøjer: Sallen-Key (LP/HP) og MFB (BP).
"""

import sys                     # Systemparametre og -funktioner, især kommandolinjeargumenter
import os                      # Stioperationer (finde mappe, tjekke filer)
import subprocess              # Start af eksterne processer (underprogrammer)
from PySide6.QtWidgets import (  # Qt-widgets til brugergrænsefladen
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QMessageBox
)
from PySide6.QtCore import Qt  # Qt-konstanter (f.eks. Alignment)


class MainLauncher(QMainWindow):
    """
    Hovedvindueklasse for launcher-programmet.

    ========================================
    KLASSENS FUNKTION OG ROLLE
    ========================================
    Denne klasse opretter og styrer hovedvinduet, der præsenterer
    brugeren for en grafisk menu. Klassens primære opgave er at:

    - Opsætte brugergrænsefladen med informationsboks og valgknapper.
    - Modtage brugerens valg af filterdesignværktøj.
    - Starte det valgte underprogram som en separat proces.
    - Håndtere fejl (manglende filer, afviklingsfejl).

    ========================================
    DATA SOM KLASSEN ARBEJDER MED
    ========================================
    Klassen arver fra QMainWindow og indeholder ingen vedvarende
    data ud over vinduesegenskaber (titel, størrelse, layout).
    Den videregiver ikke data til underprogrammerne – disse kører
    selvstændigt.

    ========================================
    METODER
    ========================================
    - __init__()          : Konstruktør, opsætter vinduet.
    - setup_info_section(): Bygger informationsboksen.
    - setup_selection_section(): Bygger knapperne.
    - launch_script()     : Starter et underprogram.
    """

    def __init__(self):
        """
        Konstruktør for MainLauncher-klassen.

        ========================================
        FUNKTION
        ========================================
        Initialiserer hovedvinduet, sætter titel og størrelse,
        opretter centralt widget og hovedlayout, kalder metoder
        til opbygning af informationssektion og valgsektion,
        samt tilføjer en fodnote.

        ========================================
        DATA DER PÅVIRKES
        ========================================
        Alle ændringer sker i selve vinduesobjektet (self).
        Der oprettes ingen persistente data uden for vinduet.
        """
        super().__init__()                     # Kald konstruktør fra QMainWindow (baseklassen)
        self.setWindowTitle("Active Filter design program")  # Sæt vinduets titel
        self.resize(700, 550)                  # Sæt vinduesstørrelse (bredde, højde)

        # Central widget og hovedlayout
        central_widget = QWidget()             # Opret tomt centralt widget (beholder for layout)
        self.setCentralWidget(central_widget)  # Gør det til vinduets centrale område
        main_layout = QVBoxLayout(central_widget)  # Lodret layout som centralt widgets layout
        main_layout.setSpacing(20)             # Afstand mellem elementer i layout (pixels)
        main_layout.setContentsMargins(30, 30, 30, 30)  # Margener: venstre, top, højre, bund

        # --- Informationssektion ---
        self.setup_info_section(main_layout)   # Byg informationsboksen og tilføj til layout

        # --- Vælgersektion ---
        self.setup_selection_section(main_layout)  # Byg knappernes gruppeboks og tilføj

        # --- Fodnote ---
        footer = QLabel(                         # Opret etikette (tekstelement)
            "Værktøj til professionel filterudvikling af Jan Engelbrecht Pedersen"
        )
        footer.setAlignment(Qt.AlignCenter)      # Centrér teksten vandret
        footer.setStyleSheet(                    # CSS-lignende stilark til udseende
            "color: #7f8c8d; font-style: italic; border-top: 1px solid #bdc3c7; "
            "padding-top: 10px;"
        )
        main_layout.addWidget(footer)            # Tilføj fodnoten nederst i layoutet

    def setup_info_section(self, layout):
        """
        Opretter og tilføjer informationssektionen til hovedlayoutet.

        ========================================
        FUNKTION
        ========================================
        Bygger en QGroupBox (indrammet boks) med en velkomsttitel
        og en detaljeret beskrivelse af programmets formål,
        topologier, approximationer og eksportmuligheder.

        ========================================
        PARAMETRE
        ========================================
        layout : QVBoxLayout
            Hovedlayoutet, som denne sektion skal tilføjes til.

        ========================================
        DATA DER PÅVIRKES
        ========================================
        Tilføjer et QGroupBox-objekt til det givne layout.
        Ændrer ingen data uden for layoutet.
        """
        info_group = QGroupBox("Hvad kan dette program")  # Opret gruppeboks med titel
        info_layout = QVBoxLayout()                       # Lodret layout inde i gruppeboksen

        info_title = QLabel(                              # Opret etikette til titel
            "Velkommen til aktiv filter designprogram"
        )
        info_title.setStyleSheet(                         # Stil for titel: fed og blålig
            "font-weight: bold; font-size: 16px; color: #2c3e50;"
        )

        info_text = (                                     # Flere linjers beskrivende tekst
            "Dette program er målrettet teknikere og ingeniører, der arbejder med design "
            "af aktive filtre. Værktøjet understøtter både Sallen-Key og Multiple Feedback "
            "topologier med Butterworth og Chebyshev approximationer.\n\n"
            "Programmet tilbyder:\n"
            "• Automatisk beregning af filterorden og komponentværdier.\n"
            "• Visualisering af Magnitude (Bode), Fase, S-plan og Gruppeløbetid.\n"
            "• Eksport af SPICE netlister (.cir) til simuleringsbrug.\n\n"
            "Vigtigt: Eksporten anvender ideelle OPAMP-modeller. Ved praktisk realisering "
            "skal disse udskiftes i netlisten med de specifikke SPICE-modeller for de "
            "operationsforstærkere, der anvendes i kredsløbet."
        )

        description = QLabel(info_text)                   # Opret etikette med beskrivelse
        description.setWordWrap(True)                     # Tekstombrydning ved vindueskant
        description.setStyleSheet(                        # Stil for beskrivelse
            "font-size: 13px; line-height: 150%; color: #34495e;"
        )

        info_layout.addWidget(info_title)                 # Tilføj titel til boksens layout
        info_layout.addWidget(description)                # Tilføj beskrivelse til layout
        info_group.setLayout(info_layout)                 # Sæt layoutet i gruppeboksen
        layout.addWidget(info_group)                      # Tilføj hele boksen til hovedlayout

    def setup_selection_section(self, layout):
        """
        Opretter og tilføjer valgsektionen (knapper) til hovedlayoutet.

        ========================================
        FUNKTION
        ========================================
        Bygger en QGroupBox med to store knapper:
        - Sallen-Key designer (Low-Pass / High-Pass)
        - Multiple Feedback designer (Bandpass)

        Hver knap får sin egen farve og hover-effekt.
        Når en knap klikkes, kaldes launch_script() med det tilsvarende filnavn.

        ========================================
        PARAMETRE
        ========================================
        layout : QVBoxLayout
            Hovedlayoutet, som denne sektion skal tilføjes til.

        ========================================
        DATA DER PÅVIRKES
        ========================================
        Tilføjer et QGroupBox-objekt med to QPushButton-objekter
        til det givne layout. Der oprettes forbindelse mellem
        knappers klik-signaler og launch_script-metoden.
        """
        select_group = QGroupBox("Vælg Designværktøj")    # Gruppeboks med titel
        select_layout = QHBoxLayout()                     # Vandret layout til knapperne
        select_layout.setSpacing(20)                      # Afstand mellem de to knapper

        # Knap til Sallen-Key (LP / HP)
        btn_sklphp = QPushButton(                         # Opret knap med tekst (newline tilladt)
            "Sallen-Key designer\n(Low-Pass / High-Pass)"
        )
        btn_sklphp.setMinimumHeight(100)                  # Minimumshøjde i pixels
        btn_sklphp.setStyleSheet("""                      # CSS-stil: blå baggrund, hvid tekst
            QPushButton {
                background-color: #2c6c91;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        # Forbind klik-signal til lambda-funktion, der kalder launch_script med "sklphp.py"
        btn_sklphp.clicked.connect(lambda: self.launch_script("sklphp.py"))

        # Knap til MFB (BP)
        btn_mfbp = QPushButton(                           # Opret knap til MFB bandpas
            "Multiple Feedback designer\n(Bandpass)"
        )
        btn_mfbp.setMinimumHeight(100)                    # Samme minimumshøjde som den anden knap
        btn_mfbp.setStyleSheet("""                        # CSS-stil: grøn baggrund, hvid tekst
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        # Forbind klik-signal til lambda-funktion, der kalder launch_script med "mfbp.py"
        btn_mfbp.clicked.connect(lambda: self.launch_script("mfbp.py"))

        select_layout.addWidget(btn_sklphp)               # Tilføj første knap til vandret layout
        select_layout.addWidget(btn_mfbp)                 # Tilføj anden knap til vandret layout
        select_group.setLayout(select_layout)             # Sæt det vandrette layout i gruppeboksen
        layout.addWidget(select_group)                    # Tilføj gruppeboksen til hovedlayout

    def launch_script(self, filename):
        """
        Starter et eksternt Python-script som en separat proces.

        ========================================
        FUNKTION OG ROLLE
        ========================================
        Denne metode håndterer sikker afvikling af underprogrammer:
        - Finder den absolutte sti til det script, der skal startes.
        - Kontrollerer, at filen eksisterer fysisk.
        - Starter scriptet med samme Python-tolk som hovedprogrammet.
        - Viser fejlmeddelelser i en dialogboks, hvis noget går galt.

        ========================================
        PARAMETRE
        ========================================
        filename : str
            Navnet på den Python-fil, der skal startes (f.eks. "sklphp.py").

        ========================================
        DATA DER PÅVIRKES
        ========================================
        Ingen direkte dataændringer. Metoden starter en ny proces
        og viser eventuelt en fejlmeddelelse via QMessageBox.

        ========================================
        FEJLHÅNDTERING
        ========================================
        - Hvis filen ikke findes: Vis kritisk fejlmeddelelse.
        - Hvis subprocess.Popen fejler: Fang exception og vis fejl.
        """
        # Find den præcise sti til mappen hvor dette script ligger
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Saml mappesti og filnavn til fuld sti
        full_path = os.path.join(base_path, filename)

        # Tjek om filen findes fysisk på disken
        if not os.path.exists(full_path):
            # Vis fejldialog, hvis filen mangler
            QMessageBox.critical(
                self,
                "Fil ikke fundet",
                f"Kunne ikke finde filen: {filename}\n\n"
                f"Sørg for at den ligger i mappen:\n{base_path}"
            )
            return  # Afbryd udførelsen af metoden

        try:
            # Start scriptet som en uafhængig proces.
            # sys.executable giver stien til den Python-tolk, der kører dette script.
            # cwd=base_path sikrer, at underprogrammet ser samme mappe som sin arbejdsmappe.
            subprocess.Popen([sys.executable, full_path], cwd=base_path)
        except Exception as e:
            # Hvis start fejler (f.eks. manglende rettigheder eller korrupt Python),
            # vis en fejlmeddelelse med den konkrete fejltekst.
            QMessageBox.critical(self, "Systemfejl", f"Fejl ved start af {filename}:\n{str(e)}")


# ========================================
# PROGRAMINDTANGSPUNKT (entry point)
# ========================================
if __name__ == "__main__":
    # Opret QApplication-instans – kræves af alle Qt GUI-programmer.
    # sys.argv giver kommandolinjeargumenter videre til Qt.
    app = QApplication(sys.argv)

    # Sæt overordnet stil til "Fusion" – giver et rent, moderne look på alle operativsystemer.
    app.setStyle("Fusion")

    # Opret hovedvinduet (launcheren)
    window = MainLauncher()

    # Gør vinduet synligt – som standard er Qt-widgets usynlige ved oprettelse.
    window.show()

    # Start Qt's event loop. sys.exit() sikrer, at programmets returkode
    # overføres til operativsystemet, når vinduet lukkes.
    sys.exit(app.exec())