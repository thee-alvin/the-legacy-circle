from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parents[1]
SIG_DIR = BASE / "frontend" / "assets" / "signatures"
BACKUP_DIR = SIG_DIR / "originals"

BACKUP_DIR.mkdir(exist_ok=True)

FILES = [
    "derrick_were_signature.png",
    "owuor_alvin_signature.png",
    "fedel_rimba_signature.png",
    "elly_wandago_signature.png",
    "sheela_onyango_signature.png",
    "faith_tracy_signature.png",
    "sheela_onyango_official_signature.png",
    "faith_tracy_official_signature.png",
    "owuor_alvin_official_signature.png",
]


def clean_signature(source, destination):

    image = Image.open(source).convert("RGBA")

    # Preserve the original.
    backup = BACKUP_DIR / source.name

    if not backup.exists():
        image.save(backup)

    # Convert to grayscale.
    gray = image.convert("L")

    # Dark pixels become visible alpha.
    # Amplification makes light scanned signatures much clearer.
    alpha = gray.point(
        lambda p: min(255, max(0, (255 - p) * 4))
    )

    # Remove very faint background noise.
    alpha = alpha.point(
        lambda p: 0 if p < 18 else p
    )

    result = Image.new(
        "RGBA",
        gray.size,
        (0, 0, 0, 0)
    )

    black = Image.new(
        "RGBA",
        gray.size,
        (15, 25, 40, 255)
    )

    result.paste(
        black,
        (0, 0),
        alpha
    )

    # Trim empty space around the signature.
    bbox = result.getchannel("A").getbbox()

    if bbox:
        left, top, right, bottom = bbox

        pad = 8

        left = max(0, left - pad)
        top = max(0, top - pad)
        right = min(result.width, right + pad)
        bottom = min(result.height, bottom + pad)

        result = result.crop(
            (left, top, right, bottom)
        )

    result.save(
        destination,
        optimize=True
    )


# The official Chairperson signature is the same
# signature shown for Sheela Onyango in the Constitution.
sheela = SIG_DIR / "sheela_onyango_signature.png"
sheela_official = SIG_DIR / "sheela_onyango_official_signature.png"

if sheela.exists():
    # Replace the incorrect extracted heading.
    Image.open(sheela).convert("RGBA").save(
        sheela_official
    )


for filename in FILES:

    source = SIG_DIR / filename

    if not source.exists():
        print(f"SKIPPED: {filename}")
        continue

    clean_signature(
        source,
        source
    )

    print(f"FIXED: {filename}")


print()
print("TLC SIGNATURES CLEANED SUCCESSFULLY")
