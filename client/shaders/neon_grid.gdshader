shader_type spatial;

uniform vec3  grid_color : source_color = vec3(0.05, 0.55, 0.72);
uniform float grid_size      = 1.0;
uniform float line_width     = 0.04;
uniform float glow_intensity = 0.65;
uniform float glitch_speed   = 0.018;

float grid(vec2 uv) {
	vec2 grid_uv = fract(uv / grid_size);
	vec2 line    = step(1.0 - line_width, grid_uv) + step(grid_uv, vec2(line_width));
	return max(line.x, line.y);
}

void fragment() {
	vec2  uv      = UV * 10.0;
	float pulse   = sin(TIME * glitch_speed) * 0.1 + 0.9;
	float g       = grid(uv);

	// Fade grid lines to zero within the outer 12 % of the UV space
	// so the boundary dissolves rather than cutting off sharply.
	vec2  edge     = min(UV, 1.0 - UV);
	float vignette = smoothstep(0.0, 0.12, min(edge.x, edge.y));

	// ALBEDO matches the outer void plane and the sky background colour,
	// so the faded edge blends invisibly into the surroundings.
	ALBEDO   = vec3(0.04, 0.04, 0.08);
	EMISSION = grid_color * g * glow_intensity * pulse * vignette;
}
