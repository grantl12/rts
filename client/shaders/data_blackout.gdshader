shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, unshaded;

// Up to 32 vision-granting positions (player units + buildings)
uniform vec3  vis_positions[32];
uniform int   vis_count    = 0;
uniform float vis_radius   : hint_range(5.0, 60.0) = 28.0;
uniform float fog_density  : hint_range(0.0, 1.0)  = 0.88;

varying vec2 world_xz;

void vertex() {
	// UV spans 0..1 across the 200×200 plane centred on world origin.
	// Map to world XZ: x ∈ [-100, 100], z ∈ [-100, 100]
	world_xz = (UV - vec2(0.5, 0.5)) * 200.0;
}

void fragment() {
	float visibility = 0.0;
	for (int i = 0; i < vis_count; i++) {
		float d = length(world_xz - vec2(vis_positions[i].x, vis_positions[i].z));
		// Soft edge: fully clear inside 60 % of radius, fades out to edge
		float v = 1.0 - smoothstep(vis_radius * 0.6, vis_radius, d);
		visibility = max(visibility, v);
	}

	// Dark Data Blackout colour with faction-neutral tint
	ALBEDO = vec3(0.01, 0.01, 0.05);
	ALPHA  = fog_density * (1.0 - visibility);
}
