import scrapy
import re
from scraper.db import db
from scraper.items import CompanyItem
from scrapy.http import FormRequest

class AsicSpider(scrapy.Spider):
    name = 'asic'

    # get all previously seen notices
    cur = db.cursor()
    cur.execute('select acn from notices')
    acn_list = cur.fetchall()
    
    # fetchall returns list of tuple
    # turn into a list of values
    acn_list = [x[0] for x in acn_list]
    
    # previously seen notices
    seen = set(acn_list)
    
    def start_requests(self):
        URL = r"https://publishednotices.asic.gov.au/browsesearch-notices?appointment=Court%20Liquidation,Creditors%27%20Voluntary%20Liquidation,Members%27%20Voluntary%20Liquidation&noticestate=All&court=&district=&dnotice="
        yield scrapy.Request(url=URL, callback=self.response_parser)
        

    def response_parser(self, response):
        company_item = CompanyItem()
        
        # Extract page number from the href link in the pagination
        # we should find the number in the <td> IMMEDIATELY AFTER a <td> containing a <span>
        # because that is plaintext containing our current page
        js_postback_text = response.xpath('//tr[@class="NoticeTablePager"]//td[span]/following-sibling::td[1]/a/@href').get()
        
        # pattern is any string 'Page$[some number]'
        pattern = r"Page\$([^\']+)"

        # look for our pattern in the href pertaining to the next page to get 'Page$[next_page]'
        # next_page = None on the last page
        next_page = re.search(pattern, js_postback_text).group(0)

        # if hit last page
        if next_page is None:
            next_page = 'Page$First'

        # Get notices on current page
        for notice in response.css('div.article-block'):
            # get ACN and remove whitespace
            company_item['acn'] = notice.css('dl > dd::text').get().replace(' ', '')

            if (company_item['acn'] in self.acn_list):
                # hit an already seen notice -> return to front page
                next_page = 'Page$First'
                # dont yield item
                continue

            company_item['name'] = notice.css('p::text')[1].get()
            company_item['note_date'] = notice.css('div.published-date::text').getall()[1]
            yield company_item

        if (next_page == 'Page$First'):
            print("Polling first page")

        # pagination works via POST requests via a form
        # get the necessary data required to goto next page
        formdata = {
            '__EVENTTARGET': 'ctl00$ctl00$ctl00$ctl00$ContentPlaceHolderDefault$INWMasterContentPlaceHolder$INWPageContentPlaceHolder$ucNoticeResult$lvNoticeList',
            '__EVENTARGUMENT': next_page,
            '__VIEWSTATE': response.css('input[name=__VIEWSTATE]::attr("value")').get(),
            '__VIEWSTATEGENERATOR': response.css('input[name=__VIEWSTATEGENERATOR]::attr("value")').get(),
            '__EVENTVALIDATION': response.css('input[name=__EVENTVALIDATION]::attr("value")').get(),
            '__VIEWSTATEENCRYPTED': response.css('input[name=__VIEWSTATEENCRYPTED]::attr("value")').get(),
        }

        yield FormRequest.from_response(
            response,
            url=response.url,
            method="POST",
            formdata = formdata,
            callback = self.response_parser
        )