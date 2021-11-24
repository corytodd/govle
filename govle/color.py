import random

WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)

def to_hex(rgb):
    """Make hex string from color tuple"""
    return "0x" + "".join([f"{b:02X}" for b in rgb])

def from_string(hex_color):
    """Create RGB tuple from hex string"""
    hex_color = hex_color.replace("#","")
    rgb = (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )
    return rgb

def get_random_color():
    """Generate a random RGB color"""
    rgb = random.sample(range(0, 255), 3)
    return tuple(rgb)

def get_random_complementary_pair():
    """Generates a random pair of complementary colors"""
    rgb = get_random_color()
    rgb_hex = rgb[0] << 16 | rgb[1] << 8 | rgb[2]
    rgb_comp = 0xFFFFFF - rgb_hex
    rbg_comp = (
        (rgb_comp >> 16) & 0xFF,
        (rgb_comp >> 8) & 0xFF,
        rgb_comp & 0xFF
    )
    return rgb, rbg_comp