#!/bin/sh
# Авто-pull в начале сессии. Вызывается SessionStart-хуком (.claude/settings.json).
#
# Задача: подтянуть свежий main/свою ветку и НЕ засорять контекст сессии.
# Молчит, когда всё уже свежее. Говорит только когда есть что сказать:
# пришли коммиты, ветки разошлись, нет сети.
#
# Проверить руками: sh skripty/session_pull.sh

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

# ─── дата и время в контекст сессии ───────────────────────────────────
# Печатается ВСЕГДА, в отличие от остального вывода этого хука.
# Причина: ассистент не видит часов. Дату он получает один раз в системном
# контексте, и она может разойтись с реальностью — так уже было дважды.
# 28.08 сессия работала по часам, отстававшим на сутки, и весь контент-план
# уехал на день; в другой раз день недели был назван неверно, и эфир из
# субботы стал пятницей.
#
# Москва — рабочий часовой пояс команды (все эфиры «по Москве»), Рим —
# часовой пояс Виолы, он нужен при согласовании созвонов и записей.
den_nedeli=$(TZ=Europe/Moscow date '+%u' 2>/dev/null)
case "$den_nedeli" in
    1) dn=понедельник ;; 2) dn=вторник ;;    3) dn=среда ;;
    4) dn=четверг ;;     5) dn=пятница ;;    6) dn=суббота ;;
    7) dn=воскресенье ;; *) dn="" ;;
esac
if [ -n "$dn" ]; then
    echo "[дата] $(TZ=Europe/Moscow date '+%d.%m.%Y'), $dn, $(TZ=Europe/Moscow date '+%H:%M') МСК (у Виолы $(TZ=Europe/Rome date '+%H:%M'))"
else
    echo "[дата] $(date '+%d.%m.%Y %H:%M') по часам машины, часовой пояс не определён"
fi
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

export GIT_TERMINAL_PROMPT=0

vetka=$(git symbolic-ref --short -q HEAD) || {
    echo "[git] HEAD отцеплён (detached). Не тяну."
    exit 0
}

# Куда тянуть. Если у ветки есть upstream — в него. Если ветки нет на origin
# (свежая локальная) — сверяемся с main, но не сливаем.
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
if [ -n "$upstream" ]; then
    udalyonnaya=${upstream#origin/}
    slivat=1
else
    udalyonnaya=$vetka
    slivat=1
    git ls-remote --exit-code --heads origin "$vetka" >/dev/null 2>&1 || {
        udalyonnaya=main
        slivat=0
    }
fi

# --no-tags и точечный refspec: не тащим теги и чужие ветки, не печатаем
# список «[new branch] ...» в контекст сессии. --prune убирает мёртвые ссылки.
if ! git fetch --quiet --no-tags --prune origin "$udalyonnaya" 2>/dev/null; then
    echo "[git] нет связи с origin — работаю на локальной копии, в конце запушу."
    exit 0
fi

bylo=$(git rev-parse HEAD)
prishlo=$(git rev-parse FETCH_HEAD)
[ "$bylo" = "$prishlo" ] && exit 0

szadi=$(git rev-list --count "$bylo..$prishlo")
vperedi=$(git rev-list --count "$prishlo..$bylo")

if [ "$szadi" = "0" ]; then
    exit 0   # мы просто впереди origin: свои незапушенные коммиты, это норма
fi

if [ "$vperedi" != "0" ]; then
    echo "[git] расхождение с origin/$udalyonnaya: у нас $vperedi своих коммитов, там $szadi чужих."
    echo "[git] Не сливаю сам. Покажи продюсеру обе версии и спроси."
    exit 0
fi

if [ "$slivat" = "0" ]; then
    echo "[git] origin/main ушёл вперёд на $szadi коммит(ов), ветка «$vetka» ещё не на origin."
    echo "[git] Если работа новая — стоит начать её от свежего main."
    exit 0
fi

if git merge --ff-only --quiet FETCH_HEAD 2>/dev/null; then
    echo "[git] подтянул $szadi коммит(ов) из origin/$udalyonnaya:"
    git log --oneline --no-decorate "$bylo..$prishlo" | head -10
else
    echo "[git] есть $szadi новых коммитов в origin/$udalyonnaya, но ff-слияние не прошло"
    echo "[git] (скорее всего, незакоммиченные правки в рабочей копии). Разберись до работы."
fi
