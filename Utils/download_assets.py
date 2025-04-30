import os
import requests

# Mapping of asset URL to local file path.
assets = {
    # CSS assets
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css": "assets/vendor/bootstrap/css/bootstrap.min.css",
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css": "assets/vendor/bootstrap-icons/bootstrap-icons.css",
    "https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.css": "assets/vendor/aos/aos.css",
    "https://cdn.jsdelivr.net/npm/glightbox/dist/css/glightbox.min.css": "assets/vendor/glightbox/css/glightbox.min.css",
    "https://cdn.jsdelivr.net/npm/swiper@9/swiper-bundle.min.css": "assets/vendor/swiper/swiper-bundle.min.css",
    # JS assets
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js": "assets/vendor/bootstrap/js/bootstrap.bundle.min.js",
    "https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.js": "assets/vendor/aos/aos.js",
    "https://cdn.jsdelivr.net/npm/glightbox/dist/js/glightbox.min.js": "assets/vendor/glightbox/js/glightbox.min.js",
    "https://cdn.jsdelivr.net/npm/purecounterjs@1.5.0/dist/purecounter_vanilla.js": "assets/vendor/purecounter/purecounter_vanilla.js",
    "https://cdn.jsdelivr.net/npm/swiper@9/swiper-bundle.min.js": "assets/vendor/swiper/swiper-bundle.min.js",
    "https://unpkg.com/imagesloaded@5/imagesloaded.pkgd.min.js": "assets/vendor/imagesloaded/imagesloaded.pkgd.min.js",
    "https://unpkg.com/isotope-layout@3/dist/isotope.pkgd.min.js": "assets/vendor/isotope-layout/isotope.pkgd.min.js",
    # Placeholder assets for images
    "https://via.placeholder.com/32": "assets/img/favicon.png",
    "https://via.placeholder.com/180": "assets/img/apple-touch-icon.png",
    # Placeholder main CSS and JS files (empty files as placeholder)
    "": "assets/css/main.css",
    "": "assets/js/main.js",
    "https://cdn.jsdelivr.net/npm/php-email-form@3.1.0/validate.js": "assets/vendor/php-email-form/validate.js",
    "https://cdn.jsdelivr.net/npm/purecounterjs@1.5.0/dist/purecounter_vanilla.js": "assets/vendor/purecounter/purecounter_vanilla.js",
"https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/fonts/bootstrap-icons.woff2": "assets/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2",
"https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/fonts/bootstrap-icons.woff": "assets/vendor/bootstrap-icons/fonts/bootstrap-icons.woff",

}

def download_file(url, path):
    # If URL is empty, create an empty placeholder file.
    if not url:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("/* Empty file as placeholder */")
        print(f"Created placeholder file {path}")
        return
    print(f"Downloading {url} to {path}...")
    response = requests.get(url)
    response.raise_for_status()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded {path}")

if __name__ == "__main__":
    for url, path in assets.items():
        try:
            download_file(url, path)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
