# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import json
import time
from collections import defaultdict

from loguru import logger
from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.project import get_project_settings
from scrapy.utils.response import response_status_message
from w3lib.http import basic_auth_header

from spiders.utils import reboot_mobile_proxy


class FlstockSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class FlstockDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class StatusMiddleware:
    def __init__(self):
        self.counter = defaultdict(lambda: defaultdict(int))
        self.response_count = 0

    def process_response(self, request, response, spider):
        content_type = response.headers.get("Content-Type", "").decode("utf-8")
        status = response.status
        self.counter[content_type][status] += 1

        if self.response_count % 50 == 0:
            logger.info(json.loads(json.dumps(self.counter)))

        self.response_count += 1

        return response


class MobileProxyMiddleware(RetryMiddleware):
    def __init__(self, _settings):
        settings = get_project_settings()
        creds, self.url = settings.get("PROXY_URL").split("@")
        self.ip, self.port = self.url.split(":")
        self.login, self.password = creds.split(":")
        self.max_retry_times = 10
        self.retry_http_codes = {403, 405, 502}
        self.retry_wait_time = 60
        super().__init__(_settings)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        request.meta["download_timeout"] = 60 * 5
        if request.meta.get("no_proxy"):
            return
        request.meta["proxy"] = f"http://{self.url}"
        request.headers["Proxy-Authorization"] = basic_auth_header(self.login, self.password)
        request.meta["ssl_certificate_validation"] = False

    def process_response(self, request, response, spider):
        if response.status in {*self.retry_http_codes, 403, 405, 502}:
            reason = response_status_message(response.status)
            time.sleep(60)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        return self._retry(request, str(exception), spider)

    def _retry(self, request, reason, spider):
        retries = request.meta.get("retry_times", 0) + 1

        if retries == 1:
            reboot_mobile_proxy()
            time.sleep(self.retry_wait_time)

        if retries <= self.max_retry_times:
            spider.logger.debug(f"Retrying {request.url} (failed {retries} times): {reason}")
            time.sleep(self.retry_wait_time)
            request.meta["retry_times"] = retries
            request.meta["ssl_certificate_validation"] = False
            request.dont_filter = True
            return request
        else:
            spider.logger.debug(f"Giving up {request.url} (failed {retries} times): {reason}")
            return None
