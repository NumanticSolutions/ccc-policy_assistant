# © 2025 Numantic Solutions LLC
# MIT License
#
# Class for scraping websites

import os, sys
import requests
from bs4 import BeautifulSoup
import urllib
import re

utils_path = "/Users/stephengodfrey/Documents/Workbench/Numantic/utilities/.."
sys.path.insert(0, utils_path)
import utilities.text_cleaning.text_cleaning_tools as tct

class webScraper:
    '''
    Class for scraping am individual website. Note that url is passed to the
    asynchronous visit_page method (see usage below) and (without errors) this
    method will return a dictionary with the raw html, a BeautifulSoup object, the
    text found in the HTML and the urls found in <a> tags.

    usage:
        turl = "https://en.wikipedia.org/wiki/Chaffey_College"
        test = await wc.webScraper.visit_page(url=turl)

        test.result.keys()
        dict_keys(['url', 'html_code_string', 'soup', 'soup_text', 'h2t_text', 'page_urls'])

    params:

    '''

    def __init__(self, **kwargs):
        '''
        Initialize class
        '''

        # Scraper parameters
        self.user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
        self.headers = {"User-Agent": self.user_agent}
        self.min_html_length = 100
        self.timeout = 10

        # Update any key word args
        self.__dict__.update(kwargs)

    def visit_page(self, url):
        '''
        Use Requests to visit page and then return results in a dict
        :return:
        '''

        ## Step 0.5: Set the result to empty
        self.result = {}

        # Step 1: Fetch URL data
        try:
            response = requests.get(url=url,
                                    headers=self.headers,
                                    timeout=self.timeout,
                                    verify=False
                                    )
            self.status_code = response.status_code
            self.content = response.content

            # URL data was returned
            if response.status_code == 200 and len(response.text) >= self.min_html_length:

                ## Step 2: Load HTML Response Into BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")

                ## Step 3: Get the HTML code in a string
                html_code_string = str(soup)

                ## Step 3b: Get meta data
                page_title = ""
                site_name = ""
                description = ""
                for tag in soup.find_all("meta"):
                    if tag.get("property", "") == "og:title":
                        page_title = tag.get("content", "")
                    elif tag.get("property", "") == "og:site_name":
                        site_name = tag.get("content", "")
                    elif tag.get("description", "") == "og:description":
                        description = tag.get("content", "")

                ## Step 4: Get text from p tags
                ptag_texts = []
                for p in soup.find_all('p'):
                    ptag_texts.append(p.text)

                ## Step 4a: Create a single clean text column
                ptag_text = tct.clean_web_texts(web_texts=ptag_texts)

                ## Step 4b. Get the text from tags
                divtag_texts = []
                for p in soup.find_all('div'):
                    divtag_texts.append(p.text)

                ## Step 4c: Create a single clean text column
                divtag_text = tct.clean_web_texts(web_texts=divtag_texts)

                ## Step 5: Get the BeautifulSoup text
                # page_text = tct.clean_web_texts(web_texts=[soup.get_text()])

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
                atag_urls = [self.get_full_url(purl=url, hurl=u) for u in atag_urls]
                atag_urls = set(atag_urls)

                # Step 7: Save results to a dictionary
                self.result = dict(url=url,
                                   site_name=site_name,
                                   page_title=page_title,
                                   description=description,
                                   html_code_string=html_code_string,
                                   soup=soup,
                                   ptag_text=ptag_text,
                                   divtag_text=divtag_text,
                                   atag_urls=atag_urls
                                   )

        except requests.exceptions.Timeout:
            print(f"Request timed out for URL: {url}")


        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch URL: {url} with error: {e}")

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
