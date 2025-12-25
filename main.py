import asyncio
import json
import os
import re
import requests
from io import BytesIO
from PIL import Image
from playwright.async_api import async_playwright

with open("links.txt", "r") as f:
    PRODUCT_URLS = [line.strip() for line in f if line.strip()]
EXISTING = {}

if os.path.exists("products.json"):
    with open("products.json", "r", encoding="utf-8") as f:
        for p in json.load(f):
            EXISTING[p["title"]] = p


BASE_IMAGE_DIR = "productimages"
os.makedirs(BASE_IMAGE_DIR, exist_ok=True)

def detect_category(title):
   
    t = title.lower()
    if "fan" in t:
        return "fan"
    if "cooler" in t:
        return "cooler"
    if "heater" in t:
        return "heater"
    if "iron" in t:
        return "iron"
    return "other"
def is_valid_image(img):
    w, h = img.size
    return w >= 600 and h >= 600

def clean_name(text):
    return re.sub(r"[^a-zA-Z0-9]", "_", text)[:40]

def upgrade_resolution(url):
    if not url:
        return None
    return (
        url.replace("/128/128/", "/832/832/")
           .replace("/312/312/", "/832/832/")
           .replace("/416/416/", "/832/832/")
    )

def download_and_compress(url, path, seen_hashes):
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return False

        img = Image.open(BytesIO(r.content)).convert("RGB")

        # Reject tiny / thumbnail images
        if not is_valid_image(img):
            return False

        # Deduplicate by content
        img_hash = hash(img.tobytes())
        if img_hash in seen_hashes:
            return False
        seen_hashes.add(img_hash)

        img.save(path, "JPEG", quality=95, subsampling=0)
        return True

    except:
        return False


async def scrape():
    products = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in PRODUCT_URLS:
            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_timeout(4000)

                title = await page.locator("h1").inner_text()
                category = detect_category(title)

                desc = ""
                if await page.locator("._1mXcCf").count():
                    desc = await page.locator("._1mXcCf").inner_text()

                category_dir = os.path.join(BASE_IMAGE_DIR, category)
                os.makedirs(category_dir, exist_ok=True)

                raw_urls = set()
                imgs = await page.locator("img").all()

                for img in imgs:
                    src = await img.get_attribute("src")
                    data_src = await img.get_attribute("data-src")
                    srcset = await img.get_attribute("srcset")

                    for u in [src, data_src]:
                        if u and "rukminim" in u:
                            raw_urls.add(upgrade_resolution(u))

                    if srcset:
                        parts = srcset.split(",")
                        raw_urls.add(upgrade_resolution(parts[-1].split()[0]))

                saved_images = []
                seen_hashes = set()

                base = clean_name(title)

                for i, img_url in enumerate(raw_urls):
                    img_path = f"{category_dir}/{base}_{i}.jpg"
                    success = download_and_compress(img_url, img_path, seen_hashes)

                    if success:
                        saved_images.append(img_path)

                if not saved_images:
                    print(f"⚠ No images saved for {title}")
                    continue

                products.append({
                    "title": title,
                    "category": category,
                    "description": desc,
                    "images": saved_images
                })

                print(f"✔ {title} ({len(saved_images)} images)")
                # Reject products with less than 2 real images
                if len(saved_images) < 2:
                    print(f"⚠ Skipped product due to insufficient images: {title}")
                    continue

            except Exception as e:
                print(f"✖ Failed: {url}\n{e}")

        await browser.close()

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)


asyncio.run(scrape())
