# Provider Configuration

> This table lists all supported metadata providers, their required API keys, free tier availability, and scopes needed for NameGnome operation.

| Provider    | Required Key         | Free Tier | Scopes/Notes                                  |
|------------|----------------------|-----------|-----------------------------------------------|
| TMDB       | TMDB_API_KEY         | Yes       | Metadata (movies, TV); free for personal use  |
| TVDB       | TVDB_API_KEY         | Yes       | Metadata (TV); free tier, registration req.   |
| MusicBrainz| N/A                  | Yes       | Metadata (music); no key, rate-limited        |
| OMDb       | OMDB_API_KEY         | Yes       | Metadata (movies); free with email reg.       |
| Fanart.tv  | FANARTTV_API_KEY     | Yes       | Artwork (movies); free with account           |
| TheAudioDB | N/A                  | Yes       | Artwork (music); no key for basic endpoints   |
| AniList    | N/A                  | Yes       | Metadata (anime); public GraphQL API          |

**How to set up:**
- Place your API keys in a `.env` file or as environment variables as shown in the quick-start guide.
- See `.env.example` for template.
- For more details, visit each provider's website. 