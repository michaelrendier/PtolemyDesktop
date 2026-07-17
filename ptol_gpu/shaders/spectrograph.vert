/* spectrograph.vert — vertex shader for live Σ_RB display
 * Passes UV to fragment shader. Quad covers the full window.
 */
#version 430 core

out vec2 v_uv;

/* Full-screen triangle trick — no VBO needed.
 * gl_VertexID: 0→(−1,−1), 1→(3,−1), 2→(−1,3) */
void main() {
    vec2 pos = vec2(
        (gl_VertexID == 1) ? 3.0 : -1.0,
        (gl_VertexID == 2) ? 3.0 : -1.0
    );
    v_uv        = pos * 0.5 + 0.5;
    gl_Position = vec4(pos, 0.0, 1.0);
}
