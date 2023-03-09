from typing import Any, Iterator, Union, Optional, Sequence
from .utils import extract_header
import scrapy
from scrapy import http
from ..items import CaseItem, ImageStudyItem, StudyItem
from datetime import date, datetime
import logging

# https://radiopaedia.org/studies/27767/stacks

_LOGGER = logging.getLogger(__name__)


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
    def _filter_by_field(values_str: Optional[Sequence[str]],
                         include_values: Optional[Sequence[str]],
                         include_na: bool) -> bool:
        if values_str is None:
            return include_na == True

        if include_values is not None:
            tags = [t.strip().lower() for t in values_str]
            in_tags = [itag.lower() in tags for itag in include_values]
            if sum(in_tags) == 0:
                return False
        return True

    def _fix_header_data_types(header_data: dict) -> dict:
        keys_single = ['Case_published', 'Citation', 'DOI', 'Permalink', 'rID', 'Quiz_mode', 'Institution']

        for k in keys_single:
            if k in header_data:
                if isinstance(header_data[k], list):
                    assert len(header_data[k])
                    header_data[k] = header_data[k][0]

        return header_data

    @staticmethod
    def parse_case(response,
                   include_tags: Optional[Sequence[str]] = None,
                   include_na_tags: bool = False,
                   include_systems: Optional[str] = None,
                   include_na_systems: bool = False,
                   min_case_date: date = date(1970, 1, 1),
                   max_case_date: date = date(2200, 1, 1)
                   ) -> Iterator:
        data = {}

        ### extract header info ###
        div_main = response.xpath('//div[@id="main"]')
        header_node = div_main.xpath('.//div[@id="content-header"]')
        header_data = extract_header(header_node)
        header_data = CaseSpider._fix_header_data_types(header_data)

        if 'Tags' in header_data:
            if not CaseSpider._filter_by_field(header_data['Tags'], include_tags, include_na_tags):
                _LOGGER.info(f'Ignoring case "{response.url}" due to "Tags" name restrictions.')
                return

        if 'Systems' in header_data:
            if not CaseSpider._filter_by_field(header_data['Systems'], include_systems, include_na_systems):
                _LOGGER.info(f'Ignoring case "{response.url}" due to "Systems" name restrictions.')
                return

        case_published_date = datetime.strptime(header_data['Case_published'], '%d %b %Y').date()
        if case_published_date < min_case_date or case_published_date > max_case_date:
            _LOGGER.info(f'Ignoring case "{response.url}" due to "Case_published" date restrictions.')
            return

        header_data['header_title'] = header_node.xpath('h1[@class="header-title"]/text()').get()
        diagnostic_certainty = header_node.xpath(
            './/span[@class="diagnostic-certainty-title"]/text()[normalize-space()]').get()
        if diagnostic_certainty is not None:
            diagnostic_certainty = diagnostic_certainty.rstrip('\xa0')
            header_data['diagnostic_certainty'] = diagnostic_certainty
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

        cb_kwargs = {'include_systems': self.settings.getlist('CASE_INCLUDE_SYSTEMS'),
                     'include_tags': self.settings.getlist('CASE_INCLUDE_TAGS')
                     }
        cb_kwargs.update({'include_na_systems': self.settings.getbool('CASE_INCLUDE_NA_SYSTEMS',
                                                                      cb_kwargs['include_systems'] is None),
                          'include_na_tags': self.settings.getbool('CASE_INCLUDE_NA_TAGS',
                                                                   cb_kwargs['include_tags'] is None)
                          }
                         )

        min_date = self.settings.get('CASE_PUBLISHED_MIN_DATE')
        if min_date is not None:
            min_date = datetime.strptime(min_date, '%Y-%m-%d').date()
            cb_kwargs['min_case_date'] = min_date
        max_date = self.settings.get('CASE_PUBLISHED_MAX_DATE')
        if max_date is not None:
            min_date = datetime.strptime(max_date, '%Y-%m-%d').date()
            cb_kwargs['max_case_date'] = max_date

        # Cases page
        if url.endswith('/cases') or url.endswith('/cases/') or '/cases?' in url:
            if not hasattr(self, 'max_pages_to_read'):
                self.max_pages_to_read = self.settings.getint('CASESPIDER_MAXPAGES', 10000)
            cases_hrefs = response.xpath('//a[@class="search-result search-result-case"]/@href').getall()
            self.logger.info(f'Found {len(cases_hrefs)} Cases in this page.')

            for page_href in cases_hrefs:
                self.logger.info(f'Following Case {page_href}...')
                yield response.follow(page_href,
                                      callback=CaseSpider.parse_case,
                                      cb_kwargs=cb_kwargs
                                      )
            self.max_pages_to_read -= 1

            next_page_href = response.xpath('//div[@role="navigation"]//a[@class="next_page"]/@href').get()
            if next_page_href is not None:
                if self.max_pages_to_read > 0:
                    self.logger.info(f'Remaining Cases pages to read: {self.max_pages_to_read}')
                    self.logger.info(f'Following next Cases page ({next_page_href})')
                    yield response.follow(next_page_href, callback=self.parse)
                    self.max_pages_to_read -= 1
                else:
                    self.logger.info('Reached max number of Cases pages to read.')
        else:
            yield from CaseSpider.parse_case(response, **cb_kwargs)


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
