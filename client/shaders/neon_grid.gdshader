shader_type spatial;

uniform vec3 grid_color : source_color = vec3(0.0, 1.0, 0.8); // Default Neon Teal
uniform float grid_size = 1.0;
uniform float line_width = 0.05;
uniform float glow_intensity = 2.0;
uniform float glitch_speed = 0.1;

float grid(vec2 uv) {
    vec2 grid_uv = fract(uv / grid_size);
    vec2 line = step(1.0 - line_width, grid_uv) + step(grid_uv, vec2(line_width));
    return max(line.x, line.y);
}

void fragment() {
    // Simple UV-based grid
    vec2 uv = UV * 10.0;
    
    // Add a slight "glitch" pulse based on time
    float pulse = sin(TIME * glitch_speed) * 0.1 + 0.9;
    float g = grid(uv);
    
    ALBEDO = vec3(0.0); // Keep floor dark
    EMISSION = grid_color * g * glow_intensity * pulse;
    ALPHA = g * 0.8; // Grid is semi-transparent
}
