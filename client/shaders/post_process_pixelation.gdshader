shader_type canvas_item;

uniform int pixel_size = 3;
uniform float scanline_intensity = 0.15;
uniform float color_bleed = 0.001;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
    vec2 uv = SCREEN_UV;
    
    // Pixelation
    vec2 resolution = vec2(textureSize(screen_texture, 0));
    vec2 pixel_uv = floor(uv * resolution / float(pixel_size)) * float(pixel_size) / resolution;
    
    // Color Bleed (Pseudo-Chromatic Aberration for CRT feel)
    float r = texture(screen_texture, pixel_uv + vec2(color_bleed, 0.0)).r;
    float g = texture(screen_texture, pixel_uv).g;
    float b = texture(screen_texture, pixel_uv - vec2(color_bleed, 0.0)).b;
    vec3 color = vec4(r, g, b, 1.0).rgb;
    
    // CRT Scanlines
    float scanline = sin(uv.y * resolution.y * 1.5) * scanline_intensity;
    color -= scanline;
    
    // Gritty Contrast / Color Crushing
    color = mix(color, floor(color * 8.0) / 8.0, 0.5); # Gritty palette
    
    COLOR = vec4(color, 1.0);
}
