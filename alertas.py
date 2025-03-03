# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "feedparser",
#     "shapely",
#     "requests",
# ]
# ///
import re
import argparse
import feedparser
import requests
import time
import shapely.geometry


def get_alerts(feed_url):
    feed = feedparser.parse(feed_url)
    alerts = []
    for entry in feed.entries:
        alert = {
            "title": entry.title,
            "summary": entry.summary,
            "link": entry.link,
            "description": entry.description,
            "coords": entry.where.coordinates[0],
        }
        alerts.append(alert)
    return alerts


def strip_tags(html):
    value = " ".join(html.split())
    pattern = re.compile('<.*?>')
    return re.sub(pattern, "", value)


def notify(topic, alert):
    title = strip_tags(alert["title"])
    summary = strip_tags(alert["summary"])
    print(f"Notify alert: {title}")
    requests.post("https://ntfy.sh", json={
        "topic": topic,
        "title": title,
        "message": summary,
        "click": "https://smn.gob.ar/alertas",
        "priority": 4,
        "tags": ["cloud_with_lightning"]
    })


def is_within_polygon(alert, user_location) -> bool:
    coords = alert["coords"]

    if not coords:
        return False

    try:
        coords.append(coords[0])
        polygon = shapely.geometry.Polygon(coords)
        point = shapely.geometry.Point(user_location)
        return polygon.contains(point)
    except Exception as e:
        print(f"Error processing polygon: {e}")
        return False


def main(args):
    FEED_URL = "https://ssl.smn.gob.ar/feeds/avisocorto_GeoRSS.xml"
    seen_alerts = set()
    coords = (args.lon, args.lat)

    while True:
        alerts = get_alerts(FEED_URL)
        for alert in alerts:
            if alert["title"] not in seen_alerts and is_within_polygon(alert, coords):
                notify(args.topic, alert)
                seen_alerts.add(alert["title"])
        time.sleep(args.interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("-t", "--topic", required=True)
    parser.add_argument("-i", "--interval", type=int, help="interval (secs)", default=300)
    args = parser.parse_args()
    main(args)
