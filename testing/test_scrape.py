import requests
from bs4 import BeautifulSoup

URLS = [
    "https://amazonlab126.cafebonappetit.com/cafe/sjc31-cafe/",
    "https://amazonlab126.cafebonappetit.com/cafe/midway-cafe-sjc-32/",
    "https://amazonlab126.cafebonappetit.com/cafe/lab-luxe/",
    "https://amazonlab126.cafebonappetit.com/cafe/lab-126-cafe/"
]

def scrape():
    all_items = []

    for url in URLS:
        print(f"Scraping: {url}")
        html = requests.get(url, timeout=15).text
        soup = BeautifulSoup(html, "html.parser")
        lunch_section = soup.find("section", id="lunch")
        if not lunch_section:
            continue

        stations = lunch_section.select("div.station-title-inline-block")
        for station in stations:
            station_title_tag = station.select_one(".site-panel__daypart-station-title")
            station_title = station_title_tag.get_text(strip=True) if station_title_tag else "Unknown Station"

            for item in station.select(".site-panel__daypart-item"):
                title_tag = item.select_one(".site-panel__daypart-item-title")
                desc_tag = item.select_one(".site-panel__daypart-item-description")
                price_tag = item.select_one(".price-item .price-item__amount")

                title = title_tag.get_text(" ", strip=True) if title_tag else ""
                desc = desc_tag.get_text(" ", strip=True) if desc_tag else ""
                price = price_tag.get_text(strip=True) if price_tag else "?"

                all_items.append({
                    "url": url,
                    "station": station_title,
                    "dish": title,
                    "price": price,
                    "description": desc
                })

    return all_items

if __name__ == "__main__":
    raw_text = scrape()
    print("\n=== Scraped Text ===\n")
    print(raw_text[:2000])  # Print first 2000 characters to avoid overload
