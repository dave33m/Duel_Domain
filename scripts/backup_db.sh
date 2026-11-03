#!/bin/sh
# Dumps one environment's Postgres database to ~/backups/<project>/ and prunes old dumps.
# Run on the VPS as the deploy user, e.g. from cron:
#   15 3 * * * sh ~/Duel_Domain/scripts/backup_db.sh duel-domain ~/Duel_Domain
#
# Restore a dump (overwrites the current data):
#   docker compose -p <project> exec -T db pg_restore -U duel -d duel_domain --clean --if-exists < <file>.dump
set -e

PROJECT="$1"
CHECKOUT="$2"
KEEP_DAYS="${KEEP_DAYS:-14}"
if [ -z "$PROJECT" ] || [ -z "$CHECKOUT" ]; then
    echo "Usage: $0 <compose-project> <checkout-dir>" >&2
    exit 1
fi

BACKUP_DIR="$HOME/backups/$PROJECT"
mkdir -p "$BACKUP_DIR"
FILE="$BACKUP_DIR/$PROJECT-$(date -u +%Y%m%d-%H%M%S).dump"

cd "$CHECKOUT"
# Write to a temp name first so a failed dump never looks like a good backup.
docker compose -p "$PROJECT" exec -T db pg_dump -U duel -d duel_domain --format=custom > "$FILE.partial"
mv "$FILE.partial" "$FILE"

find "$BACKUP_DIR" -name "$PROJECT-*.dump" -mtime +"$KEEP_DAYS" -delete
echo "Backed up $PROJECT to $FILE"
