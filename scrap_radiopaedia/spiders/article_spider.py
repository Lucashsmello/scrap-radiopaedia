from pathlib import Path
from ..items import ArticleItem
from typing import Any
from .utils import extract_header

import scrapy


class ArticleSpider(scrapy.Spider):
    name = "article"

    def start_requests(self):
        urls = [
            'https://radiopaedia.org/articles/scaphoid-fracture',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def _extract_cases_hrefs(self, response) -> list[str]:
        imagegrid_node = response.xpath('//div[@id="main"]').xpath('.//div[@class="row image-grid"]')
        return imagegrid_node.xpath('.//a[starts-with(@href,"/cases/") and @class="thumbnail"]/@href').getall()

    def parse(self, response: scrapy.http.HtmlResponse):
        div_main = response.xpath('//div[@id="main"]')
        div_article_header = div_main.xpath('.//div[@id="article-header"]')
        header_data = extract_header(div_article_header)
        cases_hrefs = self._extract_cases_hrefs(response)

        yield ArticleItem(**header_data)

        # filename = f'quotes-{page}.html'
        # Path(filename).write_bytes(response.body)
        # self.log(f'Saved file {filename}')
