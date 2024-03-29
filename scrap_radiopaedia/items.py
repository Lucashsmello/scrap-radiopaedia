# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

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
    case_ids: list[int]


@dataclass
class CaseItem:
    header_title: str
    url: str
    Citation: str
    DOI: str
    Permalink: str
    rID: int
    Case_published: str
    Revisions: str
    studies_ids: list[int]
    presentation_text: str
    Age: str = None
    Gender: str = None
    Race: str = None
    diagnostic_certainty: str = None
    Institution: str = None
    Quiz_mode: str = None
    Tags: list[str] = None
    Disclosures: str = None
    Systems: list[str] = None
    Case_of_the_day: str = None


@dataclass
class StudyItem:
    id: int
    stacks_url: str
    description: str = None
    modality: str = None


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
    image_urls: list[str]
    images = None
    study_id: int = None
    # show_feature: False,
    # show_pin: False,
    # show_case_key_image: False,
    # show_stack_key_image: False,
