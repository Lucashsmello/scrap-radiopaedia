# Scrapy settings for scrap_radiopaedia project

from .items import ImageStudyItem, CaseItem, ArticleItem, StudyItem

BOT_NAME = "scrap_radiopaedia"

SPIDER_MODULES = ["scrap_radiopaedia.spiders"]
NEWSPIDER_MODULE = "scrap_radiopaedia.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "scrap_radiopaedia (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 8

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0.1
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 8
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'scrap_radiopaedia.pipelines.MyImagesPipeline': 1,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 600
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

IMAGES_STORE = 'extracted_dataset/images/'


# https://docs.scrapy.org/en/latest/topics/feed-exports.html#topics-feed-exports
FEEDS_overwrite_option = True
FEEDS = {
    'extracted_dataset/cases.csv': {
        'format': 'csv',
        'item_classes': [CaseItem],
        'overwrite': FEEDS_overwrite_option
    },
    'extracted_dataset/images_info.csv': {
        'format': 'csv',
        'item_classes': [ImageStudyItem],
        'overwrite': FEEDS_overwrite_option
    },
    'extracted_dataset/studies.csv': {
        'format': 'csv',
        'item_classes': [StudyItem],
        'overwrite': FEEDS_overwrite_option
    }
}

# Logging
LOG_LEVEL = 'INFO'
# LOG_FILE = 'log.log'

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"


### Custom Settings ###

# Max cases pages to follow. None means no limit. 1 means that only a single page of cases will be scrapped.
CASESPIDER_MAXPAGES = 2

# Filter Cases with desired tags (case-insensitive). Multiple values means to include any case that has at least one of these value.
CASE_INCLUDE_TAGS = ['fracture']
# Set True to include Cases where there are no tags are available.
CASE_INCLUDE_NA_TAGS = True

# Filter Cases with desired systems (case-insensitive).
CASE_INCLUDE_SYSTEMS = ['musculoskeletal']
# Set True to include Cases where there are no systems are available.
CASE_INCLUDE_NA_SYSTEMS = True
