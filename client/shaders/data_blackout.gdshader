shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, unshaded;

// Up to 32 vision-granting positions (player units + buildings).
// Each source carries its own radius so Watchtowers can see further.
uniform vec3  vis_positions[32];
uniform float vis_radii[32];
uniform int   vis_count   = 0;
uniform float fog_density : hint_range(0.0, 1.0) = 0.88;

varying vec2 world_xz;

void vertex() {
	// UV spans 0..1 across the 200×200 plane centred on world origin.
	world_xz = (UV - vec2(0.5, 0.5)) * 200.0;
}

void fragment() {
	float visibility = 0.0;
	for (int i = 0; i < vis_count; i++) {
		float d = length(world_xz - vec2(vis_positions[i].x, vis_positions[i].z));
		float r = vis_radii[i];
		float v = 1.0 - smoothstep(r * 0.6, r, d);
		visibility = max(visibility, v);
	}

	ALBEDO = vec3(0.01, 0.01, 0.05);
	ALPHA  = fog_density * (1.0 - visibility);
}
