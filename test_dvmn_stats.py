from datetime import datetime

import dvmn_stats


def test_remove_spaces():
    assert dvmn_stats.remove_spaces_series('     мама     мыла раму   ') == 'мама мыла раму'


def test_dvmn_time_converter():
    assert dvmn_stats.dvmn_time_str_to_datetime('11 января 2001 года 8:32') \
            == datetime(2001, 1, 11, 8, 32)


def test_build_lessons_logs_stack():
    html = '''\
        <div class="bg-white shadow-slim rounded-lg-bottom shadow-slim">
          <div class="container-wide py-5-adaptive">
            <div class="logtable mt-4 mb-4">
              <div class="mt-4 mb-4">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    18 мая 2021 г.
                  </div>
                </div>
                <hr class="mt-2 mb-2">
                <div class="logtable-row mb-1 p-2">
                  <div class="col-1_">
                    Отправил на проверку
                  </div>
                  <div class="col-2-3_">
                    <span class="text-nowrap">Урок 5.</span>
                    Пишем сайт для риелторов
                  </div>
                  <div class="col-2-3_">Знакомство с Django: ORM</div>
                  <div class="text-muted col-4_">
                    <small>18 мая 2021 г. 12:25</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>\
    '''

    assert dvmn_stats.collect_actions_history(html) == [
        (
            'sent',
            'Урок 5. Пишем сайт для риелторов',
            'Знакомство с Django: ORM',
            datetime(2021, 5, 18, 12, 25),
        ),
    ]
