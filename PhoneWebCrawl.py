#!/usr/bin/env python3
"""
Modern Web Crawler for Phone Number Extraction
Improved version with better phone number detection, error handling, and performance
"""

import re
from urllib.parse import urljoin, urlparse, urlsplit
from collections import deque
import requests
from bs4 import BeautifulSoup
import logging
from typing import Set, Deque
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)

class PhoneNumberCrawler:
    def __init__(self, start_url: str, max_pages: int = 100):
        self.start_url = start_url
        self.max_pages = max_pages
        self.processed_urls: Set[str] = set()
        self.phone_numbers: Set[str] = set()
        self.url_queue: Deque[str] = deque([start_url])
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # More comprehensive phone number regex patterns
        self.phone_patterns = [
            r'\b0[789][01]\d{8}\b',  # Nigerian numbers (070, 080, 090) followed by 1/0
            r'\b\+234[789][01]\d{8}\b',  # Nigerian numbers with country code
        ]

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and should be crawled"""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        if parsed.scheme not in ('http', 'https'):
            return False
        # Add any domain restrictions if needed
        return True

    def normalize_phone_number(self, phone: str) -> str:
        """Standardize phone number format"""
        # Remove all non-digit characters
        digits = re.sub(r'[^\d+]', '', phone)
        
        # Convert Nigerian numbers to standard format
        if digits.startswith('234') and len(digits) == 13:
            return '0' + digits[3:]  # +2348012345678 -> 08012345678
        if digits.startswith('+234') and len(digits) == 14:
            return '0' + digits[4:]  # +2348012345678 -> 08012345678
            
        return digits

    def extract_phone_numbers(self, text: str) -> Set[str]:
        """Find all phone numbers in text using multiple patterns"""
        found_numbers = set()
        
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                normalized = self.normalize_phone_number(match)
                if len(normalized) >= 10:  # Basic validation
                    found_numbers.add(normalized)
        
        return found_numbers

    def crawl(self):
        """Main crawling method"""
        processed_count = 0
        
        while self.url_queue and processed_count < self.max_pages:
            url = self.url_queue.popleft()
            
            try:
                # Skip if already processed
                if url in self.processed_urls:
                    continue
                    
                logging.info(f"Processing #{processed_count + 1}: {url}")
                
                # Respect robots.txt and crawl delay
                time.sleep(1)  # Be polite
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # Only process HTML content
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    continue
                
                # Extract phone numbers
                new_numbers = self.extract_phone_numbers(response.text)
                if new_numbers:
                    logging.info(f"Found {len(new_numbers)} numbers: {new_numbers}")
                    self.phone_numbers.update(new_numbers)
                
                # Parse HTML and find links
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for anchor in soup.find_all('a', href=True):
                    link = anchor['href']
                    absolute_url = urljoin(url, link.split('#')[0])  # Remove fragments
                    
                    # Normalize URL and check validity
                    absolute_url = absolute_url.split('?')[0]  # Remove query params if needed
                    if self.is_valid_url(absolute_url) and absolute_url not in self.processed_urls:
                        if absolute_url not in self.url_queue:
                            self.url_queue.append(absolute_url)
                
                processed_count += 1
                self.processed_urls.add(url)
                
                # Save progress periodically
                if processed_count % 10 == 0:
                    self.save_results()
                    
            except Exception as e:
                logging.error(f"Error processing {url}: {str(e)}")
                continue
                
        self.save_results()
        logging.info(f"Crawling complete. Processed {processed_count} pages. Found {len(self.phone_numbers)} phone numbers.")

    def save_results(self):
        """Save results to file"""
        with open('phone_numbers.txt', 'w') as f:
            for number in sorted(self.phone_numbers):
                f.write(f"{number}\n")

if __name__ == '__main__':
    start_url = input("Enter the starting URL to crawl: ").strip()
    max_pages = input("Enter maximum pages to crawl (default 100): ").strip()
    
    try:
        max_pages = int(max_pages) if max_pages else 100
    except ValueError:
        max_pages = 100
    
    crawler = PhoneNumberCrawler(start_url, max_pages)
    crawler.crawl()