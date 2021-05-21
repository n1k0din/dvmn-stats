import argparse
import csv
import re
import typing as t
from collections import defaultdict, deque
from datetime import datetime
from statistics import mean, median

import requests
from bs4 import BeautifulSoup

RUS_MONTH_NUM = {
    'января': 1,
    'февраля': 2,
    'марта': 3,
    'апреля': 4,
    'мая': 5,
    'июня': 6,
    'июля': 7,
    'августа': 8,
    'сентября': 9,
    'октября': 10,
    'ноября': 11,
    'декабря': 12,
}


class LessonReviewTime(t.TypedDict):
    """
    Typing класс для словаря с двумя ключами - урок и время проверки
    """
    lesson: str
    review_time: float


def fetch_cli_parameters():
    arg_parser = argparse.ArgumentParser(description='Parse and calc dvmn.org history stats')
    arg_parser.add_argument('username', help='Username')
    arg_parser.add_argument('--skip_csv', action='store_true', help='Skip downloading csv')

    return arg_parser.parse_args()


def remove_spaces_series(src_string: str) -> str:
    """
    Возвращает строку без последовательных пробельных символов
    """
    return re.sub(r'\s+', ' ', src_string)


def dvmn_time_str_to_datetime(dvmn_time_str: str):
    """
    Преобразует строку с датой и временем определенного формата в datetime
    """
    day_str, ru_month, year_str, _, time_str = dvmn_time_str.split()
    month = RUS_MONTH_NUM[ru_month]
    hours_str, minutes_str = time_str.split(':')

    day = int(day_str)
    year = int(year_str)
    hours = int(hours_str)
    minutes = int(minutes_str)

    return datetime(year, month, day, hours, minutes)


def split_reviews_by_lessons(reviews: list[tuple[str, str, str, str]])\
        -> dict[str, t.Deque]:
    """
    Преобразует входящий список записей в словарь с ключом 'имя_модуля+имя_урока'.
    Значение: очередь из отправил решение - получил ревью.
    """
    reviews_by_lesson: dict[str, t.Deque] = defaultdict(deque)
    for _action, lesson, module, timestamp in reversed(reviews):
        module_lesson = f'{module}. {lesson}'
        reviews_by_lesson[module_lesson].appendleft(timestamp)
    return reviews_by_lesson


def calc_first_reviews_time(reviews_by_lesson:  dict[str, t.Deque]) \
        -> list[LessonReviewTime]:
    """
    Перебирает словарь с очередями сдал_задачу/получил_ревью и создает список словарей:
    lesson: имя_модуля+имя_урока, review_time: длительность первой проверки
    """
    first_reviews = []
    for lesson, reviews in reviews_by_lesson.items():
        first_sent = reviews.pop()
        try:
            first_recieved = reviews.pop()
        except IndexError:
            continue
        first_reviews.append(
            {
                'lesson': lesson,
                'review_time': timedelta_to_hours(first_recieved - first_sent),
            }
        )

    return first_reviews


def timedelta_to_hours(timedelta) -> float:
    """
    Вычисляет количество часов в обычном datetime.timdelta
    """
    return timedelta.days * 24 + timedelta.seconds / 60 / 60


def get_dvmn_history_html(username: str):
    url = f'https://dvmn.org/user/{username}/history/'
    response = requests.get(url)
    response.raise_for_status()

    return response.text


def main():
    """
    Разбирает историю, вычисляет статистику, выводит результат.
    """
    args = fetch_cli_parameters()
    username = args.username
    skip_csv = args.skip_csv

    try:
        history_html = get_dvmn_history_html(username)
    except requests.exceptions.HTTPError:
        exit('Ошибка получения истории действий. Проверьте имя пользователя и доступ в интернет.')

    reviews = []
    soup = BeautifulSoup(history_html, 'lxml')
    rows = soup.find_all('div', class_='logtable-row mb-1 p-2')
    for row in rows:
        cols = row.find_all('div')
        action, lesson, module, timestamp = [col.text.strip() for col in cols]

        action = remove_spaces_series(action)
        lesson = remove_spaces_series(lesson)

        timestamp = dvmn_time_str_to_datetime(timestamp)

        if action.startswith('Отправил на проверку'):
            action = 'sent'
        elif action.startswith('Получил код-ревью'):
            action = 'recieved'

        if action in ('sent', 'recieved'):
            reviews.append((action, lesson, module, timestamp))

    first_reviews_time = calc_first_reviews_time(split_reviews_by_lessons(reviews))

    review_durations = [review['review_time'] for review in first_reviews_time]

    print(f'Всего первых проверок: {len(first_reviews_time)}')
    print(f'Минимальное время проверки: {min(review_durations):.2f} ч.')
    print(f'Максимальное время проверки: {max(review_durations):.2f} ч.')
    print(f'Среднее время проверки: {mean(review_durations):.2f} ч.')
    print(f'Медианное время проверки: {median(review_durations):.2f} ч.')

    if not skip_csv:
        with open(f'{username}_stats.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['lesson', 'review_time'])
            writer.writeheader()
            writer.writerows(first_reviews_time)


if __name__ == '__main__':
    main()
