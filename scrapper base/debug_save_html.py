from playwright.sync_api import sync_playwright

def prueba_imdb():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.imdb.com/title/tt0062622/")
        page.wait_for_timeout(5000)

        html = page.content() # es lo que hace el DOM renderizado a HTML

        with open("imdb_2001.html", "w", encoding="utf-8") as f:
            f.write(html)

        print("HTML guardado en imdb_2001.html")
        browser.close()


if __name__ == "__main__":
    prueba_imdb()