#!/usr/bin/env python3
"""
InfinitePay Help Center Web Scraper

This module crawls the InfinitePay help center (https://ajuda.infinitepay.io/pt-BR/)
to extract all articles with proper rate limiting and deduplication.
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from typing import List, Dict, Set
import json
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Article:
    """Represents a scraped article"""
    title: str
    url: str
    content: str
    category: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "category": self.category
        }

class InfinitePayScraper:
    """Web scraper for InfinitePay help center"""
    
    def __init__(self, base_url: str = "https://ajuda.infinitepay.io/pt-BR/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; InfinitePayRAG/1.0; +https://github.com/infinitepay/rag)'
        })
        self.visited_urls: Set[str] = set()
        self.articles: List[Article] = []
        
    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing anchors and query parameters"""
        parsed = urlparse(url)
        # Remove fragment (anchor) and query parameters for deduplication
        normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return normalized.rstrip('/')
    
    def is_article_url(self, url: str) -> bool:
        """Check if URL is an article page"""
        return '/articles/' in url or '/pt-BR/' in url
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled"""
        parsed = urlparse(url)
        
        # Must be from the same domain
        if parsed.netloc and 'ajuda.infinitepay.io' not in parsed.netloc:
            return False
            
        # Skip certain paths
        skip_paths = ['/search', '/contact', '/login', '/logout', '/admin']
        if any(skip_path in url for skip_path in skip_paths):
            return False
            
        return True
    
    def extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from article page"""
        content_parts = []
        
        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if not main_content:
            main_content = soup
            
        # Extract headings
        for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text(strip=True)
            if text:
                content_parts.append(f"\n{text}\n")
        
        # Extract paragraphs
        for paragraph in main_content.find_all('p'):
            text = paragraph.get_text(strip=True)
            if text and len(text) > 10:  # Skip very short paragraphs
                content_parts.append(text)
        
        # Extract lists
        for list_elem in main_content.find_all(['ul', 'ol']):
            for item in list_elem.find_all('li'):
                text = item.get_text(strip=True)
                if text:
                    content_parts.append(f"• {text}")
        
        # Extract tables
        for table in main_content.find_all('table'):
            for row in table.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if cells:
                    content_parts.append(" | ".join(cells))
        
        return "\n\n".join(content_parts)
    
    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try different title selectors
        title_selectors = [
            'h1',
            '.article-title',
            '.page-title',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and title != "InfinitePay":
                    return title
        
        return "Untitled Article"
    
    def scrape_page(self, url: str) -> bool:
        """Scrape a single page and extract article content"""
        try:
            logger.info(f"Scraping: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article content
            title = self.extract_title(soup)
            content = self.extract_text_content(soup)
            
            if content and len(content.strip()) > 100:  # Only save substantial content
                article = Article(
                    title=title,
                    url=url,
                    content=content.strip()
                )
                self.articles.append(article)
                logger.info(f"Extracted article: {title} ({len(content)} chars)")
                return True
            else:
                logger.warning(f"Insufficient content found at {url}")
                return False
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return False
    
    def find_links(self, url: str) -> List[str]:
        """Find all internal links on a page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                normalized_url = self.normalize_url(full_url)
                
                if self.is_valid_url(normalized_url) and normalized_url not in self.visited_urls:
                    links.append(normalized_url)
            
            return links
            
        except Exception as e:
            logger.error(f"Error finding links at {url}: {str(e)}")
            return []
    
    def crawl(self, max_pages: int = 500, delay: float = 0.5) -> List[Article]:
        """Crawl the help center starting from base URL"""
        logger.info(f"Starting crawl of {self.base_url}")
        
        # Start with base URL
        urls_to_visit = [self.normalize_url(self.base_url)]
        pages_crawled = 0
        
        while urls_to_visit and pages_crawled < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            pages_crawled += 1
            
            # Scrape current page if it's an article
            if self.is_article_url(current_url):
                self.scrape_page(current_url)
            
            # Find new links to crawl
            new_links = self.find_links(current_url)
            urls_to_visit.extend(new_links)
            
            # Rate limiting
            time.sleep(delay)
            
            if pages_crawled % 10 == 0:
                logger.info(f"Crawled {pages_crawled} pages, found {len(self.articles)} articles")
        
        logger.info(f"Crawling completed. Found {len(self.articles)} articles from {pages_crawled} pages")
        return self.articles
    
    def save_articles(self, filepath: str) -> None:
        """Save scraped articles to JSON file"""
        articles_data = [article.to_dict() for article in self.articles]
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(self.articles)} articles to {filepath}")
    
    def load_articles(self, filepath: str) -> List[Article]:
        """Load articles from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                articles_data = json.load(f)
            
            self.articles = [
                Article(
                    title=data['title'],
                    url=data['url'],
                    content=data['content'],
                    category=data.get('category', '')
                )
                for data in articles_data
            ]
            
            logger.info(f"Loaded {len(self.articles)} articles from {filepath}")
            return self.articles
            
        except FileNotFoundError:
            logger.warning(f"File {filepath} not found")
            return []
        except Exception as e:
            logger.error(f"Error loading articles: {str(e)}")
            return []
    
    def scrape_all_articles(self, max_articles: int = 500, delay: float = 0.5) -> List[Article]:
        """Scrape all articles from the help center (alias for crawl method)"""
        return self.crawl(max_pages=max_articles, delay=delay)

def main():
    """Main function for testing the scraper"""
    scraper = InfinitePayScraper()
    
    # Crawl the help center
    articles = scraper.crawl(max_pages=100, delay=0.5)
    
    # Save results
    scraper.save_articles('data/infinitepay_articles.json')
    
    # Print summary
    print(f"\nScraping Summary:")
    print(f"Total articles: {len(articles)}")
    print(f"\nSample articles:")
    for i, article in enumerate(articles[:3]):
        print(f"{i+1}. {article.title}")
        print(f"   URL: {article.url}")
        print(f"   Content length: {len(article.content)} chars")
        print()

if __name__ == "__main__":
    main()