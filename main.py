from operator import attrgetter

from fastapi import FastAPI, HTTPException
import requests

import dvmn_stats

app = FastAPI()


@app.get("/{username}")
def read_user_stats(username: str, skip_unreviewed: bool = False) -> dict:
    try:
        history_html = dvmn_stats.get_dvmn_history_html(username)
    except requests.exceptions.HTTPError:
        raise HTTPException('User not found!')

    first_reviews_duration = dvmn_stats.get_first_reviews_durations(history_html, skip_unreviewed)

    if not first_reviews_duration:
        raise HTTPException('History is empty.')

    shortest_review = min(first_reviews_duration, key=attrgetter('hours'))
    longest_review = max(first_reviews_duration, key=attrgetter('hours'))

    modules_stats = dvmn_stats.build_stats_for_modules(first_reviews_duration)

    return {
        'shortest': shortest_review,
        'longest': longest_review,
        'modules_stats': modules_stats,
    }
