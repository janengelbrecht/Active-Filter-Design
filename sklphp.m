%% =========================================================
%  Sallen-Key Filter Design Tool
%  MATLAB-ækvivalent til sklphp.py
%
%  Understøtter:
%    - Low-Pass (LP) og High-Pass (HP)
%    - Butterworth og Chebyshev approximation
%    - E-række komponentvalg (E6, E12, E24, E48, E96)
%    - Bode plot, Fase, Pol-nulpunkts-diagram, Gruppeløbetid
%    - SPICE-netliste eksport
%
%  Brug: Redigér parametrene i BRUGER INDSTILLINGER nedenfor,
%        og kør scriptet.
%% =========================================================

clc; clear; close all;

%% =========================================================
%  BRUGER INDSTILLINGER - Redigér her
%% =========================================================

FILTER_TYPE   = 'LP';          % 'LP' = Low-Pass, 'HP' = High-Pass
APPROX        = 'Butterworth'; % 'Butterworth' eller 'Chebyshev'
fc            = 1000;          % Cutoff frekvens [Hz]
fs            = 4000;          % Stopband frekvens [Hz]
Ac_dB         = 3;             % Passband dæmpning [dB]  (= ripple for Chebyshev)
As_dB         = 40;            % Stopband dæmpning [dB]
C_basis       = 10e-9;         % Basis kondensatorværdi [F]  (f.eks. 10e-9 = 10 nF)
E_SERIES_R    = 'E96';         % E-række for modstande: 'E12','E24','E48','E96'
E_SERIES_C    = 'E12';         % E-række for kondensatorer: 'E6','E12'
EXPORT_SPICE  = true;          % Eksportér SPICE netliste (true/false)
SPICE_USE_STD = true;          % Brug E-række værdier i SPICE (ellers eksakte)
SPICE_FILE    = 'filter.cir';  % Filnavn til SPICE eksport

%% =========================================================
%  E-RÆKKER
%% =========================================================

E_SERIES.E6  = [1.0, 1.5, 2.2, 3.3, 4.7, 6.8];
E_SERIES.E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2];
E_SERIES.E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, ...
                3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1];
E_SERIES.E48 = [1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, ...
                1.62, 1.69, 1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, ...
                2.61, 2.74, 2.87, 3.01, 3.16, 3.32, 3.48, 3.65, 3.83, 4.02, ...
                4.22, 4.42, 4.64, 4.87, 5.11, 5.36, 5.62, 5.90, 6.19, 6.49, ...
                6.81, 7.15, 7.50, 7.87, 8.25, 8.66, 9.09, 9.53];

% Generer E96 dynamisk
e96_raw = round(10.^((0:95)/96), 2);
E_SERIES.E96 = unique(e96_raw);

%% =========================================================
%  HJÆLPEFUNKTIONER
%% =========================================================

function result = find_closest_e(value, series_name, E_SERIES)
    % Finder nærmeste E-række værdi
    if value == 0
        result = value; return;
    end
    series = E_SERIES.(series_name);
    magnitude = floor(log10(value));
    normalized = value / (10^magnitude);
    [~, idx] = min(abs(series - normalized));
    result = series(idx) * (10^magnitude);
end

function result = find_higher_e(value, series_name, E_SERIES)
    % Finder næste højere E-række værdi
    if value == 0
        result = value; return;
    end
    series = E_SERIES.(series_name);
    magnitude = floor(log10(value));
    normalized = value / (10^magnitude);
    idx = find(series >= normalized - 1e-9, 1, 'first');
    if isempty(idx)
        result = series(1) * (10^(magnitude + 1));
    else
        result = series(idx) * (10^magnitude);
    end
end

function str = format_eng(val, comp_type)
    % Formaterer værdier med teknisk notation
    if val == 0
        str = '0'; return;
    end
    if comp_type == 'R'
        if val >= 1e6
            str = sprintf('%.2f MΩ', val/1e6);
        elseif val >= 1e3
            str = sprintf('%.2f kΩ', val/1e3);
        else
            str = sprintf('%.2f Ω', val);
        end
    else
        if val >= 1e-6
            str = sprintf('%.2f µF', val*1e6);
        elseif val >= 1e-9
            str = sprintf('%.2f nF', val*1e9);
        else
            str = sprintf('%.2f pF', val*1e12);
        end
    end
end

%% =========================================================
%  BEREGN FILTERORDEN
%% =========================================================

if strcmp(FILTER_TYPE, 'LP')
    ratio = fs / fc;
else
    ratio = fc / fs;
end

order_n = log10((10^(As_dB/10) - 1) / (10^(Ac_dB/10) - 1)) / (2 * log10(ratio));
order   = max(2, ceil(order_n));
if mod(order, 2) ~= 0
    order = order + 1;
end

fprintf('===========================================\n');
fprintf('  Sallen-Key Filter Design\n');
fprintf('===========================================\n');
fprintf('  Type:          %s\n', FILTER_TYPE);
fprintf('  Approksimation: %s\n', APPROX);
fprintf('  Cutoff fc:     %.1f Hz\n', fc);
fprintf('  Stopband fs:   %.1f Hz\n', fs);
fprintf('  Ac:            %.1f dB\n', Ac_dB);
fprintf('  As:            %.1f dB\n', As_dB);
fprintf('  Filter Orden:  %d (%d sektioner)\n', order, order/2);
fprintf('===========================================\n\n');

%% =========================================================
%  BEREGN POL-PLACERINGER
%% =========================================================

poles = struct('w0', {}, 'q', {});

if strcmp(APPROX, 'Butterworth')
    for k = 1:(order/2)
        q  = 1.0 / (2 * cos((2*k - 1) * pi / (2*order)));
        poles(k).w0 = 1.0;
        poles(k).q  = q;
    end
else % Chebyshev
    eps = sqrt(10^(Ac_dB/10) - 1);
    a   = asinh(1/eps) / order;
    for k = 1:(order/2)
        phi   = (2*k - 1) * pi / (2*order);
        sigma = -sinh(a) * sin(phi);
        omega =  cosh(a) * cos(phi);
        w0    = sqrt(sigma^2 + omega^2);
        q     = w0 / (-2 * sigma);
        poles(k).w0 = w0;
        poles(k).q  = q;
    end
end

%% =========================================================
%  KOMPONENT BEREGNING OG TABEL
%% =========================================================

fprintf('%-6s | %-18s | %-18s | %-10s\n', 'Komp.', 'Ideel / Krævet', 'E-række Valg', 'Q-faktor');
fprintf('%s\n', repmat('-', 1, 62));

val      = C_basis;
max_q    = 0;
spice_data = struct();

for i = 1:length(poles)
    wc     = 2 * pi * fc;
    w0_p   = poles(i).w0;
    q      = poles(i).q;

    if strcmp(FILTER_TYPE, 'LP')
        w0_actual = wc * w0_p;
    else
        w0_actual = wc / w0_p;
    end

    max_q = max(max_q, q);

    if strcmp(FILTER_TYPE, 'LP')
        % LP: C2 er basis, C1 >= 4*Q²*C2
        c2_std   = find_closest_e(val, E_SERIES_C, E_SERIES);
        c1_min   = c2_std * 4 * (q^2);
        c1_std   = find_higher_e(c1_min, E_SERIES_C, E_SERIES);
        c1_exact = c1_min;
        c2_exact = c2_std;

        radicand = 1 - (4 * (q^2) * c2_std / c1_std);
        if radicand < 0; radicand = 0; end
        factor   = 1 / (2 * w0_actual * q * c2_std);
        r1_exact = factor * (1 - sqrt(radicand));
        r2_exact = factor * (1 + sqrt(radicand));
    else
        % HP: C1 = C2 = basis
        c1_std   = find_closest_e(val, E_SERIES_C, E_SERIES);
        c2_std   = c1_std;
        c1_exact = c1_std;
        c2_exact = c2_std;
        r1_exact = 1 / (2 * w0_actual * q * c1_std);
        r2_exact = (2 * q) / (w0_actual * c1_std);
    end

    r1_std = find_closest_e(r1_exact, E_SERIES_R, E_SERIES);
    r2_std = find_closest_e(r2_exact, E_SERIES_R, E_SERIES);

    % Gem til SPICE
    spice_data(i).exact.r1 = r1_exact;
    spice_data(i).exact.r2 = r2_exact;
    spice_data(i).exact.c1 = c1_std;
    spice_data(i).exact.c2 = c2_std;
    spice_data(i).std.r1   = r1_std;
    spice_data(i).std.r2   = r2_std;
    spice_data(i).std.c1   = c1_std;
    spice_data(i).std.c2   = c2_std;

    % Print komponent tabel
    names    = {sprintf('R%d1',i), sprintf('R%d2',i), sprintf('C%d1',i), sprintf('C%d2',i)};
    exacts   = {r1_exact, r2_exact, c1_exact, c2_exact};
    stds     = {r1_std,   r2_std,   c1_std,   c2_std};
    ctypes   = {'R','R','C','C'};

    for j = 1:4
        exact_str = format_eng(exacts{j}, ctypes{j});
        std_str   = format_eng(stds{j}, ctypes{j});
        if j == 3 && strcmp(FILTER_TYPE, 'LP')
            exact_str = ['Min: ' exact_str];
        end
        fprintf('%-6s | %-18s | %-18s | Q=%.3f\n', names{j}, exact_str, std_str, q);
    end
    fprintf('%s\n', repmat('-', 1, 62));
end

% Stabilitetsvurdering
if max_q < 3.0
    fprintf('\n  Stabilitet: God (Max Q = %.2f)\n\n', max_q);
else
    fprintf('\n  ADVARSEL: Kritisk Q-faktor (Max Q = %.2f) - Risiko for ringing!\n\n', max_q);
end

%% =========================================================
%  BODE PLOT, FASE, POL-DIAGRAM, GRUPPELØBETID
%% =========================================================

f  = logspace(log10(fc/10), log10(fc*10), 1000);
w  = 2 * pi * f;
s  = 1j * w;
wc = 2 * pi * fc;

H           = ones(size(s));
s_poles_all = [];

for i = 1:length(poles)
    w0_p = poles(i).w0;
    q    = poles(i).q;

    alpha = -w0_p / (2*q);
    beta  =  w0_p * sqrt(abs(1 - 1/(4*q^2)));
    s_poles_all(end+1) = alpha + 1j*beta; %#ok<SAGROW>
    s_poles_all(end+1) = alpha - 1j*beta; %#ok<SAGROW>

    if strcmp(FILTER_TYPE, 'LP')
        w0_actual = wc * w0_p;
        H = H .* (w0_actual^2) ./ (s.^2 + (w0_actual/q).*s + w0_actual^2);
    else
        w0_actual = wc / w0_p;
        H = H .* (s.^2) ./ (s.^2 + (w0_actual/q).*s + w0_actual^2);
    end
end

mag_dB    = 20 * log10(max(abs(H), 1e-12));
phase_rad = unwrap(angle(H));
phase_deg = rad2deg(phase_rad);
gd_ms     = -gradient(phase_rad, w) * 1000;  % Gruppeløbetid i ms

figure('Name', 'Sallen-Key Filter', 'NumberTitle', 'off', ...
       'Position', [100, 100, 1100, 750], 'Color', 'white');

% --- Magnitude ---
subplot(2,2,1);
semilogx(f, mag_dB, 'Color', [0.173, 0.424, 0.569], 'LineWidth', 2);
hold on;
xline(fc, 'r--', 'Alpha', 0.5);
yline(-3, 'g:', 'Alpha', 0.5);
hold off;
title('Magnitude (dB)');
ylabel('Gain [dB]');
xlabel('Frekvens [Hz]');
grid on; grid minor;
xlim([f(1), f(end)]);

% --- Pol-diagram ---
subplot(2,2,2);
theta = linspace(0, 2*pi, 100);
plot(cos(theta), sin(theta), '--', 'Color', [0.8 0.8 0.8]); hold on;
plot(real(s_poles_all), imag(s_poles_all), 'rx', ...
     'MarkerSize', 10, 'LineWidth', 2);
xline(0, 'k', 'LineWidth', 1);
yline(0, 'k', 'LineWidth', 1);
hold off;
title('Pol-Diagram (S-plan)');
xlabel('Re'); ylabel('Im');
axis equal;
grid on;

% --- Fase ---
subplot(2,2,3);
semilogx(f, phase_deg, 'Color', [0.290, 0.620, 0.847], 'LineWidth', 2);
hold on;
xline(fc, 'r--', 'Alpha', 0.5);
hold off;
title('Fase (grader)');
ylabel('Fase [°]');
xlabel('Frekvens [Hz]');
grid on; grid minor;
xlim([f(1), f(end)]);

% --- Gruppeløbetid ---
subplot(2,2,4);
semilogx(f, gd_ms, 'Color', [0.851, 0.325, 0.310], 'LineWidth', 2);
hold on;
xline(fc, 'r--', 'Alpha', 0.5);
hold off;
title('Gruppeløbetid (Group Delay)');
ylabel('Delay [ms]');
xlabel('Frekvens [Hz]');
grid on; grid minor;
xlim([f(1), f(end)]);

sgtitle(sprintf('Sallen-Key %s Filter — %s, Orden %d, fc = %.0f Hz', ...
        FILTER_TYPE, APPROX, order, fc), 'FontSize', 13, 'FontWeight', 'bold');

%% =========================================================
%  SPICE NETLISTE EKSPORT
%% =========================================================

if EXPORT_SPICE
    fid = fopen(SPICE_FILE, 'w');
    if fid == -1
        warning('Kunne ikke oprette SPICE-fil: %s', SPICE_FILE);
    else
        if SPICE_USE_STD
            header_text = 'E-række R-værdier';
        else
            header_text = 'Eksakte matematiske R-værdier (C er standard)';
        end

        fprintf(fid, '* Sallen-Key %s Filter (%s)\n', FILTER_TYPE, header_text);
        fprintf(fid, 'Vin n0 0 AC 1\n');

        for i = 1:length(spice_data)
            if SPICE_USE_STD
                vals = spice_data(i).std;
            else
                vals = spice_data(i).exact;
            end

            p_node = sprintf('n%d', i-1);
            mid    = sprintf('n%dm', i);
            pos    = sprintf('n%dp', i);
            if i == length(spice_data)
                out = 'OUT';
            else
                out = sprintf('n%d', i);
            end

            if strcmp(FILTER_TYPE, 'LP')
                fprintf(fid, 'R%d1 %s %s %.2f\n', i, p_node, mid, vals.r1);
                fprintf(fid, 'R%d2 %s %s %.2f\n', i, mid, pos, vals.r2);
                fprintf(fid, 'C%d1 %s %s %.4e\n', i, mid, out, vals.c1);
                fprintf(fid, 'C%d2 %s 0 %.4e\n',  i, pos, vals.c2);
            else
                fprintf(fid, 'C%d1 %s %s %.4e\n', i, p_node, mid, vals.c1);
                fprintf(fid, 'C%d2 %s %s %.4e\n', i, mid, pos, vals.c2);
                fprintf(fid, 'R%d1 %s %s %.2f\n', i, mid, out, vals.r1);
                fprintf(fid, 'R%d2 %s 0 %.2f\n',  i, pos, vals.r2);
            end
            fprintf(fid, 'E%d %s 0 %s %s 1E6\n', i, out, pos, out);
        end

        fprintf(fid, '.ac dec 100 10 1Meg\n');
        fprintf(fid, '.meas AC Gain_ved_fc FIND vdb(OUT) AT %g\n', fc);
        fprintf(fid, '.end\n');
        fclose(fid);

        fprintf('SPICE netliste gemt: %s\n', SPICE_FILE);
    end
end

fprintf('Færdig.\n');
