import aiohttp
import os
from datetime import datetime, timezone
import time
from typing import Tuple


async def get_github_last_commit(
    repo_owner: str, repo_name: str
) -> Tuple[str, str, str]:
    """
    Fetch the latest commit info from GitHub
    Returns: (commit_hash, commit_date, commit_message)
    """
    async with aiohttp.ClientSession() as session:
        try:
            # Add headers to avoid rate limiting and get fresh data
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "If-None-Match": "",  # Ignore cache
                "Cache-Control": "no-cache",
            }

            # Try main branch first
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/main"
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/master"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return (
                                data["sha"][:7],
                                data["commit"]["author"]["date"],
                                data["commit"]["message"],
                            )
                elif response.status == 200:
                    data = await response.json()
                    return (
                        data["sha"][:7],
                        data["commit"]["author"]["date"],
                        data["commit"]["message"],
                    )

                print(f"Debug - GitHub API Status: {response.status}")  # Debug print

            current_time = datetime.now(timezone.utc)
            print(f"Debug - Fallback time: {current_time.isoformat()}")  # Debug print
            return "unknown", current_time.isoformat(), "unknown"
        except Exception as e:
            print(f"❌ Error fetching GitHub commit info: {e}")
            current_time = datetime.now(timezone.utc)
            print(
                f"Debug - Error fallback time: {current_time.isoformat()}"
            )  # Debug print
            return "unknown", current_time.isoformat(), "unknown"


def get_local_commit_info() -> tuple[str, str]:
    """
    Get local commit info
    Returns: (commit_hash, commit_date)
    """
    try:
        version_file = os.path.join(os.path.dirname(__file__), "..", "version.txt")
        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                content = f.read().strip().split(",")
                if len(content) == 2:
                    return content[0], content[1]
        return None, None
    except Exception as e:
        print(f"❌ Error reading local version: {e}")
        return None, None


async def compare_versions(
    local_date: str,
    github_date: str,
    local_hash: str,
    github_hash: str,
    commit_message: str,
) -> Tuple[bool, str]:
    """
    Compare local and GitHub versions using commit dates
    Returns: (is_latest, message)
    """
    try:
        # Format github date for display (always in UTC)
        github_dt = datetime.fromisoformat(github_date.replace("Z", "+00:00"))
        formatted_date = github_dt.strftime("%d.%m.%Y %H:%M UTC")

        # If no local version found, initialize it
        if local_hash is None or local_date is None:
            return (False, "")

        # Convert both dates to UTC
        local_dt = datetime.fromisoformat(local_date.replace("Z", "+00:00"))

        # Ensure both dates are UTC
        if github_dt.tzinfo is None:
            github_dt = github_dt.replace(tzinfo=timezone.utc)
        if local_dt.tzinfo is None:
            local_dt = local_dt.replace(tzinfo=timezone.utc)

        if local_hash == github_hash:
            return (
                True,
                f"✅ You have the latest version (commit from {formatted_date})",
            )
        print(local_dt, github_dt)
        if local_dt < github_dt:
            time_diff = github_dt - local_dt
            if time_diff.days > 0:
                time_str = f"{time_diff.days} days"
            elif time_diff.seconds // 3600 > 0:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''}"

            return (
                False,
                f"⚠️ Update available!\n"
                f"📅 Latest update released: {formatted_date}\n"
                f"⏰ Your version is {time_str} behind\n"
                f"ℹ️ To update, use: git pull\n"
                f"📥 Or download from: https://github.com/0xStarLabs/StarLabs-Monad",
            )
        else:
            return (
                True,
                f"❓ Local version ({local_hash}) is newer than GitHub ({github_hash})",
            )
    except Exception as e:
        print(f"❌ Error comparing versions: {e}")
        return False, "Error comparing versions"


def save_current_version(commit_hash: str, commit_date: str) -> None:
    """
    Save current version info to version.txt
    """
    try:
        version_file = os.path.join(
            os.path.dirname(__file__), "..", "version.txt"
        )  # Changed path to /src
        with open(version_file, "w") as f:
            f.write(f"{commit_hash},{commit_date}")
    except Exception as e:
        print(f"❌ Error saving version info: {e}")


async def check_version(repo_owner: str, repo_name: str) -> bool:
    """
    Main function to check versions and print status
    """

    # Сначала получаем время с GitHub, оно будет нашей точкой отсчета
    github_hash, github_date, commit_message = await get_github_last_commit(
        repo_owner, repo_name
    )

    # При первом запуске используем время GitHub вместо локального
    local_hash, _ = get_local_commit_info()
    local_date = github_date if local_hash is None else _

    is_latest, message = await compare_versions(
        local_date, github_date, local_hash, github_hash, commit_message
    )
    if message:
        print(message)

    # При сохранении всегда используем время с GitHub
    if local_hash is None or is_latest:
        save_current_version(github_hash, github_date)

    return is_latest
