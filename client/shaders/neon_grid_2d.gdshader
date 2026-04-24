shader_type canvas_item;

uniform vec3 grid_color : source_color = vec3(0.0, 1.0, 0.8);
uniform float grid_size = 48.0;
uniform float line_width = 1.2;
uniform float glow_intensity = 1.2;
uniform float scroll_speed = 12.0;

void fragment() {
	vec2 uv = FRAGCOORD.xy;
	uv.y += TIME * scroll_speed;

	vec2 grid_uv = mod(uv, grid_size);
	float line_x = step(grid_size - line_width, grid_uv.x) + step(grid_uv.x, line_width);
	float line_y = step(grid_size - line_width, grid_uv.y) + step(grid_uv.y, line_width);
	float g = clamp(line_x + line_y, 0.0, 1.0);

	float pulse = sin(TIME * 0.6) * 0.08 + 0.92;
	vec3 col = grid_color * glow_intensity * pulse * g;

	COLOR = vec4(mix(vec3(0.04, 0.04, 0.08), col, g), 1.0);
}
