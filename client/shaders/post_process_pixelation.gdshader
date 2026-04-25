shader_type canvas_item;

uniform int pixel_size = 4;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
    vec2 uv = SCREEN_UV;
    float x = float(int(uv.x * float(textureSize(screen_texture, 0).x) / float(pixel_size))) * float(pixel_size) / float(textureSize(screen_texture, 0).x);
    float y = float(int(uv.y * float(textureSize(screen_texture, 0).y) / float(pixel_size))) * float(pixel_size) / float(textureSize(screen_texture, 0).y);
    
    vec3 color = texture(screen_texture, vec2(x, y)).rgb;
    
    // Slight color crushing for that lo-fi feel
    color = floor(color * 16.0) / 16.0;
    
    COLOR = vec4(color, 1.0);
}
