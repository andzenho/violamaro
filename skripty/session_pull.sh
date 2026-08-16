#!/bin/sh
# Авто-pull в начале сессии. Вызывается SessionStart-хуком (.claude/settings.json).
#
# Задача: подтянуть свежий main/свою ветку и НЕ засорять контекст сессии.
# Молчит, когда всё уже свежее. Говорит только когда есть что сказать:
# пришли коммиты, ветки разошлись, нет сети.
#
# Проверить руками: sh skripty/session_pull.sh

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
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
