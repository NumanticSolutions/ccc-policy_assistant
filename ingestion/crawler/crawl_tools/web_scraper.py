# © 2025 Numantic Solutions LLC
# MIT License
#

# Class for scraping websites
# Built using Pyppeteer

from pyppeteer import launch
from bs4 import BeautifulSoup
# import html2text
import urllib
import re

class webScraper:
    '''
    Class for scraping am individual website. Note that url is passed to the
    asynchronous visit_page method (see usage below) and (without errors) this
    method will return a dictionary with the raw html, a BeautifulSoup object, the
    text found in the HTML and the urls found in <a> tags.

    usage:
        turl = "https://en.wikipedia.org/wiki/Chaffey_College"
        test = await wc.webScraper.visit_page(url=turl)

        test.crawl_results.keys()
        dict_keys(['url', 'html_code_string', 'soup', 'soup_text', 'h2t_text', 'page_urls'])

    params:

    '''

    def __init__(self, crawl_results):
        '''
        Initialize class
        '''

        self.crawl_results = crawl_results

        # # Update any key word args
        # self.__dict__.update(kwargs)

    @classmethod
    async def visit_page(cls, url):
        '''
        Use Pyppeteeer to visit page and then return results in a dict
        :return:
        '''

        min_html_length = 100

        # Get HTML code from webpage
        html = await cls.collect_page_data(url=url)

        if len(html) < min_html_length:
            # Step 8: Create a class instance and return it
            instance = cls(crawl_results={})
            return instance

        else:

            ## Step 2: Load HTML Response Into BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            ## Step 3: Get the HTML code in a string
            html_code_string = str(soup)

            ## Step 4: Get text from p tags
            ptag_texts = []
            for p in soup.find_all('p'):
                ptag_texts.append(p.text)

            ## Step 4b: Create a single clean text column
            ptag_text = cls.clean_ptag_texts(ptag_texts=ptag_texts)

            # ## Step 5: Get the BeautifulSoup text
            # soup_text = soup.get_text()
            #
            # ## Step 6: Get the HTML2Text text
            # h = html2text.HTML2Text()
            # # Ignore converting links from HTML
            # h.ignore_links = True
            # h.body_width = 0
            # h2t_text = h.handle(html_code_string)

            ## Step 6: Return all links in <a tags with href values
            atag_urls = []
            for a in soup.find_all('a', href=True):
                atag_urls.append(a['href'])

            # Append the base url to href URLS to make them navigable - remove redundant URLs in the process
            atag_urls = [cls.get_full_url(purl=url, hurl=u) for u in atag_urls]
            atag_urls = set(atag_urls)

            # Step 7: Save results to a dictionary
            result = dict(url=url,
                        html_code_string=html_code_string,
                        soup=soup,
                        ptag_text=ptag_text,
                        atag_urls=atag_urls)

            # Step 8: Create a class instance and return it
            instance = cls(crawl_results=result)
            return instance

    @staticmethod
    async def collect_page_data(url):
        '''
        Asynch function to get page content
        :return:
        '''

        try:
            browser = await launch()
            page = await browser.newPage()
            await page.goto(url=url)

            ## Step 1: Get page content from Pyppeter
            html = await page.content()
            await browser.close()

        except:
            return {}

        return html

    @classmethod
    def get_full_url(self,
                     purl,
                     hurl):
        '''
        Method to get a navigable url from urls found in a tag reference. This method will
        concatenate the page url (purl) with href url (hurl) to create a URL that can be crawled.
        '''

        # First check in this is a navigable URL
        if hurl.find("http") >= 0:
            return hurl

        else:

            # Parse the page URL
            parsed_url = urllib.parse.urlparse(purl)

            # Construct a root URL
            root_url = "{}://{}{}".format(parsed_url.scheme, parsed_url.netloc, parsed_url.path)

            # Drop aspx references
            drop_pat = r"\/[^\/]+\.aspx"
            root_url = re.sub(drop_pat, "/", root_url)

            # Join root and href URL
            return urllib.parse.urljoin(root_url, hurl)

    @classmethod
    def clean_ptag_texts(self, ptag_texts: list):
        '''
        Method to clean the ptag text. This method takes a list of ptag texts and
        returns a single string of cleaned ptag texts joined together.
        '''

        # remove unwanted characters
        pat = r"\n|\xa0"
        ptag_text = " ".join(ptag_texts)
        ptag_text = re.sub(pat, " ", ptag_text)
        pat = "\\s+"
        ptag_text = re.sub(pat, " ", ptag_text)

        return ptag_text