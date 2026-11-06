"""Brand + resize the 9 Pexels photos into discover variants."""
from PIL import Image, ImageDraw, ImageFont, ImageOps
import pathlib, os

SRC_DIR = pathlib.Path(r"C:\Users\arkra\Downloads")
OUT_DIR = pathlib.Path(r"C:\Users\arkra\NVY DMRV\nvy-dmrv-dashboard\public\assets\images\discover")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (source filename, output stem)
MAP = [
    ("pexels-ralf-ruppert-2165046205-40760368.jpg", "default-2"),        # JOBS blocks
    ("pexels-ann-hannes-45017-38824378.jpg", "default-3"),              # WE ARE HIRING
    ("pexels-andrei-simon-amisi-2159595332-36198132.jpg", "esg-2"),     # cracked dry earth
    ("pexels-tieugiang007-35298887.jpg", "esg-3"),                      # factory smoke over river
    ("pexels-alex-sanchez-2150797975-32408717.jpg", "esg-4"),           # wind turbines
    ("pexels-marek-piwnicki-3907296-20495914.jpg", "esg-5"),            # geothermal steam
    ("pexels-francesco-ungaro-30429916.jpg", "research-2"),             # antarctica ice
    ("pexels-silverkblack-36733322.jpg", "events-2"),                   # office meeting
    ("pexels-shubhamthakur-39293484.jpg", "forestry-2"),                # people planting field
]

W, H = 1200, 675
TEXT = "urbanforestpark.com"

def find_font(size):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\seguisb.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()

def brand(im, out_webp, out_jpg):
    # Centre-crop to 16:9 then resize
    im = ImageOps.exif_transpose(im).convert("RGB")
    target_ratio = 16/9
    w, h = im.size
    r = w/h
    if r > target_ratio:
        nw = int(h*target_ratio); x=(w-nw)//2; im = im.crop((x,0,x+nw,h))
    else:
        nh = int(w/target_ratio); y=(h-nh)//2; im = im.crop((0,y,w,y+nh))
    im = im.resize((W,H), Image.LANCZOS)

    # Bottom gradient for readability (fades up 90px)
    overlay = Image.new("RGBA", (W,H), (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    strip = 90
    for i in range(strip):
        alpha = int(140 * (i/strip) ** 1.2)  # darker at bottom
        d.line([(0, H-strip+i),(W, H-strip+i)], fill=(4,26,18,alpha))
    im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(im)
    font = find_font(36)
    # measure
    pad_x, pad_y = 14, 10
    # text bbox
    bbox = draw.textbbox((0,0), TEXT, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    box_w, box_h = tw + pad_x*2, th + pad_y*2
    margin = 22
    x0 = W - box_w - margin
    y0 = H - box_h - margin
    # pill background (dark green, semi-opaque -> draw solid on RGB for consistency)
    draw.rounded_rectangle([x0,y0,x0+box_w,y0+box_h], radius=12, fill=(6,38,26))
    # thin green accent border
    draw.rounded_rectangle([x0,y0,x0+box_w,y0+box_h], radius=12, outline=(94,234,179), width=2)
    draw.text((x0+pad_x-bbox[0], y0+pad_y-bbox[1]), TEXT, font=font, fill=(255,255,255))
    # small URBAN FOREST PARK label top-left for trademark (subtle, readable)
    font2 = find_font(26)
    label = "URBAN FOREST PARK"
    bbox2 = draw.textbbox((0,0), label, font=font2)
    tw2, th2 = bbox2[2]-bbox2[0], bbox2[3]-bbox2[1]
    x1, y1 = 22, 20
    bw, bh = tw2+pad_x*2, th2+pad_y*2
    draw.rounded_rectangle([x1,y1,x1+bw,y1+bh], radius=10, fill=(6,38,26))
    draw.rounded_rectangle([x1,y1,x1+bw,y1+bh], radius=10, outline=(94,234,179), width=2)
    draw.text((x1+pad_x-bbox2[0], y1+pad_y-bbox2[1]), label, font=font2, fill=(167,243,208))

    im.save(out_webp, "WEBP", quality=78, method=6)
    im.save(out_jpg, "JPEG", quality=78)
    print(out_webp.name, out_webp.stat().st_size, "|", out_jpg.name, out_jpg.stat().st_size)

for src, stem in MAP:
    p = SRC_DIR/src
    assert p.exists(), p
    with Image.open(p) as im:
        brand(im, OUT_DIR/f"{stem}.webp", OUT_DIR/f"{stem}.jpg")

print("done")
