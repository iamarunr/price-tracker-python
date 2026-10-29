# Price tracker (Python)

A small Python script that watches a product's price for you. Give it a product link and how often to check, and it prints whether the price **dropped**, **went up** or stayed **unchanged** since the last check. Every price is saved to `price_history.csv`.

I wrote it to watch the MacBook Pro I'd just bought from Micro Center. On day 14 the price dropped, and the store refunded me $459. The full story, and how to do this with an AI assistant instead, is on my blog: [How a price tracker got me $459 back on my MacBook Pro](https://knnaresh.com/blog/price-tracker-macbook/).

## How it works

It opens a normal Chrome window with [Playwright](https://playwright.dev/python/), because Micro Center blocks plain web requests. It reads the price from Micro Center's product data, or from the standard product data (JSON-LD) that many other stores publish. If the store shows a "Just a moment…" check, complete it in that window; the script waits up to two minutes for the product page.

## Set up

You need Python 3 and Google Chrome. Download this repository (**Code → Download ZIP**, or `git clone`), open a terminal in its folder, and run once:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python price_tracker.py
```

It asks for the product link and how many minutes between checks (60 by default). Stop it with Ctrl+C.

## Good to know

- **Keep your computer awake.** It only checks while the script is running.
- **Check the first price by eye.** A discontinued Micro Center listing can still carry an old hidden price, so the script skips products marked "no longer carried". Compare the first printed price with the one in the browser window.
- **It prints to the terminal.** For an email or phone notification, ask an AI assistant to add one.
- **Stores change their pages.** If it stops finding a price, the page has probably changed; the price-finding code is in `find_price`.

## Want more?

[price-tracker](https://github.com/iamarunr/price-tracker) is the fuller version: a dashboard with price history for many products, email alerts, and optional hosting on Cloudflare. It needs Node.js.

## License

MIT
