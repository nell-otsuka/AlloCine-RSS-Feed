"""
RSS Feed Generator for Movie Showtimes
Generates an RSS feed from scraped movie data
"""

from feedgen.feed import FeedGenerator
from datetime import datetime
import json
import yaml
from typing import Dict
import os
import zoneinfo


class RSSFeedGenerator:
    """Generates RSS feed from movie showtime data"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize feed generator with configuration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.rss_config = self.config['rss']
        self.previous_results = self._load_previous_results()
    
    def _load_previous_results(self) -> Dict:
        """Load previous results to detect changes"""
        history_file = "results_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, ValueError):
                return {}
        return {}
    
    def _save_results_history(self, current_movies: Dict):
        """Save current results for next comparison"""
        with open("results_history.json", 'w', encoding='utf-8') as f:
            json.dump(current_movies, f, ensure_ascii=False, indent=2)
    
    def _detect_new_showtimes(self, current_movies: Dict) -> list[dict]:
        """Detect new showtimes that weren't in previous run"""
        new_showtimes = []
        
        for allocine_id, data in current_movies.items():
            metadata = data['metadata']
            url = f"https://www.allocine.fr/seance/film-{allocine_id}/"
            for city in data['screenings']:
                key = f"{allocine_id}_{city}"
                
                # Check if this movie-city combo existed before
                prev_data = self.previous_results.get(allocine_id)
                if not prev_data or city not in prev_data.get('screenings', []):
                    new_showtimes.append({
                        'movie': metadata['name'],
                        'year': metadata.get('year', 0) or 0,
                        'city': city,
                        'poster': metadata.get('poster'),
                        'allocine_id': allocine_id,
                        'url': url,
                        'found_date': datetime.now().isoformat()
                    })
        
        return new_showtimes
    
    def generate_feed(self, movies_dict: Dict, output_file: str = None):
        """
        Generate RSS feed from current results
        
        Args:
            movies_dict: Dictionary of movie data (nested structure from results.json)
            output_file: Path to output RSS file (uses config if not provided)
        """
        if output_file is None:
            output_file = self.rss_config['output_file']
        
        # Only detect changes if we have previous results
        new_showtimes = []
        
        if self.previous_results:
            new_showtimes = self._detect_new_showtimes(movies_dict)
        
        # Group new screenings by movie
        new_by_movie = {}
        for item in new_showtimes:
            key = item['allocine_id']
            if key not in new_by_movie:
                new_by_movie[key] = []
            new_by_movie[key].append(item['city'])

        
        # Setup feed
        fg = FeedGenerator()
        fg.id(self.rss_config['link'])
        fg.title(self.rss_config['title'])
        fg.description(self.rss_config['description'])
        fg.link(href=self.rss_config['link'], rel='alternate')
        fg.language('fr-FR')
        
        # Use France timezone
        paris_tz = zoneinfo.ZoneInfo('Europe/Paris')
        fg.updated(datetime.now(paris_tz))
        
        # Separate movies with updates vs without updates
        movies_with_updates = []
        movies_without_updates = []
        
        for allocine_id, data in movies_dict.items():
            if data['screenings']:  # Only movies with current screenings
                if allocine_id in new_by_movie:
                    movies_with_updates.append((allocine_id, data))
                else:
                    movies_without_updates.append((allocine_id, data))
        
        # Sort each group alphabetically by movie name
        movies_with_updates.sort(key=lambda x: x[1]['metadata']['name'])
        movies_without_updates.sort(key=lambda x: x[1]['metadata']['name'])
        
        # Combine: updated first, then others
        sorted_movies = movies_with_updates + movies_without_updates
        
        # Reverse because RSS feeds display in reverse order (last added = first shown)
        sorted_movies.reverse()
        
        # Create one entry per movie
        for allocine_id, data in sorted_movies:
            metadata = data['metadata']
            current_cities = sorted(data['screenings'])
            
            # Skip movies with no screenings
            if not current_cities:
                continue
            
            fe = fg.add_entry()
            
            # Stable GUID (movie title + year)
            movie_title = metadata['name']
            movie_year = metadata.get('year', 0) or 0
            
            # Add emoji to title if there are new screenings
            display_title = f"✨ {movie_title} ({movie_year})" if allocine_id in new_by_movie else f"{movie_title} ({movie_year})"
            
            fe.id(f"{movie_title}-{movie_year}")
            fe.title(display_title)
            fe.link(href=f"https://www.allocine.fr/seance/film-{allocine_id}/")
            
            # Build description with HTML
            description_parts = []
            description_parts.append(f"<strong>⌛ Current:</strong> {', '.join(current_cities)}")
            
            # Add new screenings if any
            if allocine_id in new_by_movie:
                new_cities = sorted(new_by_movie[allocine_id])
                description_parts.append(f"<br/><strong>🔔 New:</strong> {', '.join(new_cities)}")
            
            # Use content() method which handles CDATA properly
            description_html = "".join(description_parts)
            fe.content(content=description_html, type='CDATA')
            
            # Add poster if available
            if metadata.get('poster'):
                fe.enclosure(url=metadata['poster'], type='image/jpeg', length='0')
            
            # Set dates
            pub_date = datetime.now(paris_tz)
            fe.published(pub_date)
            fe.updated(pub_date)
        
        # Generate RSS file
        fg.rss_file(output_file, pretty=True)
        
        # Save current results for next comparison
        self._save_results_history(movies_dict)
        
        return len(new_by_movie)
    
    def generate_from_file(self, results_file: str = "results.json", output_file: str = None):
        """
        Generate RSS feed from results JSON file
        
        Args:
            results_file: Path to results JSON file
            output_file: Path to output RSS file
        """
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract movies dict from new nested structure
        movies_dict = data.get('movies', {})
        
        return self.generate_feed(movies_dict, output_file)


if __name__ == "__main__":
    # Generate RSS feed from latest results
    generator = RSSFeedGenerator()
    change_count = generator.generate_from_file()
    
    if not generator.previous_results:
        print("✅ RSS feed generated (first run)")
    elif change_count > 0:
        print(f"✅ RSS feed generated with {change_count} movie(s) with changes")
    else:
        print("✅ RSS feed generated (no changes detected)")
