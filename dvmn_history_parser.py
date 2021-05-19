import csv
import re
from collections import defaultdict, deque
from datetime import datetime
from statistics import mean, median

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


def remove_spaces_series(src_string):
    return re.sub(r'\s+', ' ', src_string)


def dmnv_time_str_to_datetime(string):
    day, ru_month, year, _, time = string.split()
    month = RUS_MONTH_NUM[ru_month]
    hours, minutes = time.split(':')

    day = int(day)
    year = int(year)
    hours = int(hours)
    minutes = int(minutes)

    return datetime(year, month, day, hours, minutes)


def split_reviews_by_lessons(reviews):
    reviews_by_lesson = defaultdict(deque)
    for action, lesson, module, timestamp in reversed(reviews):
        module_lesson = f'{module}. {lesson}'
        reviews_by_lesson[module_lesson].appendleft(timestamp)
    return reviews_by_lesson


def calc_first_reviews_time(reviews_by_lesson):
    first_reviews = []
    for lesson, reviews in reviews_by_lesson.items():
        first_sent = reviews.pop()
        first_recieved = reviews.pop()
        first_reviews.append(
            {
                'lesson': lesson,
                'review_time': timedelta_to_hours(first_recieved - first_sent),
            }
        )

    return first_reviews


def timedelta_to_hours(timedelta):
    return timedelta.days * 24 + timedelta.seconds / 60 / 60


def main():
    with open('history.html', 'r') as f:
        history_html = f.read()

    reviews = []
    soup = BeautifulSoup(history_html, 'lxml')
    rows = soup.find_all('div', class_='logtable-row mb-1 p-2')
    for row in rows:
        cols = row.find_all('div')
        action, lesson, module, timestamp = [col.text.strip() for col in cols]

        action = remove_spaces_series(action)
        lesson = remove_spaces_series(lesson)

        timestamp = dmnv_time_str_to_datetime(timestamp)

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

    with open('reviews_stats.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['lesson', 'review_time'])
        writer.writeheader()
        writer.writerows(first_reviews_time)


if __name__ == '__main__':
    main()
