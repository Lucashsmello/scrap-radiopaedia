# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from dataclasses import dataclass
from typing import Optional


@dataclass
class ArticleItem:
    Citation: str
    DOI: str
    Permalink: str
    rID: int
    Article_created: str
    Disclosures: str
    Last_revised: str
    Revisions: str
    Systems: list[str]
    Tags: list[str]
    Synonyms: list[str]


@dataclass
class CaseItem:
    header_title: str
    Citation: str
    DOI: str
    Permalink: str
    rID: int
    Disclosures: str
    Case_published: str
    Disclosures: str
    Revisions: str
    Systems: list[str]
    Tags: list[str]
    Quiz_mode: str
    diagnostic_certainty: str
    study_id: int
    presentation_text: str
    study_stacks_url: str
    images_ids: list[int] = None


@dataclass
class ImageStudyItem:
    modality: str
    id: int
    fullscreen_filename: str
    public_filename: str
    plane_projection: str
    aux_modality: Optional[str]
    position: int
    content_type: str
    width: int
    height: int
    download_image_url: str
    crop_pending: bool
    image_urls: str
    images = None
    case_study_id: int = None
    # show_feature: False,
    # show_pin: False,
    # show_case_key_image: False,
    # show_stack_key_image: False,
