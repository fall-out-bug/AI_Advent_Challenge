#!/usr/bin/env fish
# safe-rm.fish
# Скрипт удаляет файлы/папки, перечисленные в переменной targets.
# Редактируйте список ниже — указывайте только относительные пути.
# Скрипт отбрасывает абсолютные пути и пути с ".." (безопасность).

# --- НАЧАЛО: отредактируйте список относительных путей ---
set -l targets \
    "minio/data/.minio.sys/" \
    "minio/data/features/" \
    "minio/data/mlflow-artifacts/" \
    "minio/data/movielens/" \
    "minio/data/raw/" \
    "mlflow/mlruns/" \
    "mlflow/mlartifacts/" \
    "mlflow/mlflow.db"
# --- КОНЕЦ: список путей ---

# Обработка: проверим корректность путей и соберём существующие
set -l to_delete
for p in $targets
    # Пропускаем пустые записи
    if test -z "$p"
        continue
    end

    # Запрет абсолютных путей
    if string match -q '/*' -- "$p"
        echo "Пропускаю абсолютный путь (не разрешено): $p"
        continue
    end

    # Запрет на '..' в пути
    if string match -q '*..*' -- "$p"
        echo "Пропускаю потенциально опасный путь с '..': $p"
        continue
    end

    # Нормализуем: удалим завершающий слеш у файловоподобных путей для отображения
    set -l cleanp (string replace -r '/$' '' -- "$p")

    if test -e "$p"
        echo "Будет удалено: $p"
        set to_delete $to_delete $p
    else
        echo "Не найдено (пропускаю): $p"
    end
end

if test (count $to_delete) -eq 0
    echo "Нет существующих указанных файлов/папок для удаления. Выход."
    exit 0
end

# Подтверждение
read -P "Подтвердите удаление (введите y чтобы подтвердить): " -l ans
if test "$ans" != "y" -a "$ans" != "Y"
    echo "Отмена удаления."
    exit 0
end

# Выполняем удаление
for p in $to_delete
    if test -d "$p"
        # директория
        echo "Удаляю папку: $p"
        rm -rf -- "$p"
        or begin; echo "Ошибка при удалении $p"; end
    else if test -e "$p"
        # файл или ссылка
        echo "Удаляю файл: $p"
        rm -f -- "$p"
        or begin; echo "Ошибка при удалении $p"; end
    else
        # уже отсутствует (мог исчезнуть между шагами)
        echo "Уже отсутствует: $p"
    end
end

echo "Готово."
