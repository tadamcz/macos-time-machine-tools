#!/bin/zsh

# You should set this to run on a schedule somehow. I recommend using MacOS's built-in LaunchDaemons.
# You can take something like the `healthchecks.plist` file in this repo and put it in `/Library/LaunchDaemons/`
# (it must run as root).

# Get the path of the latest Time Machine backup
latest_backup=$(tmutil latestbackup)

# If there is no backup, exit with an error message
if [ -z "$latest_backup" ]; then
  echo "No Time Machine backups found"
  exit 1
fi


# Extract the date part from the path
backup_date=$(basename "$(dirname "$latest_backup")")

# Calculate the difference in seconds between now and the time of the latest backup
backup_age=$(($(date +%s) - $(date -j -f "%Y-%m-%d-%H%M%S.backup" "$backup_date" "+%s")))


# Send requests to healthchecks.io
if [ -z "$HEALTHCHECKS_UUID" ]; then
  echo "HEALTHCHECKS_UUID is not set. Exiting."
  exit 1
fi

three_days=259200 # 60*60*24*3
if [ $backup_age -lt $three_days ]; then
  echo "Latest backup is less than 3 days old. Sending request to https://hc-ping.com/$HEALTHCHECKS_UUID"
  curl "https://hc-ping.com/$HEALTHCHECKS_UUID"
else
  echo "Latest backup is more than 3 days old. Sending request to https://hc-ping.com/$HEALTHCHECKS_UUID/fail"
  curl "https://hc-ping.com/$HEALTHCHECKS_UUID/fail"
fi
