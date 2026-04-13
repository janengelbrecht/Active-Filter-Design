%% =========================================================
%  Multiple Feedback (MFB) Bandpass Filter Design Tool
%  MATLAB-ækvivalent til mfbp.py
%
%  Understøtter:
%    - Butterworth og Chebyshev LP-prototype → Bandpass transformation
%    - MFB biquad-komponentberegning med gain-kompensation
%    - E-række komponentvalg (E6, E12, E24, E48, E96)
%    - Bode plot, Fase, Pol-diagram, Gruppeløbetid
%    - SPICE-netliste eksport
%
%  Brug: Redigér parametrene i BRUGER INDSTILLINGER nedenfor,
%        og kør scriptet.
%% =========================================================

clc; clear; close all;

%% =========================================================
%  BRUGER INDSTILLINGER - Redigér her
%% =========================================================

APPROX        = 'Butterworth'; % 'Butterworth' eller 'Chebyshev'
fn            = 900;           % Passband nedre grænse [Hz]
fo            = 1100;          % Passband øvre grænse [Hz]
fsn           = 300;           % Stopband nedre grænse [Hz]
fso           = 3300;          % Stopband øvre grænse [Hz]
Ac_dB         = 3.0;           % Passband dæmpning [dB] (= ripple for Chebyshev)
As_dB         = 40;            % Stopband dæmpning [dB]
total_gain    = 1.0;           % Ønsket samlet gain ved f0 [V/V]
C_basis       = 10e-9;         % Basis kondensatorværdi [F]  (f.eks. 10e-9 = 10 nF)
E_SERIES_R    = 'E96';         % E-række for modstande: 'E12','E24','E48','E96'
E_SERIES_C    = 'E12';         % E-række for kondensatorer: 'E6','E12'
EXPORT_SPICE  = true;          % Eksportér SPICE netliste (true/false)
SPICE_USE_STD = true;          % Brug E-række værdier i SPICE (ellers eksakte)
SPICE_FILE    = 'mfb_filter.cir'; % Filnavn til SPICE eksport

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
e96_raw = round(10.^((0:95)./96), 2);
E_SERIES.E96 = unique(e96_raw);

%% =========================================================
%  HJÆLPEFUNKTIONER (nested, kræver MATLAB R2016b+)
%% =========================================================

    function result = find_closest_e(value, series_name, ES)
        if value == 0; result = 0; return; end
        series    = ES.(series_name);
        magnitude = floor(log10(abs(value)));
        normalized = value / (10^magnitude);
        [~, idx]  = min(abs(series - normalized));
        result    = series(idx) * (10^magnitude);
    end

    function str = format_eng(val, comp_type)
        if val == 0; str = '0'; return; end
        if comp_type == 'R'
            if val >= 1e6;     str = sprintf('%.2f MΩ', val/1e6);
            elseif val >= 1e3; str = sprintf('%.2f kΩ', val/1e3);
            else;              str = sprintf('%.2f Ω',  val);
            end
        else
            if val >= 1e-6;    str = sprintf('%.2f µF', val*1e6);
            elseif val >= 1e-9;str = sprintf('%.2f nF', val*1e9);
            else;              str = sprintf('%.2f pF', val*1e12);
            end
        end
    end

%% =========================================================
%  VALIDÉR INPUT
%% =========================================================

bw_pass = fo - fn;
bw_stop = fso - fsn;

if Ac_dB <= 0;            error('Ac skal være > 0'); end
if bw_pass <= 0;          error('fn skal være < fo'); end
if bw_stop <= bw_pass;    error('Stopbåndet skal være bredere end passbåndet'); end

f0_center = sqrt(fn * fo);          % Geometrisk centrefrekvens [Hz]
w0_center = 2 * pi * f0_center;
bw_rad    = 2 * pi * bw_pass;       % Båndbredde [rad/s]
ratio     = bw_stop / bw_pass;      % Selektivitetsforhold

%% =========================================================
%  BEREGN FILTERORDEN  (LP prototype)
%% =========================================================

order_n  = log10((10^(As_dB/10) - 1) / (10^(Ac_dB/10) - 1)) / (2 * log10(ratio));
order_lp = max(1, ceil(order_n));
if mod(order_lp, 2) ~= 0
    order_lp = order_lp + 1;
end

fprintf('===========================================\n');
fprintf('  MFB Bandpass Filter Design\n');
fprintf('===========================================\n');
fprintf('  Approksimation:   %s\n', APPROX);
fprintf('  Passband:         %.1f Hz – %.1f Hz\n', fn, fo);
fprintf('  Stopband:         %.1f Hz – %.1f Hz\n', fsn, fso);
fprintf('  Centrefrekvens:   %.2f Hz\n', f0_center);
fprintf('  Båndbredde:       %.1f Hz\n', bw_pass);
fprintf('  Ac:               %.1f dB\n', Ac_dB);
fprintf('  As:               %.1f dB\n', As_dB);
fprintf('  LP Prototype Orden: %d\n', order_lp);

%% =========================================================
%  LP-PROTOTYPE POLER
%% =========================================================

lp_poles = struct('w0', {}, 'q', {});

if strcmp(APPROX, 'Butterworth')
    for k = 1:(order_lp/2)
        q_lp          = 1.0 / (2 * cos((2*k - 1) * pi / (2*order_lp)));
        lp_poles(k).w0 = 1.0;
        lp_poles(k).q  = q_lp;
    end
else % Chebyshev
    eps = sqrt(10^(Ac_dB/10) - 1);
    a   = asinh(1/eps) / order_lp;
    for k = 1:(order_lp/2)
        phi   = (2*k - 1) * pi / (2*order_lp);
        sigma = -sinh(a) * sin(phi);
        omega =  cosh(a) * cos(phi);
        w0_lp = sqrt(sigma^2 + omega^2);
        q_lp  = w0_lp / (-2 * sigma);
        lp_poles(k).w0 = w0_lp;
        lp_poles(k).q  = q_lp;
    end
end

%% =========================================================
%  LP → BP TRANSFORMATION
%  Hver LP pol giver to BP biquads (konjugerede par)
%% =========================================================

bp_biquads = [];

for p = lp_poles
    w0_lp = p.w0;
    q_lp  = p.q;

    % LP pol i s-planet (tager øvre halvplan)
    alpha = -w0_lp / (2 * q_lp);
    beta  =  w0_lp * sqrt(abs(1 - 1/(4*q_lp^2)));
    p_lp  = complex(alpha, beta);   % LP kompleks pol

    % Kvadratisk ligning: s^2 - p_lp*bw_rad*s + w0_center^2 = 0
    coeffs = [1, -p_lp * bw_rad, w0_center^2];
    roots_bp = roots(coeffs);

    for r = roots_bp.'
        wk = abs(r);
        qk = wk / (-2 * real(r));
        bp_biquads(end+1).w0 = wk;  %#ok<SAGROW>
        bp_biquads(end).q    = qk;
    end
end

% Sorter sektioner efter Q (lavest Q først, som Python)
[~, idx] = sort([bp_biquads.q]);
bp_biquads = bp_biquads(idx);
num_sections = length(bp_biquads);

fprintf('  BP Sektioner:     %d (Filterorden %d)\n', num_sections, num_sections*2);
fprintf('===========================================\n\n');

%% =========================================================
%  GAIN KOMPENSATION VED f0
%  Beregn naturligt tab ved f0 for alle sektioner samlet,
%  og fordel kompensations-gain ligeligt
%% =========================================================

s_at_f0    = 1j * w0_center;
H_at_f0    = 1.0;

for bq = bp_biquads
    wk = bq.w0; qk = bq.q;
    H_at_f0 = H_at_f0 * ((wk/qk) * s_at_f0) / ...
              (s_at_f0^2 + (wk/qk)*s_at_f0 + wk^2);
end

natural_loss = abs(H_at_f0);
Ak_target    = (total_gain / natural_loss)^(1/num_sections);

%% =========================================================
%  KOMPONENT BEREGNING OG TABEL
%% =========================================================

fprintf('%-6s | %-18s | %-18s | %-25s\n', 'Komp.', 'Ideel Værdi', 'E-række Valg', 'Sektion Info');
fprintf('%s\n', repmat('-', 1, 75));

spice_data = struct();
max_q = 0;
val   = C_basis;

for i = 1:num_sections
    wk = bp_biquads(i).w0;
    qk = bp_biquads(i).q;
    max_q = max(max_q, qk);

    c_std = find_closest_e(val, E_SERIES_C, E_SERIES);

    % MFB Bandpass ligninger
    r3_exact = 2 * qk / (wk * c_std);
    r1_exact = qk / (Ak_target * wk * c_std);

    denom = 2 * qk^2 - Ak_target;
    if denom <= 0
        % Gain for høj ift. denne sektions Q — begræns lokalt
        local_Ak = 1.8 * qk^2;
        r1_exact = qk / (local_Ak * wk * c_std);
        r2_exact = qk / (wk * c_std * (2*qk^2 - local_Ak));
        info_text = sprintf('Q=%.2f (Gain begrænset)', qk);
    else
        r2_exact = qk / (wk * c_std * denom);
        info_text = sprintf('Q=%.2f, Ak=%.2f', qk, Ak_target);
    end

    r1_std = find_closest_e(r1_exact, E_SERIES_R, E_SERIES);
    r2_std = find_closest_e(r2_exact, E_SERIES_R, E_SERIES);
    r3_std = find_closest_e(r3_exact, E_SERIES_R, E_SERIES);

    % Gem til SPICE og plot
    spice_data(i).exact.r1 = r1_exact;
    spice_data(i).exact.r2 = r2_exact;
    spice_data(i).exact.r3 = r3_exact;
    spice_data(i).exact.c1 = c_std;
    spice_data(i).exact.c2 = c_std;
    spice_data(i).std.r1   = r1_std;
    spice_data(i).std.r2   = r2_std;
    spice_data(i).std.r3   = r3_std;
    spice_data(i).std.c1   = c_std;
    spice_data(i).std.c2   = c_std;
    spice_data(i).Ak       = Ak_target;
    spice_data(i).w0       = wk;
    spice_data(i).q        = qk;

    % Print komponenttabel
    names  = {sprintf('R%d1',i), sprintf('R%d2',i), sprintf('R%d3',i), ...
              sprintf('C%d1',i), sprintf('C%d2',i)};
    exacts = {r1_exact, r2_exact, r3_exact, c_std, c_std};
    stds   = {r1_std, r2_std, r3_std, c_std, c_std};
    ctypes = {'R','R','R','C','C'};

    for j = 1:5
        info_col = '';
        if j == 1; info_col = info_text; end
        fprintf('%-6s | %-18s | %-18s | %-25s\n', ...
            names{j}, format_eng(exacts{j}, ctypes{j}), ...
            format_eng(stds{j}, ctypes{j}), info_col);
    end
    fprintf('%s\n', repmat('-', 1, 75));
end

fprintf('\n  Filter Orden: %d (%d sektioner)\n', num_sections*2, num_sections);
if max_q < 8
    fprintf('  Stabilitet: God (Max Q = %.1f)\n\n', max_q);
else
    fprintf('  ADVARSEL: Højt Q (%.1f) — Brug 1%% tolerancer!\n\n', max_q);
end

%% =========================================================
%  BODE PLOT, FASE, POL-DIAGRAM, GRUPPELØBETID
%% =========================================================

f  = logspace(log10(fn/10), log10(fo*10), 2000);
w  = 2 * pi * f;
s  = 1j * w;
H  = ones(size(s));
s_poles_all = [];

for i = 1:num_sections
    wk = spice_data(i).w0;
    qk = spice_data(i).q;
    Ak = spice_data(i).Ak;

    % MFB BP overføringsfunktion: H(s) = -Ak*(wk/qk)*s / (s^2 + (wk/qk)*s + wk^2)
    H = H .* (-Ak * (wk/qk) .* s) ./ (s.^2 + (wk/qk).*s + wk^2);

    alpha = -wk / (2*qk);
    beta  =  wk * sqrt(abs(1 - 1/(4*qk^2)));
    s_poles_all(end+1) = alpha + 1j*beta; %#ok<SAGROW>
    s_poles_all(end+1) = alpha - 1j*beta; %#ok<SAGROW>
end

mag_dB    = 20 * log10(abs(H) + 1e-12);
phase_rad = unwrap(angle(H));
phase_deg = rad2deg(phase_rad);
gd_ms     = -gradient(phase_rad, w) * 1000;

figure('Name', 'MFB Bandpass Filter', 'NumberTitle', 'off', ...
       'Position', [100, 80, 1150, 760], 'Color', 'white');

% --- Magnitude ---
subplot(2,2,1);
semilogx(f, mag_dB, 'b', 'LineWidth', 2);
hold on;
xline(f0_center, 'g--', 'LineWidth', 1.2, 'Alpha', 0.8);
xline(fn, 'r:', 'LineWidth', 1, 'Alpha', 0.7);
xline(fo, 'r:', 'LineWidth', 1, 'Alpha', 0.7);
hold off;
title('Magnitude (dB)');
ylabel('Gain [dB]');
xlabel('Frekvens [Hz]');
grid on; grid minor;
xlim([f(1), f(end)]);
legend('|H(f)|', 'f_0', 'f_n / f_o', 'Location', 'SouthEast');

% --- Pol-diagram ---
subplot(2,2,2);
plot(real(s_poles_all), imag(s_poles_all), 'rx', ...
     'MarkerSize', 10, 'LineWidth', 2);
hold on;
xline(0, 'k', 'LineWidth', 1);
yline(0, 'k', 'LineWidth', 1);
hold off;
title('S-Plan (Poler)');
xlabel('Re'); ylabel('Im');
grid on;
axis equal;

% --- Fase ---
subplot(2,2,3);
semilogx(f, phase_deg, 'Color', [0.5 0 0.8], 'LineWidth', 2);
hold on;
xline(f0_center, 'g--', 'LineWidth', 1.2, 'Alpha', 0.7);
hold off;
title('Fase (grader)');
ylabel('Fase [°]');
xlabel('Frekvens [Hz]');
grid on; grid minor;
xlim([f(1), f(end)]);

% --- Gruppeløbetid ---
subplot(2,2,4);
semilogx(f, gd_ms, 'r', 'LineWidth', 2);
hold on;
xline(f0_center, 'g--', 'LineWidth', 1.2, 'Alpha', 0.7);
hold off;
title('Gruppeløbetid (Group Delay)');
ylabel('Delay [ms]');
xlabel('Frekvens [Hz]');
grid on; grid minor;
xlim([f(1), f(end)]);

sgtitle(sprintf('MFB Bandpass — %s, %d sektioner, f_0 = %.1f Hz, BW = %.1f Hz', ...
        APPROX, num_sections, f0_center, bw_pass), ...
        'FontSize', 13, 'FontWeight', 'bold');

%% =========================================================
%  SPICE NETLISTE EKSPORT
%% =========================================================

if EXPORT_SPICE
    fid = fopen(SPICE_FILE, 'w');
    if fid == -1
        warning('Kunne ikke oprette SPICE-fil: %s', SPICE_FILE);
    else
        fprintf(fid, '* MFB Bandpass Netliste\n');
        fprintf(fid, 'Vin n0 0 AC 1\n');

        for i = 1:num_sections
            if SPICE_USE_STD
                v = spice_data(i).std;
            else
                v = spice_data(i).exact;
            end

            inn = sprintf('n%d', i-1);
            if i < num_sections
                out = sprintf('n%d', i);
            else
                out = 'VOUT';
            end
            mid = sprintf('n%dm', i);
            inv = sprintf('n%dinv', i);

            fprintf(fid, 'R%d1 %s %s %.2f\n',    i, inn, mid, v.r1);
            fprintf(fid, 'R%d2 %s 0 %.2f\n',      i, mid, v.r2);
            fprintf(fid, 'R%d3 %s %s %.2f\n',    i, inv, out, v.r3);
            fprintf(fid, 'C%d1 %s %s %.4e\n',    i, mid, out, v.c1);
            fprintf(fid, 'C%d2 %s %s %.4e\n',    i, mid, inv, v.c2);
            fprintf(fid, 'XOP%d 0 %s %s IDEAL_OP\n', i, inv, out);
        end

        fprintf(fid, '* Ideel OP-AMP model\n');
        fprintf(fid, '.subckt IDEAL_OP 1 2 3\n');
        fprintf(fid, 'E1 3 0 1 2 1E6\n');
        fprintf(fid, '.ends\n');
        fprintf(fid, '.ac dec 100 10 1Meg\n');
        fprintf(fid, '.end\n');
        fclose(fid);
        fprintf('SPICE netliste gemt: %s\n', SPICE_FILE);
    end
end

fprintf('Færdig.\n');
