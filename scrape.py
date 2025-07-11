import os
import requests
import smtplib
import ssl
import datetime as dt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import anthropic
import json
from dotenv import load_dotenv
load_dotenv()

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

def ask_llm(menu_data):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Convert JSON to readable text format
    menu_text = ""
    for item in menu_data:
        menu_text += f"• {item['dish']} - {item['station']} - {item['price']}\n"
        if item['description']:
            menu_text += f"  Description: {item['description']}\n"
        menu_text += f"  Location: {item['url']}\n\n"

    prompt = (
        "You are a nutrition coach helping someone who is cutting (trying to reduce body fat while maintaining muscle). Select for high-protein meals that are under 700 calories."
        "Given the following list of menu items, your task is to:\n\n"
        "1. Identify the **top 5 meals** that are best suited for cutting.\n"
        "2. For each recommended dish, estimate **total calories**, **protein content**, and explain why it's a good choice (e.g., lean protein, minimal fat, no cream, controllable portions, etc.).\n"
        "3. Flag any high-protein meals that are **only good with modifications** (e.g., 'ask for half rice', 'skip sauce', etc.).\n"
        "4. Clearly **avoid meals with beef or pork**, and avoid recommending anything overly high in carbs/fat (e.g., creamy pastas, fried food, heavy sauces).\n"
        "5. Bonus: Provide any strong **meal combos** that stay within ~500–700 kcal and 35–45g protein, and that are available from a single menu if possible.\n\n"
        "MENU OPTIONS:\n"
        f"{menu_text}"
        "Format your response with clear headings for each recommendation and include the location URL for each dish."
    )

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=5000,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}]
    )

    print(response.content[0].text.strip())
    return response.content[0].text.strip()

def send_email(recommendations):
    """Send the menu recommendations via email"""
    
    # Email configuration from environment variables
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")  # Use App Password for Gmail
    receiver_email = os.getenv("RECEIVER_EMAIL")
    
    if not all([sender_email, sender_password, receiver_email]):
        print("Missing email configuration. Set SENDER_EMAIL, SENDER_PASSWORD, and RECEIVER_EMAIL environment variables.")
        return False
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Daily Menu Recommendations - {dt.date.today().strftime('%B %d, %Y')}"
    message["From"] = sender_email
    message["To"] = receiver_email
    
    # Create HTML email body
    html_body = f"""
    <html>
      <body>
        <h2>🍽️ Daily Menu Recommendations for Cutting</h2>
        <p><strong>Date:</strong> {dt.date.today().strftime('%A, %B %d, %Y')}</p>
        <div style="white-space: pre-wrap; font-family: Arial, sans-serif; line-height: 1.6;">
{recommendations}
        </div>
        <hr>
        <p><small>Generated automatically from Amazon Lab 126 cafeterias</small></p>
      </body>
    </html>
    """
    
    # Create plain text version
    text_body = f"""
Daily Menu Recommendations for Cutting
Date: {dt.date.today().strftime('%A, %B %d, %Y')}

{recommendations}

---
Generated automatically from Amazon Lab 126 cafeterias
    """
    
    # Attach parts
    part1 = MIMEText(text_body, "plain")
    part2 = MIMEText(html_body, "html")
    message.attach(part1)
    message.attach(part2)
    
    try:
        # Create secure connection and send email
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        
        print(f"✅ Email sent successfully to {receiver_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"🕒 Running menu scraper at {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        raw_menu = scrape()
        if not raw_menu:
            print("❌ No menu items found")
            exit(1)
            
        print(f"✅ Found {len(raw_menu)} menu items")
        recs = ask_llm(raw_menu)
        
        # Send email with recommendations
        email_sent = send_email(recs)
        
        if email_sent:
            print("🎉 Menu recommendations sent successfully!")
        else:
            print("⚠️ Failed to send email, but recommendations were generated")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)
