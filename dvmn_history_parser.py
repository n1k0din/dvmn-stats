import re
import typing as t
from collections import defaultdict, deque, namedtuple
from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from operator import attrgetter
from statistics import mean, median

import requests
import typer
from bs4 import BeautifulSoup
from dataclass_csv import DataclassWriter

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


ModuleLesson = namedtuple('ModuleLesson', 'module lesson')


@dataclass
class ReviewDuration:
    module_lesson: ModuleLesson
    hours: float

    def __str__(self):
        return f'{self.module_lesson.module}. {self.module_lesson.lesson} – {self.hours:.2f} ч.'


@dataclass
class LessonLog:
    module_lesson: ModuleLesson
    actions: deque


@dataclass
class ModuleStats:
    module_name: str
    mean: float
    median: float

    def __str__(self):
        return f'{self.module_name}. Среднее {self.mean:.2f}, медиана {self.median:.2f}'


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


def build_lessons_logs_stack(reviews: list[tuple[str, str, str, datetime]])\
        -> dict[ModuleLesson, t.Deque]:
    """
    Преобразует входящий список записей в словарь с очередью из отправил решение - получил ревью.
    """
    logs_for_lesson: dict[ModuleLesson, t.Deque] = defaultdict(deque)
    for _action, lesson, module, timestamp in reversed(reviews):
        module_lesson = ModuleLesson(module, lesson)
        logs_for_lesson[module_lesson].appendleft(timestamp)
    return logs_for_lesson


def convert_lessons_logs_to_dataclass_list(reviews_for_lesson: dict[ModuleLesson, t.Deque])\
        -> list[LessonLog]:

    lessons_logs = []
    for module_lesson, actions in reviews_for_lesson.items():
        lessons_logs.append(LessonLog(module_lesson, actions))

    return lessons_logs


def calc_first_reviews_duration(lessons_logs: list[LessonLog]) -> list[ReviewDuration]:
    """
    Перебирает список сдал/получил и создает список длительности первых проверок.
    """
    first_reviews_duration = []
    for lesson_logs in lessons_logs:
        first_sent = lesson_logs.actions.pop()
        try:
            first_recieved = lesson_logs.actions.pop()
        except IndexError:
            continue

        review_hours = timedelta_to_hours(first_recieved - first_sent)

        first_reviews_duration.append(ReviewDuration(lesson_logs.module_lesson, review_hours))

    return first_reviews_duration


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


def collect_actions_history(history_html: str) -> list[tuple[str, str, str, datetime]]:
    logs = []
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
            logs.append((action, lesson, module, timestamp))

    return logs


def build_stats_for_modules(reviews_durations: list[ReviewDuration])\
        -> list[ModuleStats]:
    modules_stats = []
    data = sorted(reviews_durations, key=attrgetter('module_lesson.module'))
    for module_name, module_reviews in groupby(data, key=attrgetter('module_lesson.module')):
        durations = [module_review.hours for module_review in module_reviews]
        modules_stats.append(ModuleStats(module_name, mean(durations), median(durations)))

    return modules_stats


def main(username: str, skip_csv: bool = False):
    """
    Разбирает историю, вычисляет статистику, выводит результат.
    """

    try:
        history_html = get_dvmn_history_html(username)
    except requests.exceptions.HTTPError:
        exit('Ошибка получения истории действий. Проверьте имя пользователя и доступ в интернет.')

    logs = collect_actions_history(history_html)
    lessons_logs_stack = build_lessons_logs_stack(logs)
    lesson_logs = convert_lessons_logs_to_dataclass_list(lessons_logs_stack)
    first_reviews_duration = calc_first_reviews_duration(lesson_logs)

    review_durations = [review.hours for review in first_reviews_duration]

    if not first_reviews_duration:
        exit('Первых проверок не найдено, в истории пусто')

    shortest_review = min(first_reviews_duration, key=attrgetter('hours'))
    longest_review = max(first_reviews_duration, key=attrgetter('hours'))

    print(f'Всего первых проверок: {len(first_reviews_duration)}')
    print(f'Минимальное время проверки: {shortest_review}')
    print(f'Максимальное время проверки: {longest_review}')
    print(f'Среднее время проверки: {mean(review_durations):.2f} ч.')
    print(f'Медианное время проверки: {median(review_durations):.2f} ч.')

    modules_stats = build_stats_for_modules(first_reviews_duration)
    print('Время проверки по модулям:')
    print(*modules_stats, sep='\n')

    if not skip_csv:
        with open(f'{username}_stats.csv', 'w', newline='') as csvfile:
            writer = DataclassWriter(csvfile, first_reviews_duration, ReviewDuration)
            writer.write()


if __name__ == '__main__':
    typer.run(main)
