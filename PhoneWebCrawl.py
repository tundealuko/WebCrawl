"""
Created on Wed Dec 20 14:54:38 2017

@author: Tunde Aluko
"""
from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urllib.parse import urlsplit
from collections import deque
import re

webpage = input("Enter the static webpage to crawl phone number from: ")
new_urls = deque([str(webpage)])

processed_urls = set()

phoneNumbers = set()

while len(new_urls):
        # move next url from the queue to the set of processed urls
        url = new_urls.popleft()
        processed_urls.add(url)

        # extract base url to resolve relative links
        parts = urlsplit(url)
        base_url = "{0.scheme}://{0.netloc}".format(parts)
        path = url[:url.rfind('/') + 1] if '/' in parts.path else url

        # get url's content
        print("Processing %s" % url)
        try:
            response = requests.get(url)
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
            # ignore pages with errors
            continue

        # extract all phone number and add them into the resulting set
        new_phoneNumbers = set(
            re.findall(r"([0][8,7,9][1,0][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9])", response.text, re.I))
        phoneNumbers.update(new_phoneNumbers)

        # create a beautiful soup for the html document
        soup = BeautifulSoup(response.text)

        # find and process all the anchors in the document
        for anchor in soup.find_all("a"):
            # extract link url from the anchor
            link = anchor.attrs["href"] if "href" in anchor.attrs else ''
            # resolve relative links
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = path + link
            # add the new url to the queue if it was not enqueued nor processed yet
            if not link in new_urls and not link in processed_urls:
                new_urls.append(link)
        #save the result in a text file
        with open('phone_list.txt', 'w') as output:
            for phoneNumber in phoneNumbers:
                output.write(str(phoneNumber) + "\n")

