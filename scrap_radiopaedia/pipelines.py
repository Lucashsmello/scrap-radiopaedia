# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from .items import ImageStudyItem
import logging

LOGGER = logging.getLogger(__name__)


class ScrapRadiopaediaPipeline:
    def process_item(self, item, spider):
        return item


class MyImagesPipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None, *, item: ImageStudyItem = None):
        study_id = int(request.url.split('/')[-2])
        if study_id != item.id:
            LOGGER.warning(f'study_id inconsistent for item: {item}')
        image_filename = f'{item.id}.{item.content_type.split("/")[1]}'

        return image_filename
