#!/usr/bin/env python3
"""Статистика рилсов Виолы: нормировка на возраст поста, дециля, матрица решений.

Источник данных: analitika/reels-data.csv (выгрузка Instagram @viola.maro.psy).
Только стандартная библиотека.

Зачем нормировка. Медиана просмотров падает со временем (2025-01 ~38k -> 2026-08 ~12k):
меняется охват аккаунта, а не качество рилса. Сравнивать сырые просмотры между 2025 и 2026
нельзя. K = просмотры / медиана окна +-30 дней вокруг даты публикации. K=1 -- ровно как
обычно в тот период; K=3 -- втрое выше нормы своего времени.

Чего в выгрузке НЕТ: сохранений, досмотров, подписок с рилса, обложек. Ось "квалификация"
считается по прокси: комментарии на 1000 просмотров (CR) и лайки на 1000 просмотров (LR).

Запуск:
    python3 skripty/reels_stats.py            # общий отчёт
    python3 skripty/reels_stats.py --top 20   # верх и низ по K
    python3 skripty/reels_stats.py --csv      # выгрузка с K и прокси в stdout
"""
import csv, sys, re, statistics, datetime, collections

DATA = 'analitika/reels-data.csv'
WINDOW_DAYS = 30
MIN_WINDOW_N = 5   # меньше -- окно ненадёжно, берём глобальную медиану года

# Бакеты длительности подобраны под фактическое распределение (медиана 114 сек),
# а не под "типовой рилс до 60 сек": у Виолы формат длинный.
BUCKETS = [(0, 45), (45, 75), (75, 120), (120, 180), (180, 10**6)]


def load(path=DATA):
    recs = []
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            recs.append({
                'date': datetime.date.fromisoformat(r['data']),
                'views': int(r['prosmotry']),
                'likes': int(r['laiki']),
                'comments': int(r['kommentarii']),
                'dur': float(r['dlitelnost']),
                'url': r['ssylka'],
                'desc': r['opisanie'].strip(),
                'tr': r['transkript'].strip(),
            })
    recs.sort(key=lambda x: x['date'])
    return recs


def add_norm(recs):
    """K = просмотры / медиана окна +-30 дней (сам рилс из окна исключён)."""
    by_year = collections.defaultdict(list)
    for r in recs:
        by_year[r['date'].year].append(r['views'])
    year_med = {y: statistics.median(v) for y, v in by_year.items()}
    for r in recs:
        lo = r['date'] - datetime.timedelta(days=WINDOW_DAYS)
        hi = r['date'] + datetime.timedelta(days=WINDOW_DAYS)
        w = [o['views'] for o in recs if o is not r and lo <= o['date'] <= hi]
        base = statistics.median(w) if len(w) >= MIN_WINDOW_N else year_med[r['date'].year]
        r['base'] = base
        r['K'] = r['views'] / base
        r['LR'] = 1000 * r['likes'] / r['views']    # лайки на 1000 просмотров
        r['CR'] = 1000 * r['comments'] / r['views']  # комментарии на 1000 просмотров
        r['bucket'] = next('%d-%d' % (a, b) if b < 10**6 else '%d+' % a
                           for a, b in BUCKETS if a <= r['dur'] < b)
    return recs


def clean_text(t):
    t = re.sub(r'https?://\S+', ' ', t)
    t = re.sub(r'#\S+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def text_of(r):
    """Текст рилса: транскрипт, если есть, иначе описание (в 69% случаев это тот же текст)."""
    return r['tr'] if r['tr'] else clean_text(r['desc'])


def quartile_split(recs, key):
    vals = sorted(r[key] for r in recs)
    n = len(vals)
    return vals[n // 4], statistics.median(vals), vals[3 * n // 4]


def matrix(recs):
    """2x2: залёт (K) x квалификация (CR -- комментарии на 1000 просмотров)."""
    kmed = statistics.median(r['K'] for r in recs)
    cmed = statistics.median(r['CR'] for r in recs)
    cells = collections.defaultdict(list)
    for r in recs:
        hi_k = r['K'] >= kmed
        hi_c = r['CR'] >= cmed
        cells[('ЯДРО' if hi_c else 'ВЕРХ ВОРОНКИ') if hi_k
              else ('ПЕРЕУПАКОВАТЬ' if hi_c else 'ВЫКИНУТЬ')].append(r)
    return kmed, cmed, cells


def fmt(r):
    return ('%s K=%4.2f  %7d просм  LR=%5.1f CR=%4.2f  %3d сек  %s\n      %s'
            % (r['date'], r['K'], r['views'], r['LR'], r['CR'], round(r['dur']), r['url'],
               text_of(r)[:110].replace('\n', ' ')))


def report(recs, top_n=15):
    print('РИЛСЫ @viola.maro.psy — %d шт, %s … %s' % (len(recs), recs[0]['date'], recs[-1]['date']))
    print('Суммарно просмотров: %s | медиана: %s | транскриптов: %d'
          % (f"{sum(r['views'] for r in recs):,}".replace(',', ' '),
             f"{int(statistics.median(r['views'] for r in recs)):,}".replace(',', ' '),
             sum(1 for r in recs if r['tr'])))

    print('\n— ДРЕЙФ ОХВАТА ПО ПОЛУГОДИЯМ (почему нужна нормировка) —')
    half = collections.defaultdict(list)
    for r in recs:
        half['%d-H%d' % (r['date'].year, 1 if r['date'].month <= 6 else 2)].append(r)
    print('период    n   медиана просм.  медиана LR  медиана CR')
    for k in sorted(half):
        g = half[k]
        print('%-9s %3d %14s %11.1f %11.2f'
              % (k, len(g), f"{int(statistics.median(x['views'] for x in g)):,}".replace(',', ' '),
                 statistics.median(x['LR'] for x in g), statistics.median(x['CR'] for x in g)))

    print('\n— ДЛИТЕЛЬНОСТЬ (K нормирован, поэтому сравнимо между годами) —')
    print('бакет, сек   n   медиана K   медиана LR  медиана CR')
    bk = collections.defaultdict(list)
    for r in recs:
        bk[r['bucket']].append(r)
    for a, b in BUCKETS:
        k = '%d-%d' % (a, b) if b < 10**6 else '%d+' % a
        g = bk.get(k, [])
        if not g:
            continue
        print('%-11s %3d %11.2f %12.1f %11.2f'
              % (k, len(g), statistics.median(x['K'] for x in g),
                 statistics.median(x['LR'] for x in g), statistics.median(x['CR'] for x in g)))

    kmed, cmed, cells = matrix(recs)
    print('\n— МАТРИЦА РЕШЕНИЙ (порог K=%.2f, CR=%.2f — медианы) —' % (kmed, cmed))
    for name in ('ЯДРО', 'ВЕРХ ВОРОНКИ', 'ПЕРЕУПАКОВАТЬ', 'ВЫКИНУТЬ'):
        g = cells[name]
        print('%-14s n=%3d  медиана K=%4.2f  медиана CR=%4.2f'
              % (name, len(g), statistics.median(x['K'] for x in g),
                 statistics.median(x['CR'] for x in g)))

    sk = sorted(recs, key=lambda x: -x['K'])
    print('\n— ВЕРХНИЙ ДЕЦИЛЬ ПО K (топ-%d) —' % top_n)
    for r in sk[:top_n]:
        print(fmt(r))
    print('\n— НИЖНИЙ ДЕЦИЛЬ ПО K (дно-%d) —' % top_n)
    for r in sk[-top_n:]:
        print(fmt(r))


def dump_csv(recs):
    w = csv.writer(sys.stdout)
    w.writerow(['data', 'prosmotry', 'K', 'LR', 'CR', 'dlitelnost', 'bucket', 'est_transkript', 'ssylka'])
    for r in sorted(recs, key=lambda x: -x['K']):
        w.writerow([r['date'], r['views'], '%.3f' % r['K'], '%.1f' % r['LR'], '%.2f' % r['CR'],
                    '%.1f' % r['dur'], r['bucket'], int(bool(r['tr'])), r['url']])


if __name__ == '__main__':
    recs = add_norm(load())
    if '--csv' in sys.argv:
        dump_csv(recs)
    else:
        n = 15
        if '--top' in sys.argv:
            n = int(sys.argv[sys.argv.index('--top') + 1])
        report(recs, n)
