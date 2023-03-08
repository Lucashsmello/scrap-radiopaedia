from pathlib import Path
from ..items import ArticleItem
from typing import Any, Iterator
from .utils import extract_header
from .case_spider import CaseSpider

import scrapy
from scrapy import http


class ArticleSpider(scrapy.Spider):
    name = "article"

    def start_requests(self):
        urls = [
            'https://radiopaedia.org/articles/scaphoid-fracture',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def _extract_cases(self, response) -> Iterator[http.Request]:
        imagegrid_node = response.xpath('//div[@id="main"]').xpath('.//div[@class="row image-grid"]')
        case_thumbnail_node = imagegrid_node.xpath('.//a[starts-with(@href,"/cases/") and @class="thumbnail"]/')
        cases_hrefs = case_thumbnail_node.xpath('@href').getall()
        cases_ids = case_thumbnail_node.xpath('@data-presentation-path').re('/cases/(\d+)/stud')
        cases_ids = [int(cid) for cid in cases_ids]

        for href in cases_hrefs:
            yield response.follow(href,
                                  callback=CaseSpider.parse_case,
                                  )

        self.case_ids = cases_ids

    def parse(self, response: scrapy.http.HtmlResponse):
        div_main = response.xpath('//div[@id="main"]')
        div_article_header = div_main.xpath('.//div[@id="article-header"]')
        header_data = extract_header(div_article_header)
        yield from self._extract_cases_hrefs(response)

        yield ArticleItem(case_ids=self.case_ids, **header_data)

        # self.log(f'Saved file {filename}')
