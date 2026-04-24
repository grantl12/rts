shader_type spatial;

uniform vec3 dead_zone_color : source_color = vec3(0.1, 0.1, 0.1);
uniform float radius = 5.0;
uniform float edge_fuzz = 0.5;

void fragment() {
	// This shader effectively "erases" the Neon Grid emission 
	// and returns the surface to its "Analog" state.
	float dist = length(UV - vec2(0.5));
	float mask = smoothstep(radius, radius - edge_fuzz, dist);
	
	ALBEDO = dead_zone_color;
	ALPHA = 1.0 - mask; // Only shows up outside the Analog Zone
}
