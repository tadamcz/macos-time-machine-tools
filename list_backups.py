import argparse
import datetime
import subprocess
from dataclasses import dataclass

from backoff import retry

parser = argparse.ArgumentParser()
parser.add_argument('n_recent', type=int, nargs="?", default=10, help='Analyse the `n` most recent backups')
args = parser.parse_args()

MAX_RETRIES = 5


@dataclass
class Backup:
    path: str

    def __post_init__(self):
        date = self.path.split("/")[-1].split(".")[0]
        self.date = datetime.datetime.strptime(date, "%Y-%m-%d-%H%M%S")
        time_ago = datetime.datetime.now() - self.date
        self.time_ago = f"{time_ago.days}d {time_ago.seconds // 3600}h {time_ago.seconds // 60 % 60}m ago"

    @retry(exception=Exception, n_tries=MAX_RETRIES)
    def calculate_size(self):
        timeout = 45
        print(f"\t{self.date} (timeout={timeout}s)...", end=" ")
        uniquesize = subprocess.run(["tmutil", "uniquesize", self.path], capture_output=True, text=True, timeout=timeout)
        print("Success.")
        self.size, _ = uniquesize.stdout.split(" ")

    def try_calculate_size(self):
        try:
            self.calculate_size()
        except Exception as e:
            self.size = f"ERROR ({MAX_RETRIES} retries)"


@retry(exception=Exception, n_tries=MAX_RETRIES)
def list_backups():
    command = ["tmutil", "listbackups", "-m"]
    timeout = 45
    print(f"Running `{' '.join(command)}` (timeout={timeout}s)...", end=" ")
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise Exception(f"`tmutil listbackups` failed with '{result.stderr}'")
    else:
        result = result.stdout.splitlines()
        print("Found", len(result), "backups.")
    return result


status = subprocess.check_output(["tmutil", "status"], text=True, timeout=1).strip()
if "Running = 1;" in status:
    print("Time Machine is currently running with status:")
    print(status)
    print("Please wait for it to finish before running this script.")
    exit(1)

backups = list_backups()
backups = [Backup(b) for b in backups[-args.n_recent:]]
print("Calculating size of", len(backups), "most recent backups...")
for backup in backups:
    backup.try_calculate_size()
print("========================================")
print("Results:")
for backup in backups:
    # Align size as column
    backup.time_ago = f"({backup.time_ago})".ljust(20)
    print(f"{backup.date} {backup.time_ago} {backup.size:>10}")

exit(0)
