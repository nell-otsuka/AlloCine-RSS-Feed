# Movie Theater Scraper

Tracks movies in French theaters. Scrapes AlloCiné, generates RSS feed with change detection.

## Setup

```powershell
pip install -r requirements.txt
```

Add movies to `config.yaml`:
```yaml
movies:
  - name: "Blade Runner"
    year: 1982
    allocine_id: 1975  # From allocine.fr URL
```

## Usage

**Scrape all cities**:
```powershell
python scraper.py
```

**Scrape with proximity filter** (city name + radius in km):
```powershell
python scraper.py --near rouen 120
```

**Generate RSS feed** (from results.json):
```powershell
python rss_generator.py
```

**Automated** (daily at 9 AM + every 6 hours):
```powershell
python main.py
```

RSS feed: `movie_feed.xml`

For personal use only.
