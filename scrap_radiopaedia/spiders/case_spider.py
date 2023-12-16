from typing import Any, Iterator, Union, Optional, Sequence
from .utils import extract_header
import scrapy
from scrapy import http
from ..items import CaseItem, ImageStudyItem, StudyItem
from datetime import date, datetime
import logging
import json

# https://radiopaedia.org/studies/27767/stacks

_LOGGER = logging.getLogger(__name__)


class CaseSpider(scrapy.Spider):
    name = "case"

    def start_requests(self):
        maxpages = self.settings.get('CASESPIDER_MAXPAGES', 1)
        for i in range(1, maxpages+1):
            filter_modality = self.settings.get('CASESPIDER_PAGES_FILTER_MODALITY')
            if filter_modality is None:
                url = f'https://radiopaedia.org/search?lang=us&page={i}&scope=cases&sort=date_of_publication'
            else:
                url = f'https://radiopaedia.org/search?lang=us&modality={filter_modality}&page={i}&scope=cases&sort=date_of_publication'
            yield scrapy.Request(url=url, callback=self.parse)

    @staticmethod
    def extract_studies(response,
                        div_usercontent_node,
                        filter_img_modalities: Sequence[str] = None) -> Iterator[Union[StudyItem, http.Request]]:
        case_study_node = div_usercontent_node.xpath('.//div[contains(@class,"case-section case-study")]')
        # study_ids = [int(study_id) for study_id in case_study_node.xpath('@data-study-id').getall()]
        study_ids = [int(study_id.split('-')[-1])
                     for study_id in case_study_node.xpath('./div[@class="main-study-desc"]/@id').getall()]
        
        study_stacks_urls = [f'https://radiopaedia.org/studies/{study_id}/stacks' for study_id in study_ids]
        

        assert all(str(x) in y for x, y in zip(study_ids, study_stacks_urls))
        # Images descriptions/findings
        img_study_descriptions = [study.xpath('.//div[contains(@class,"study-findings")]//text()').getall()
                                  for study in case_study_node]
        img_study_descriptions = [''.join(desc).replace('\xa0', ' ')
                                  for desc in img_study_descriptions]

        # Study modality
        studies_modality = [x.xpath('.//div[@class="study-modality"]/span/text()').get() for x in case_study_node]

        assert len(studies_modality) == len(img_study_descriptions) and len(study_ids) == len(studies_modality), \
            f'studies_modality={studies_modality} | img_study_descriptions={img_study_descriptions} | study_ids={study_ids}'

        for study_id, stacks_url, desc, modality in zip(study_ids, study_stacks_urls, img_study_descriptions, studies_modality):
            yield response.follow(stacks_url,
                                  callback=ImageStudySpider.parse_imagestudy,
                                  cb_kwargs={'study_id': study_id,
                                             'filter_modalities': filter_img_modalities}
                                  )

            yield StudyItem(id=study_id,
                            stacks_url=stacks_url,
                            description=desc,
                            modality=modality)

    # @staticmethod
    # def extract_studies(response,
    #                     div_usercontent_node,
    #                     filter_img_modalities: Sequence[str] = None) -> Iterator[Union[StudyItem, http.Request]]:
    #     case_study_node = div_usercontent_node.xpath('.//div[contains(@class,"case-section case-study")]')
    #     # study_ids = [int(study_id) for study_id in case_study_node.xpath('@data-study-id').getall()]
    #     study_ids = [int(study_id.split('-')[-1])
    #                  for study_id in case_study_node.xpath('./div[@class="main-study-desc"]/@id').getall()]
    #     # Images descriptions/findings
    #     img_study_descriptions = [study.xpath('.//div[contains(@class,"study-findings")]//text()').getall()
    #                               for study in case_study_node]
    #     img_study_descriptions = [''.join(desc).replace('\xa0', ' ')
    #                               for desc in img_study_descriptions]

    #     study_datas = [json.loads(data)['study'] for data in case_study_node.xpath('.//div[@class="hidden data"]/text()').getall()]

    #     for study in study_datas:
    #         ImageStudySpider.parse_imagestudy(study, filter_img_modalities=filter_img_modalities)

    #         yield StudyItem(id=study_id,
    #                         stacks_url=stacks_url,
    #                         description=desc,
    #                         modality=modality)

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

    @staticmethod
    def _fix_header_data_types(header_data: dict) -> dict:
        keys_single = ['Case_published', 'Citation', 'DOI', 'Permalink', 'rID', 'Quiz_mode', 'Institution']

        for k in keys_single:
            if k in header_data:
                if isinstance(header_data[k], list):
                    assert len(header_data[k])
                    header_data[k] = header_data[k][0]

        return header_data

    @staticmethod
    def _extract_extra_header_info(div_usercontent_node) -> dict:
        data = {}
        data['presentation_text'] = div_usercontent_node.xpath('.//div[@id="case-patient-presentation"]/p/text()').get()

        # Extract Age and Gender:
        case_patient_data = div_usercontent_node.xpath('//div[@id="case-patient-data"]/div[@class="data-item"]')
        patient_data_names = case_patient_data.xpath('strong/text()[normalize-space()]').getall()
        patient_data_names = [name.rstrip(':') for name in patient_data_names]
        patient_data_values = case_patient_data.xpath('text()[normalize-space()]').getall()
        patient_data_values = [v.rstrip('\n').strip() for v in patient_data_values]
        data.update({name: value for name, value in zip(patient_data_names, patient_data_values)})

        return data

    @staticmethod
    def parse_case(response,
                   include_tags: Optional[Sequence[str]] = None,
                   include_na_tags: bool = False,
                   include_systems: Optional[Sequence[str]] = None,
                   include_na_systems: bool = False,
                   min_case_date: date = date(1970, 1, 1),
                   max_case_date: date = date(2200, 1, 1),
                   filter_img_modalities: Optional[Sequence[str]] = None
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

        # Extract additional header_info
        extra_header_data = CaseSpider._extract_extra_header_info(div_usercontent_node)
        header_data.update(extra_header_data)

        studies_ids = []
        for item in CaseSpider.extract_studies(response,
                                               div_usercontent_node,
                                               filter_img_modalities=filter_img_modalities):
            if isinstance(item, StudyItem):
                studies_ids.append(item.id)
            yield item

        data.update(header_data)

        # TODO: scrap case-study questions

        yield CaseItem(studies_ids=studies_ids,
                       url=response.url,
                       **data)

    def _get_parse_case_settings(self) -> dict:
        cb_kwargs = {'include_systems': self.settings.getlist('CASE_INCLUDE_SYSTEMS'),
                     'include_tags': self.settings.getlist('CASE_INCLUDE_TAGS')
                     }
        cb_kwargs = {k: None if (v is None or len(v) == 0) else v for k, v in cb_kwargs.items()}
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
            max_date = datetime.strptime(max_date, '%Y-%m-%d').date()
            cb_kwargs['max_case_date'] = max_date

        cb_kwargs['filter_img_modalities'] = self.settings.get('IMAGE_MODALITIES')

        return cb_kwargs

    def parse(self, response: http.Request):
        cb_kwargs = self._get_parse_case_settings()

        # Cases page
        cases_hrefs = response.xpath('//a[@class="search-result search-result-case"]/@href').getall()
        self.logger.info(f'Found {len(cases_hrefs)} Cases in this page.')

        for page_href in cases_hrefs:
            self.logger.info(f'Following Case {page_href}...')
            yield response.follow(page_href,
                                  callback=CaseSpider.parse_case,
                                  cb_kwargs=cb_kwargs
                                  )


class ImageStudySpider(scrapy.Spider):
    name = "image_study"

    start_urls = ['https://radiopaedia.org/studies/27767/stacks']

    # @staticmethod
    # def parse_imagestudy(study:dict,
    #                      filter_modalities: Sequence[str] = None):
    #     modality = study['modality']
    #     if filter_modalities is not None and modality.lower() not in filter_modalities:
    #         return
    #     for imgobj in study['series']:
    #         imgdata = {'modality': modality,
    #                    'id': imgobj['id'],
    #                    'fullscreen_filename': None,
    #                    'public_filename': None,
    #                    'plane_projection':imgobj['perspective'],
    #                    'aux_modality': None,

    #                    }

    @staticmethod
    def parse_imagestudy(response,
                         study_id: int = None,
                         filter_modalities: Sequence[str] = None):
        for img_study in response.json():
            modality = img_study['modality']
            if filter_modalities is not None and modality.lower() not in filter_modalities:
                continue
            for imgobj in img_study['images']:
                imgobj['image_urls'] = [imgobj['public_filename']]
                if study_id is not None:
                    imgobj['study_id'] = study_id

                imgobj = {k: v for k, v in imgobj.items() if k in ImageStudyItem.__annotations__.keys()}

                yield ImageStudyItem(modality=modality, **imgobj)

    def parse(self, response):
        yield from ImageStudySpider.parse_imagestudy(response,
                                                     filter_modalities=self.settings.get('IMAGE_MODALITIES'))
