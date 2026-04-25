shader_type spatial;
render_mode unshaded, cull_disabled;

uniform vec3 color : source_color = vec3(0.0, 1.0, 0.6);
uniform float glitch_intensity : hint_range(0.0, 1.0) = 0.2;
uniform float line_width : hint_range(0.0, 0.5) = 0.05;

float random(vec2 uv) {
    return fract(sin(dot(uv.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

void fragment() {
    vec2 uv = UV;
    
    // Create corner bracket logic
    float border = line_width;
    bool is_corner = (uv.x < border || uv.x > 1.0 - border) || (uv.y < border || uv.y > 1.0 - border);
    
    if (!is_corner) {
        discard;
    }
    
    // Add flickering glitch
    float flicker = step(0.1, random(vec2(TIME * 10.0, 0.0)));
    float glitch = random(vec2(floor(uv.y * 20.0), TIME)) * glitch_intensity;
    
    ALBEDO = color;
    ALPHA = flicker * (0.8 + glitch);
}
