from typing import Any, Iterator, Union
from .utils import extract_header
import scrapy
from scrapy import http
from ..items import CaseItem, ImageStudyItem, StudyItem

# https://radiopaedia.org/studies/27767/stacks


class CaseSpider(scrapy.Spider):
    name = "case"

    def start_requests(self):
        urls = [
            # 'https://radiopaedia.org/cases/scaphoid-fracture-undisplaced',
            # 'https://radiopaedia.org/cases/scaphoid-fracture-13'
            # 'https://radiopaedia.org/cases/trans-scaphoid-perilunate-dislocation'
            'https://radiopaedia.org/cases'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    @staticmethod
    def extract_studies(response, div_usercontent_node) -> Iterator[Union[StudyItem, http.Request]]:
        case_study_node = div_usercontent_node.xpath('.//div[contains(@class,"case-section case-study")]')
        study_ids = [int(study_id) for study_id in case_study_node.xpath('@data-study-id').getall()]
        study_stacks_urls = case_study_node.xpath('@data-study-stacks-url').getall()
        assert all(str(x) in y for x, y in zip(study_ids, study_stacks_urls))
        # Images descriptions/findings
        img_study_descriptions = div_usercontent_node.xpath(
            './/div[contains(@class,"study-findings")]/p/text()').getall()
        img_study_descriptions = [s.rstrip('\xa0') for s in img_study_descriptions]

        for study_id, stacks_url, desc in zip(study_ids, study_stacks_urls, img_study_descriptions):
            yield response.follow(stacks_url,
                                  callback=ImageStudySpider.parse_imagestudy,
                                  cb_kwargs={'study_id': study_id}
                                  )
            yield StudyItem(id=study_id,
                            stacks_url=stacks_url,
                            description=desc)

    @staticmethod
    def parse_case(response):
        data = {}

        ### extract header info ###
        div_main = response.xpath('//div[@id="main"]')
        header_node = div_main.xpath('.//div[@id="content-header"]')
        header_data = extract_header(header_node)
        header_data['header_title'] = header_node.xpath('h1[@class="header-title"]/text()').get()
        header_data['diagnostic_certainty'] = header_node.xpath(
            './/span[@class="diagnostic-certainty-title"]/text()[normalize-space()]').get().rstrip('\xa0')
        ###########################

        div_usercontent_node = div_main.xpath('//div[@class="user-generated-content"]')

        ### Extract additional header_info ###
        header_data['presentation_text'] = div_usercontent_node.xpath(
            './/div[@id="case-patient-presentation"]/p/text()').get()
        ######################################

        studies_ids = []
        for item in CaseSpider.extract_studies(response, div_usercontent_node):
            if isinstance(item, StudyItem):
                studies_ids.append(item.id)
            yield item

        data.update(header_data)

        # TODO: scrap age and gender
        # TODO: scrap case-study questions

        yield CaseItem(studies_ids=studies_ids,
                       url=response.url,
                       **data)

    def parse(self, response: http.Request):
        url = response.url

        # Cases page
        if url.endswith('/cases') or url.endswith('/cases/') or '/cases?page=' in url:
            cases_hrefs = response.xpath('//a[@class="search-result search-result-case"]/@href').getall()

            for page_href in cases_hrefs:
                yield response.follow(page_href,
                                      callback=CaseSpider.parse_case
                                      )

            next_page_href = response.xpath('//div[@role="navigation"]//a[@class="next_page"]/@href').get()
            if next_page_href is not None:
                yield response.follow(next_page_href, callback=self.parse)

        yield from CaseSpider.parse_case(response)


class ImageStudySpider(scrapy.Spider):
    name = "image_study"

    start_urls = ['https://radiopaedia.org/studies/27767/stacks']

    @staticmethod
    def parse_imagestudy(response, study_id: int = None):
        for img_study in response.json():
            modality = img_study['modality']
            for imgobj in img_study['images']:
                imgobj['image_urls'] = [imgobj['public_filename']]
                if study_id is not None:
                    imgobj['study_id'] = study_id

                imgobj = {k: v for k, v in imgobj.items() if k in ImageStudyItem.__annotations__.keys()}

                yield ImageStudyItem(modality=modality, **imgobj)

    def parse(self, response):
        yield from ImageStudySpider.parse_imagestudy(response)
