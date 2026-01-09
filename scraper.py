"""
Movie Theater Scraper for Classic Films in France
Scrapes AlloCiné to find which cities are showing classic movies
"""

import requests
from bs4 import BeautifulSoup
import time
import yaml
from datetime import datetime
from typing import List, Dict, Optional
import json
import re
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.console import Console
from rich.panel import Panel

console = Console()


class MovieScraper:
    """Scrapes AlloCiné for movie showtimes by city"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize scraper
        
        Args:
            config_path: Path to config file
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.movies = self.config['movies']
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['scraping']['user_agent']
        })
        self.results = {}
    
    def get_movie_metadata(self, allocine_id: str) -> Dict:
        """
        Get movie metadata (year, poster URL) from film page
        Returns dict with 'year' and 'poster' keys
        """
        film_url = f"https://www.allocine.fr/film/fichefilm_gen_cfilm={allocine_id}.html"
        
        try:
            response = self.session.get(film_url, timeout=10)
            if response.status_code != 200:
                return {'year': None, 'poster': None}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract year from release date
            year = None
            # Look for ANY element where 'date' appears in the class attribute
            # The class may have a random base64-like prefix before 'date'
            date_element = soup.find(lambda tag: tag.get('class') and any('date' in str(c) for c in tag.get('class')))
            
            if date_element:
                date_text = date_element.get_text(strip=True)
                year_match = re.search(r'\b(19|20)\d{2}\b', date_text)
                if year_match:
                    year = int(year_match.group())
            
            # Extract poster URL
            poster = None
            poster_img = soup.find('img', class_='thumbnail-img')
            if poster_img:
                poster = poster_img.get('src')
            
            return {'year': year, 'poster': poster}
            
        except Exception as e:
            return {'year': None, 'poster': None}
    
    def scrape_movie_cities(self, movie_name: str, allocine_id: str) -> List[str]:
        """Scrape which cities are showing a movie"""
        showtime_url = f"https://www.allocine.fr/seance/film-{allocine_id}/"
        
        try:
            response = self.session.get(showtime_url, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find city elements (span tags with js-set-localization class)
            city_elements = soup.find_all(['a', 'span'], class_='js-set-localization')
            
            if not city_elements:
                return []
            
            cities = []
            
            for elem in city_elements:
                city_name = elem.get_text(strip=True)
                # Remove numbers in parentheses like "Paris(15)" -> "Paris"
                city_name = re.sub(r'\(\d+\)$', '', city_name).strip()
                cities.append(city_name)
            
            return cities
            
        except Exception as e:
            return []
    
    def scrape_all(self):
        """Scrape all movies"""
        # First, scrape city screenings for all movies
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description:<20}", justify="left"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Scraping Screenings", total=len(self.movies))
            
            for movie in self.movies:
                allocine_id = movie['allocine_id']
                cities = self.scrape_movie_cities(movie['name'], allocine_id)
                
                # Initialize movie entry in results
                if allocine_id not in self.results:
                    self.results[allocine_id] = {
                        'metadata': {'name': movie['name']},
                        'screenings': []
                    }
                
                # Store city names
                self.results[allocine_id]['screenings'] = cities
                
                progress.advance(task)
                time.sleep(self.config['scraping']['allocine_delay'])
        
        # Then fetch metadata for all movies (year + poster)
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description:<20}", justify="left"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Scraping Metadata", total=len(self.movies))
            
            for movie in self.movies:
                allocine_id = movie['allocine_id']
                metadata = self.get_movie_metadata(allocine_id)
                
                # Update metadata with year and poster
                self.results[allocine_id]['metadata'].update({
                    'year': metadata.get('year'),
                    'poster': metadata.get('poster')
                })
                
                progress.advance(task)
                time.sleep(self.config['scraping']['allocine_delay'])
        
        console.print()
        
        # Sort movies: available first (alphabetically), then unavailable (alphabetically)
        available_movies = []
        unavailable_movies = []
        
        for allocine_id, data in self.results.items():
            metadata = data['metadata']
            year = metadata.get('year', 0) or 0
            movie_key = f"{metadata['name']} ({year})"
            
            if data['screenings']:
                available_movies.append((movie_key, allocine_id))
            else:
                unavailable_movies.append((movie_key, allocine_id))
        
        # Sort each group alphabetically
        available_movies.sort(key=lambda x: x[0])
        unavailable_movies.sort(key=lambda x: x[0])
        
        # Display available movies first
        for movie_key, allocine_id in available_movies:
            cities = sorted(self.results[allocine_id]['screenings'])
            url = f"https://www.allocine.fr/seance/film-{allocine_id}/"
            
            content = f"[green]Cities:[/green] {', '.join(cities)}\n[blue]URL:[/blue] {url}"
            console.print(Panel(content, title=f"{movie_key}", border_style="green"))
        
        # Then display unavailable movies
        for movie_key, allocine_id in unavailable_movies:
            content = "[dim]Not currently showing anywhere[/dim]"
            console.print(Panel(content, title=f"{movie_key}", border_style="dim"))
        
        # Save results with timestamp
        output = {
            'timestamp': datetime.now().isoformat(),
            'movies': self.results
        }
        
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    scraper = MovieScraper()
    scraper.scrape_all()
