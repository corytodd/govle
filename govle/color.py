import random

WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)

def to_hex(rgb):
    """Make hex string from color tuple"""
    return "0x" + "".join([f"{b:02X}" for b in rgb])

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