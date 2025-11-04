# ML System Design HW1: Получение топ-10 жанров по отзывам через PySpark (набор MovieLens)

# Базовый образ
FROM openjdk:17-slim

# Переменные среды
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Обновляем списки
RUN apt-get update

# Устанавливаем пакеты
RUN apt-get install -y procps python3 python3-pip python3-dev python3-venv wget unzip zip ca-certificates tini

# Обновляем pip
RUN pip3 install --upgrade pip

# Удаляем списки менеджера пакетов
RUN rm -rf /var/lib/apt/lists/*

# Переменные против падения Spark
ENV JAVA_TOOL_OPTIONS="-XX:-UseContainerSupport -Dlog4j2.disable.jmx=true"
ENV JDK_JAVA_OPTIONS="$JAVA_TOOL_OPTIONS"
ENV SPARK_SUBMIT_OPTS="$JAVA_TOOL_OPTIONS"

# Устанавливаем стабильный pyspark версии 3.5.1
RUN python3 -m pip install "pyspark==3.5.1"

# Рабочая директория
WORKDIR /app

# Добавляем в образ сам скрипт и entrypoint
COPY job.py /app/job.py
COPY entrypoint.sh /app/entrypoint.sh

# Выдаем права на запуск
RUN chmod +x /app/entrypoint.sh

# Инициализация для корректной обработки PID 1
ENTRYPOINT ["tini", "--", "/app/entrypoint.sh"]
