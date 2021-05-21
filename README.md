# Вычислятель времени первых проверок dvmn.org
Парсит [историю действий ученика](https://dvmn.org/user/nik726/history/) и собирает информацию о времени проверок, выгружает данные в csv-файл.

## Аргументы
- `username` имя пользователя, обязательный.
- `--skip_csv` пропускать сохранение в csv-файл.

## Пример

### Запуск
Получает статистику пользователя nik726
  ```sh
  python nik726

  ```

### Результат

#### Консольный вывод
  ```
  Всего первых проверок: 33
  Минимальное время проверки: 0.02 ч.
  Максимальное время проверки: 176.05 ч.
  Среднее время проверки: 24.55 ч.
  Медианное время проверки: 15.80 ч.
  ```
#### nik726_stats.csv
lesson|review_time
------|-----------
Знакомство с Python. Урок 1. Раскрутите планету|18.55
Знакомство с Python. Урок 2. Готовим речь|0.55
Знакомство с Python. Урок 3. Рассылаем имейлы|3.65
Знакомство с Python. Урок 4. Нарезаем аватарки|5.383333333333334
Знакомство с Python. Урок 5. Считаем секунды в Telegram|0.4166666666666667
Знакомство с Python. Урок 6. Создаём человеков|31.28333333333333

## Установка и запуск

1. Скачайте код и перейдите в папку проекта
  ```bash
  git clone https://github.com/n1k0din/dvmn-stats.git
  ```  
  ```bash
  cd dvmn-stats
  ```
2. Скопируйте файл с шага 0. в `dvmn-stats`

3. Установите вирт. окружение
```bash
python -m venv venv
```
4. Активируйте
```bash
venv\Scripts\activate.bat
```
 или
 ```
 source venv/bin/activate
 ```
5. Установите необходимые пакеты
```bash
pip install -r requirements.txt
```
6. Запустите
```bash
python dvmn_history_parser.py USERNAME [--skip_csv]
```
