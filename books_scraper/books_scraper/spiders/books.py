import scrapy


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]

    # 📌 EXACT START URL SETTING:
    start_urls = ["https://books.toscrape.com/catalogue/page-1.html"]

    RATING_MAP = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }

    def parse(self, response):
        """
        Step 1: Inspect incoming landing payload structure and track selectors.
        """
        # 🔍 ADDED TEMPORARY DEBUG LOGS AS REQUESTED:
        self.logger.info(f"Title: {response.css('title::text').get()}")
        self.logger.info(f"HTML preview: {response.text[:1000]}")

        # Extract book listing relative endpoints
        book_links = response.css("article.product_pod h3 a::attr(href)").getall()
        self.logger.info(f"Books found on current page layer: {len(book_links)}")

        for link in book_links:
            yield response.follow(link, callback=self.parse_book_details)

        # Handle forward structural pagination routing
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_book_details(self, response):
        """
        Step 2: Collect book technical details, stock, pricing, and specs.
        """

        def get_table_value(label):
            return response.xpath(f"//th[text()='{label}']/following-sibling::td/text()").get()

        rating_classes = response.css("p.star-rating::attr(class)").get("").split()
        text_rating = next((cls for cls in rating_classes if cls != "star-rating"), None)
        rating = self.RATING_MAP.get(text_rating, 0)

        stock_text = response.css("p.availability::text").getall()
        stock_cleaned = "".join(stock_text).strip()
        amount_in_stock = int("".join(filter(str.isdigit, stock_cleaned))) if any(
            c.isdigit() for c in stock_cleaned) else 0

        yield {
            "title": response.css("div.product_main h1::text").get(),
            "price": response.css("p.price_color::text").get(),
            "amount_in_stock": amount_in_stock,
            "rating": rating,
            "category": response.css("ul.breadcrumb li:nth-last-child(2) a::text").get(),
            "description": response.css("#product_description + p::text").get(),
            "upc": get_table_value("UPC"),
        }
