"""
Automated Movie Theater Scraper with RSS Feed
Runs periodically to check for movies in theaters
"""

import schedule
import time
from scraper import MovieScraper
from rss_generator import RSSFeedGenerator
from datetime import datetime
import logging
import yaml
from rich.console import Console
from rich.panel import Panel

console = Console()

# Setup logging (file only, no console)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log')
    ]
)


def run_scraper():
    """Run the scraper and generate RSS feed"""
    logging.info("Starting scheduled scrape...")
    
    try:
        # Scrape movie listings (saves results.json automatically)
        scraper = MovieScraper()
        scraper.scrape_all()
        
        # Generate RSS feed
        generator = RSSFeedGenerator()
        new_count = generator.generate_from_file()
        
        console.print(f"\n[green]✅ Scraping completed[/green]")
        console.print(f"[green]✅ RSS feed generated[/green]")
        logging.info("Scraping completed")
        logging.info(f"RSS feed generated with {new_count} changes")
        
    except Exception as e:
        console.print(f"[red]Error during scraping: {e}[/red]")
        logging.error(f"Error during scraping: {e}")
        import traceback
        logging.error(traceback.format_exc())


def main():
    """Main function to run scheduled scraper"""
    console.print(Panel("[bold cyan]Movie Theater Scraper[/bold cyan]\nPeriodically checks French theaters for movies", expand=False))
    console.print()
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    daily_time = config['schedule']['daily_time']
    
    # Run immediately on startup
    console.print("[yellow]Running initial scrape...[/yellow]")
    run_scraper()
    
    # Schedule runs daily at specified time
    schedule.every().day.at(daily_time).do(run_scraper)
    
    console.print()
    console.print(f"[bold]Scheduled:[/bold] Daily at {daily_time}")
    console.print()
    console.print("[dim]Press Ctrl+C to stop...[/dim]")
    console.print()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping scraper...[/yellow]")
