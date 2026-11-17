"""Build 2 local web app for Fernweh.

Serves a single-page form at http://localhost:8000. The browser posts trip
details + friend profiles to /plan-trip; this server calls OpenRouter (the
API key stays here, never sent to the browser) and returns 8 restaurants
and 8 activities as JSON for the page to render as cards.

Run: python3 app.py
Needs OPENROUTER_API_KEY and OPENROUTER_MODEL set in .env (see .env.example).
"""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

ENV_PATH = ".env"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
PORT = 8000
STATIC_FILE = os.path.join("static", "index.html")

CATEGORIES = [
    "fine dining", "wine bar", "cafe", "seafood", "tapas", "market",
    "walking tour", "museum", "viewpoint", "nightlife", "cooking class", "beach",
]

SYSTEM_PROMPT = """You are Fernweh, a virtual travel agent for friend groups. You are given \
trip details (destination, dates, group size, budget, vibe) and a short profile from each \
friend in the group (budget comfort, food preferences/restrictions, activity interests, \
energy level, dealbreakers).

The budget given is a TOTAL PER-PERSON amount for the whole trip, in USD, not including \
flights. It is not a per-meal or per-day amount. Every suggestion's cost_per_person must be \
a realistic amount that fits within that total per-person budget on its own — never suggest \
something whose cost per person alone would exceed the group's stated budget.

Suggest exactly 8 restaurants and 8 activities in the destination that fit the whole group, \
balancing everyone's profiles, not just one person's.

Every suggestion must also include a "category" field: exactly one of these 12 values, \
whichever best matches the suggestion: """ + ", ".join(CATEGORIES) + """. This is used to \
pick a representative stock photo, so choose the closest match even if imperfect.

Respond with ONLY a single JSON object, no markdown code fences, no commentary, matching \
exactly this shape:

{
  "restaurants": [
    {"name": "...", "price_level": "$ to $$$$", "why_fits": "one sentence referencing specific profile details", "cost_per_person": "...", "category": "one of the 12 categories above"},
    ... exactly 8 items
  ],
  "activities": [
    {"name": "...", "price_level": "$ to $$$$", "why_fits": "one sentence referencing specific profile details", "cost_per_person": "...", "category": "one of the 12 categories above"},
    ... exactly 8 items
  ]
}"""


def load_env(path):
    if not os.path.exists(path):
        raise SystemExit(
            f"No {path} file found. Run `cp .env.example .env` and add your "
            "OpenRouter API key first."
        )
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def strip_code_fence(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```$", "", text.strip())
    return text.strip()


def call_openrouter(api_key, model, user_content):
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def build_user_content(trip):
    lines = [
        f"Destination: {trip['destination']}",
        f"Dates: {trip['dates']}",
        f"Group size: {trip['group_size']}",
        f"Budget: ${trip['budget']} per person, total for the whole trip, "
        "not including flights",
        f"Vibe: {trip['vibe']}",
        "",
        "Friend profiles:",
    ]
    for i, profile in enumerate(trip["friends"], start=1):
        lines.append(f"Friend {i}: {profile}")
    return "\n".join(lines)


def add_maps_links(items, destination):
    for item in items:
        query = urllib.parse.quote(f"{item.get('name', '')} {destination}")
        item["maps_url"] = f"https://www.google.com/maps/search/?api=1&query={query}"
    return items


# Curated, verified-loadable Unsplash photos, one per category, used as
# representative stock images since the AI can't provide real place photos.
PHOTOS = {
    "fine dining": {
        "url": "https://images.unsplash.com/photo-1766832255363-c9f060ade8b0?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Tanja Tepavac",
        "credit_url": "https://unsplash.com/photos/elegant-dining-tables-set-in-a-cozy-restaurant-interior-jSH-7IjJVsQ",
    },
    "wine bar": {
        "url": "https://images.unsplash.com/photo-1761330439476-3d4abe0f7a53?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Caroline Badran",
        "credit_url": "https://unsplash.com/photos/shelving-unit-with-wine-bottles-and-glassware-QLIrD78v9_E",
    },
    "cafe": {
        "url": "https://images.unsplash.com/photo-1752756992329-961db6366376?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Haberdoedas",
        "credit_url": "https://unsplash.com/photos/a-cozy-coffee-shop-interior-with-a-menu-_yJXuiFdsPo",
    },
    "seafood": {
        "url": "https://images.unsplash.com/photo-1765100479761-2359e22fbe16?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Vitalii Kyktov",
        "credit_url": "https://unsplash.com/photos/a-platter-of-assorted-seafood-with-mussels-and-shrimp-2xd9c6jQhGs",
    },
    "tapas": {
        "url": "https://images.unsplash.com/photo-1781115650865-6e29104a7edd?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Paul",
        "credit_url": "https://unsplash.com/photos/delicious-spanish-pintxos-and-tapas-displayed-on-a-counter-I6VLaTNCs9I",
    },
    "market": {
        "url": "https://images.unsplash.com/photo-1761289731268-900eba5cf09f?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Bernd Dittrich",
        "credit_url": "https://unsplash.com/photos/colorful-spices-and-dried-goods-displayed-at-a-market-stall-hvgiElA441A",
    },
    "walking tour": {
        "url": "https://images.unsplash.com/photo-1680205415325-3ceebea06319?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Paulina Bargielska",
        "credit_url": "https://unsplash.com/photos/a-cobblestone-street-in-an-old-city-PJRgaZmckF0",
    },
    "museum": {
        "url": "https://images.unsplash.com/photo-1761403757058-e3c95b662a89?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Julia Taubitz",
        "credit_url": "https://unsplash.com/photos/modern-museum-interior-with-spiraling-ramps-and-atrium-BJnv18pmmBk",
    },
    "viewpoint": {
        "url": "https://images.unsplash.com/photo-1732494644033-fedc311f0442?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Kellen Riggin",
        "credit_url": "https://unsplash.com/photos/an-aerial-view-of-a-city-at-sunset-105M1xsnV4o",
    },
    "nightlife": {
        "url": "https://images.unsplash.com/photo-1771850081567-22d494c9aca8?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "ayumi kubo",
        "credit_url": "https://unsplash.com/photos/a-busy-city-street-at-night-with-neon-lights-mYtL05HFNG8",
    },
    "cooking class": {
        "url": "https://images.unsplash.com/photo-1638446081329-aa6003de5800?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Nita Payne",
        "credit_url": "https://unsplash.com/photos/4kymbla9ZIw",
    },
    "beach": {
        "url": "https://images.unsplash.com/photo-1746131272890-6f7f2678743c?fm=jpg&q=70&w=1200&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D",
        "credit_name": "Adam Juman",
        "credit_url": "https://unsplash.com/photos/beautiful-beach-with-turquoise-water-and-palm-trees-0JaiQiU5bgw",
    },
}


def add_photos(items, item_type):
    fallback = PHOTOS["cafe"] if item_type == "restaurant" else PHOTOS["viewpoint"]
    for item in items:
        category = str(item.get("category", "")).strip().lower()
        photo = PHOTOS.get(category, fallback)
        item["photo_url"] = photo["url"]
        item["photo_credit_name"] = photo["credit_name"]
        item["photo_credit_url"] = photo["credit_url"]
    return items


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(STATIC_FILE, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/plan-trip":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            trip = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Could not read the form data sent."})
            return

        required = ["destination", "dates", "group_size", "budget", "vibe", "friends"]
        missing = [k for k in required if not trip.get(k)]
        if missing:
            self._send_json(400, {"error": f"Missing fields: {', '.join(missing)}"})
            return

        friends = trip["friends"]
        if not isinstance(friends, list) or not (2 <= len(friends) <= 6):
            self._send_json(400, {"error": "Enter between 2 and 6 friend profiles."})
            return

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        model = os.environ.get("OPENROUTER_MODEL", "")
        if not api_key or api_key.startswith("sk-or-v1-replace"):
            self._send_json(500, {"error": "Server is missing a real OPENROUTER_API_KEY."})
            return
        if not model:
            self._send_json(500, {"error": "Server is missing OPENROUTER_MODEL."})
            return

        user_content = build_user_content(trip)

        try:
            result = call_openrouter(api_key, model, user_content)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            self._send_json(502, {"error": f"OpenRouter request failed ({e.code}): {detail}"})
            return
        except urllib.error.URLError as e:
            self._send_json(502, {"error": f"Could not reach OpenRouter: {e.reason}"})
            return

        usage = result.get("usage", {})
        print(
            f"Tokens in: {usage.get('prompt_tokens', 'unknown')} · "
            f"Tokens out: {usage.get('completion_tokens', 'unknown')}",
            flush=True,
        )

        content = result["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(strip_code_fence(content))
        except json.JSONDecodeError:
            print("Model did not return valid JSON:\n", content)
            self._send_json(
                502, {"error": "The model didn't return valid JSON. Try again."}
            )
            return

        parsed["restaurants"] = add_photos(
            add_maps_links(parsed.get("restaurants", []), trip["destination"]),
            "restaurant",
        )
        parsed["activities"] = add_photos(
            add_maps_links(parsed.get("activities", []), trip["destination"]),
            "activity",
        )

        self._send_json(200, parsed)

    def log_message(self, format, *args):
        pass


def main():
    load_env(ENV_PATH)
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"Fernweh running at http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
