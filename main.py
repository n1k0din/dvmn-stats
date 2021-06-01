import typing as t
from operator import attrgetter

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import dvmn_stats

app = FastAPI()

origins = [
    'http://localhost',
    'http://localhost:8080',
    'http://localhost:3000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_reviews(username: str, skip_unreviewed: bool) -> t.List[dvmn_stats.ReviewDuration]:
    try:
        history_html = dvmn_stats.get_dvmn_history_html(username)
    except requests.exceptions.HTTPError:
        raise HTTPException(404, detail='User not found!')

    first_reviews_duration = dvmn_stats.get_first_reviews_durations(history_html, skip_unreviewed)

    if not first_reviews_duration:
        raise HTTPException(404, detail='History is empty.')

    return first_reviews_duration


@app.get("/profile/{username}")
def read_user_stats(username: str, skip_unreviewed: bool = False) -> dict:

    reviews = get_reviews(username, skip_unreviewed)

    modules_stats = dvmn_stats.build_stats_for_modules(reviews)

    return {
        'modules_stats': modules_stats,
    }


@app.get("/{username}/minmax")
def read_user_minmax(username: str) -> dict:
    reviews = get_reviews(username, skip_unreviewed=False)

    shortest_review = min(reviews, key=attrgetter('hours'))
    longest_review = max(reviews, key=attrgetter('hours'))

    return {
        'min': shortest_review,
        'max': longest_review,
    }
