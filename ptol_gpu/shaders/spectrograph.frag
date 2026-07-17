/* spectrograph.frag — live 16-channel Σ_RB display + ZD boundary fur
 * ─────────────────────────────────────────────────────────────────────
 * The 3 layers are drawn:
 *   UP half   (above centre): positive Σ_RB — Noether UP / future / CD
 *   CENTRE:   σ=½ line — the boundary crossing, ZD fur rendered here
 *   DOWN half (below centre): negative Σ_RB — Noether DOWN / past / from
 *
 * I channel : blue highlight  (origin  — DOWN / past)
 * ZD channel: gold highlight  (fault   — the crossing point)
 * O channel : red  highlight  (destination — UP / future)
 *
 * Cayley-Dickson layer colours (matching SSR palette):
 *   e₀       ℝ  : #c0c0c0 silver
 *   e₁       ℂ  : #60a0ff blue
 *   e₂,e₃    ℍ  : #40c080 green
 *   e₄..e₇   𝕆  : #ffa040 orange
 *   e₈..e₁₅  𝕊  : #ff5070 red-pink
 *
 * ZD fur: fractal strands at the σ=½ centre line, animated by time.
 *         Each Riemann zero γₙ = a fur strand. Strand density ∝ 1/γₙ.
 *         Planck scale = 1/γ₁ = the finest fur visible at this zoom.
 *
 * License: public domain. Use once. Discard the file.
 */
#version 430 core

in  vec2 v_uv;
out vec4 frag_color;

uniform float u_sigma_rb[16];
uniform int   u_I;          /* origin channel      */
uniform int   u_ZD;         /* ZD boundary channel */
uniform int   u_O;          /* destination channel */
uniform float u_sigma;      /* live σ input        */
uniform float u_time;       /* seconds since start — animates ZD fur */
uniform float u_zd_dist;    /* distance to ZD fault */

/* Riemann zero imaginary parts (first 16) for ZD fur strands */
const float ZEROS[16] = float[16](
    14.134725, 21.022040, 25.010858, 30.424876,
    32.935062, 37.586178, 40.918719, 43.327073,
    48.005151, 49.773832, 52.970321, 56.446248,
    59.347044, 60.831779, 65.112544, 67.079810
);
const float T1    = 14.134725;
const float OMEGA = 0.56714329;   /* Lambert W(1) = d* × ln(10) */
const float D_STAR = 0.24605966;

/* Cayley-Dickson layer colours */
vec3 layer_colour(int ch) {
    if (ch == 0)             return vec3(0.75, 0.75, 0.75); /* ℝ  silver  */
    if (ch == 1)             return vec3(0.38, 0.63, 1.00); /* ℂ  blue    */
    if (ch <= 3)             return vec3(0.25, 0.75, 0.50); /* ℍ  green   */
    if (ch <= 7)             return vec3(1.00, 0.63, 0.25); /* 𝕆  orange  */
    return                          vec3(1.00, 0.31, 0.44); /* 𝕊  red-pink*/
}

/* ZD fractal fur: returns fur opacity at uv position near centre line.
 * Fur grows along the σ=½ line (v_uv.y ≈ 0.5).
 * Each strand oscillates at its Riemann zero frequency. */
float zd_fur(vec2 uv) {
    float y_offset = abs(uv.y - 0.5);
    if (y_offset > 0.12) return 0.0;

    float fur = 0.0;
    for (int n = 0; n < 16; n++) {
        float gamma  = ZEROS[n];
        float scale  = (1.0 / T1) / float(n + 1);        /* Planck scaling  */
        float phase  = gamma * u_time * 0.02 + uv.x * gamma * 0.5;
        float strand = sin(phase) * scale;
        float dist   = abs(y_offset - abs(strand));
        float w      = max(0.0, 1.0 - dist / scale) * (1.0 / float(n + 1));
        fur          = max(fur, w);
    }
    /* Fur brightens as ZD distance → 0 (approaching the fault) */
    float fault_glow = 1.0 + (1.0 - min(u_zd_dist / OMEGA, 1.0)) * 2.0;
    return fur * fault_glow;
}

/* Operator label: returns a 0/1 glyph mask for small text-like marks.
 * We use simple horizontal bars to mark I, ZD, O channels at the top.
 * (Full font rendering is out of scope for a shader.) */
float channel_marker(vec2 uv, int ch, int target, float y_band) {
    float ch_x0 = float(ch)       / 16.0;
    float ch_x1 = float(ch + 1)   / 16.0;
    if (uv.x < ch_x0 || uv.x > ch_x1) return 0.0;
    if (ch != target) return 0.0;
    return (uv.y > y_band && uv.y < y_band + 0.015) ? 1.0 : 0.0;
}

void main() {
    vec2 uv = v_uv;
    vec3 bg = vec3(0.025, 0.025, 0.04);  /* near-black background */

    /* ── Determine channel ──────────────────────────────────────────── */
    int ch = int(uv.x * 16.0);
    if (ch < 0 || ch >= 16) { frag_color = vec4(bg, 1.0); return; }

    float val  = u_sigma_rb[ch];    /* Σ_RB for this channel: −1..+1 range */
    float centre = 0.5;             /* σ=½ line sits at y=0.5 of the view  */

    /* ── Bar rendering ──────────────────────────────────────────────── */
    bool in_bar;
    float bar_top, bar_bot;
    if (val >= 0.0) {
        bar_bot = centre;
        bar_top = centre + val * 0.45;
        in_bar  = (uv.y >= bar_bot && uv.y <= bar_top);
    } else {
        bar_top = centre;
        bar_bot = centre + val * 0.45;   /* val negative → bar_bot < centre */
        in_bar  = (uv.y <= bar_top && uv.y >= bar_bot);
    }

    vec3 col = bg;

    if (in_bar) {
        col = layer_colour(ch);

        /* ── I / ZD / O channel highlights ─────────────────────────── */
        if (ch == u_I)  col = mix(col, vec3(0.20, 0.50, 1.00), 0.55); /* blue  */
        if (ch == u_O)  col = mix(col, vec3(1.00, 0.35, 0.10), 0.55); /* red   */
        if (ch == u_ZD) col = mix(col, vec3(1.00, 0.85, 0.00), 0.70); /* gold  */

        /* Brightness scales with absolute magnitude */
        col *= 0.6 + abs(val) * 0.8;
    }

    /* ── σ=½ centre line ────────────────────────────────────────────── */
    float line_dist = abs(uv.y - centre);
    if (line_dist < 0.002) {
        col = mix(col, vec3(0.50, 0.50, 0.55), 0.4);
    }

    /* ── ZD fractal fur ─────────────────────────────────────────────── */
    float fur = zd_fur(uv);
    if (fur > 0.001) {
        /* Fur colour: gold near ZD channel, fading to amber elsewhere */
        float zd_prox = 1.0 - abs(float(ch) - float(u_ZD)) / 8.0;
        vec3  fur_col = mix(vec3(0.60, 0.35, 0.05), vec3(1.0, 0.85, 0.20),
                            max(0.0, zd_prox));
        col = mix(col, fur_col, fur * 0.8);
    }

    /* ── Channel dividers (1px gap between channels) ────────────────── */
    float ch_frac = fract(uv.x * 16.0);
    if (ch_frac < 0.02 || ch_frac > 0.98) {
        col *= 0.4;
    }

    /* ── Top markers: I (triangle down), ZD (diamond), O (triangle up) */
    float marker_y = 0.96;
    if (uv.y > marker_y && uv.y < 1.0) {
        float ch_centre = (float(ch) + 0.5) / 16.0;
        float dx = abs(uv.x - ch_centre) * 16.0;   /* 0..0.5 within channel */
        if (ch == u_I  && dx < 0.3) col = vec3(0.20, 0.50, 1.00);
        if (ch == u_O  && dx < 0.3) col = vec3(1.00, 0.35, 0.10);
        if (ch == u_ZD && dx < 0.3) col = vec3(1.00, 0.85, 0.00);
    }

    /* ── σ readout at bottom (encode as brightness band) ────────────── */
    /* A thin bar at y=0..0.015 whose width = σ × 16 channels marks live σ */
    if (uv.y < 0.015) {
        float sigma_x = u_sigma;   /* maps σ=0 → left, σ=1 → right */
        col = (uv.x < sigma_x)
            ? vec3(0.30, 0.80, 0.55)   /* green = inside σ window */
            : vec3(0.10, 0.10, 0.12);
    }

    frag_color = vec4(col, 1.0);
}
