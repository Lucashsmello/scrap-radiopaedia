from typing import Any
from .utils import extract_header
import scrapy
from ..items import CaseItem, ImageStudyItem

# https://radiopaedia.org/studies/27767/stacks


class CaseSpider(scrapy.Spider):
    name = "case"

    def start_requests(self):
        urls = [
            'https://radiopaedia.org/cases/scaphoid-fracture-undisplaced',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    @staticmethod
    def _extract_images_urls(div_usercontent_node) -> dict:
        data = {}
        # images_node = div_usercontent_node.xpath('.//div[@id="case-images"]')

        data['study_id'] = int(
            div_usercontent_node.xpath('.//div[contains(@class,"case-section case-study")]/@data-study-id').get()
        )
        data['study_stacks_url'] = div_usercontent_node.xpath(
            './/div[contains(@class,"case-section case-study")]/@data-study-stacks-url').get()

        return data

    @staticmethod
    def parse_case(response):
        data = {}

        # def cb_func_parse_image(img_response):
        #     image_items = list(ImageStudySpider.parse_imagestudy(img_response))
        #     images_ids = [img_i.id for img_i in image_items]
        #     data['images_ids'] = images_ids
        #     yield from image_items

        ### extract header info ###
        div_main = response.xpath('//div[@id="main"]')
        header_node = div_main.xpath('.//div[@id="content-header"]')
        header_data = extract_header(header_node)
        header_data['header_title'] = header_node.xpath('h1[@class="header-title"]/text()').get()
        header_data['diagnostic_certainty'] = header_node.xpath(
            './/span[@class="diagnostic-certainty-title"]/text()[normalize-space()]')[-1].get().rstrip('\xa0')
        ###########################

        div_usercontent_node = div_main.xpath('//div[@class="user-generated-content"]')

        ### Extract additional header_info ###
        header_data['presentation_text'] = div_usercontent_node.xpath(
            './/div[@id="case-patient-presentation"]/p/text()').get()
        ######################################

        data.update(CaseSpider._extract_images_urls(div_usercontent_node))
        data.update(header_data)

        yield response.follow(data['study_stacks_url'],
                              callback=ImageStudySpider.parse_imagestudy,
                              cb_kwargs={'case_study_id': data['study_id']}
                              )

        yield CaseItem(**data)

    def parse(self, response):
        yield from CaseSpider.parse_case(response)


class ImageStudySpider(scrapy.Spider):
    name = "image_study"

    start_urls = ['https://radiopaedia.org/studies/27767/stacks']

    @staticmethod
    def parse_imagestudy(response, case_study_id: int = None):
        for img_study in response.json():
            modality = img_study['modality']
            for imgobj in img_study['images']:
                imgobj['image_urls'] = [imgobj['public_filename']]
                if case_study_id is not None:
                    imgobj['case_study_id'] = case_study_id

                imgobj = {k: v for k, v in imgobj.items() if k in ImageStudyItem.__annotations__.keys()}

                yield ImageStudyItem(modality=modality, **imgobj)

    def parse(self, response):
        yield from ImageStudySpider.parse_imagestudy(response)
