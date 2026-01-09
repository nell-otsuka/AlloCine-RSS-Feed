# AlloCiné RSS Feed

Automated scraper that tracks classic movie showtimes in French theaters. Scrapes AlloCiné daily and generates an RSS feed with change detection.

## RSS Feed

**Public URL**: https://nell-otsuka.github.io/AlloCine-RSS-Feed/movie_feed.xml

Updates daily at 8 PM Paris time via GitHub Actions.

## Features

- Scrapes movie showtimes from AlloCiné
- Detects new screenings (🔔 emoji in feed)
- Fetches movie metadata (year, poster)
- RSS 2.0 feed with CDATA HTML content
- Automated daily updates via GitHub Actions

## Configuration

Add movies to `config.yaml`:
```yaml
movies:
  - name: "Blade Runner"
    allocine_id: 1975  # From allocine.fr film URL
```

Year and poster are automatically scraped from AlloCiné.

## Local Testing

```powershell
pip install -r requirements.txt
python scraper.py        # Manual scrape
python rss_generator.py  # Generate RSS
python main.py           # Scheduled (daily at 8 PM)
```

## GitHub Actions

Workflow runs daily at 8 PM Paris time, commits updated `results.json` and `movie_feed.xml` to the repo.

**Required settings**:
- GitHub Pages enabled (source: main/master branch, root folder)
- Actions permissions: Read and write

For personal use only.
