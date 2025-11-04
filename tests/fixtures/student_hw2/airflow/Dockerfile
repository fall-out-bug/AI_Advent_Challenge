# airflow/Dockerfile
FROM apache/airflow:2.9.3-python3.11

# 1) Системные пакеты + Java 17
USER root
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless curl procps tini ca-certificates unzip; \
    rm -rf /var/lib/apt/lists/*

# 2) Spark client
ARG SPARK_VERSION=3.5.1
ARG HADOOP_VERSION=3
RUN set -eux; \
    SPARK_TGZ="spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz"; \
    SPARK_URL="https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/${SPARK_TGZ}"; \
    curl -fL "$SPARK_URL" -o /tmp/spark.tgz; \
    tar -xzf /tmp/spark.tgz -C /opt; \
    ln -s "/opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}" /opt/spark; \
    rm -f /tmp/spark.tgz

ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV JAVA_TOOL_OPTIONS="-Dlog4j2.disable.jmx=true -Dcom.sun.management.jmxremote=false -XX:-UseContainerSupport"

# 3) JAR’ы для S3A → MinIO
ARG HADOOP_AWS_VER=3.3.4
ARG AWS_BUNDLE_VER=1.12.262
RUN set -eux; \
    curl -fL "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VER}/hadoop-aws-${HADOOP_AWS_VER}.jar" \
      -o ${SPARK_HOME}/jars/hadoop-aws-${HADOOP_AWS_VER}.jar; \
    curl -fL "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_BUNDLE_VER}/aws-java-sdk-bundle-${AWS_BUNDLE_VER}.jar" \
      -o ${SPARK_HOME}/jars/aws-java-sdk-bundle-${AWS_BUNDLE_VER}.jar

# единый Python для PySpark (и у драйвера, и у executors)
ENV PYSPARK_PYTHON=/usr/bin/python3
ENV PYSPARK_DRIVER_PYTHON=/usr/bin/python3

# 4) Устанавливаем Python-зависимости ПРАВИЛЬНО: пользователем airflow + constraints
#    (так не ругается базовый образ и минимизируются конфликты зависимостей)
ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.11
ENV AIRFLOW_CONSTRAINTS_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

USER airflow
# чтобы CLI из ~/.local/bin были видны
ENV PATH="/home/airflow/.local/bin:${PATH}"
WORKDIR /opt/airflow

COPY requirements.txt /requirements.txt
RUN python -m pip install --no-cache-dir --constraint "${AIRFLOW_CONSTRAINTS_URL}" -r /requirements.txt
