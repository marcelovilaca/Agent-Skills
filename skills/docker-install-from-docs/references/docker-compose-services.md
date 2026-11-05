# Standard Docker multi-service install pattern (docs-derived)

From tt-rss Installation Guide / repo docker-compose.yml and common patterns:

Services (in dependency order):
- db: postgres image; env_file .env; volume db
- app: main app image; env_file .env; volumes app + ./config.d ro; depends_on db
- updater: same image, command updater script; depends_on app; shares app volume
- web-nginx: nginx-proxy image; ports ${HTTP_PORT}:80; depends_on app; volume app ro
- backups (optional): same image, command dcron.sh -f; depends_on db; volumes backups + app

Volumes: db:, app:, backups:

Image sources (comment both in compose):
- Docker Hub: supahgreg/tt-rss / supahgreg/tt-rss-web-nginx
- GHCR: ghcr.io/tt-rss/tt-rss / ghcr.io/tt-rss/tt-rss-web-nginx

Config override mount (always include in app/updater):
- ./config.d:/opt/tt-rss/config.d:ro
