# spark/Dockerfile
FROM debian:bookworm-slim

ARG SPARK_VERSION=3.5.1
ARG HADOOP_VERSION=3
ARG HADOOP_AWS_VER=3.3.4
ARG AWS_BUNDLE_VER=1.12.262
ENV DEBIAN_FRONTEND=noninteractive

ENV SPARK_HOME=/opt/spark \
    PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH \
    JAVA_TOOL_OPTIONS="-Dlog4j2.disable.jmx=true -Dcom.sun.management.jmxremote=false -XX:-UseContainerSupport"

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates python3 python3-pip python3-venv openjdk-17-jre-headless procps tini bash; \
    ln -sf /usr/bin/python3 /usr/bin/python; \
    rm -rf /var/lib/apt/lists/*

ENV PYSPARK_PYTHON=/usr/bin/python3
ENV PYSPARK_DRIVER_PYTHON=/usr/bin/python3

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Скачиваем Spark
RUN set -eux; \
    SPARK_TGZ="spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz"; \
    SPARK_URL="https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/${SPARK_TGZ}"; \
    echo "Downloading $SPARK_URL"; \
    curl -fL "$SPARK_URL" -o /tmp/spark.tgz; \
    tar -xzf /tmp/spark.tgz -C /opt; \
    ln -s "/opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}" "$SPARK_HOME"; \
    rm -f /tmp/spark.tgz

# JAR'ы только для протокола S3A → MinIO
RUN set -eux; \
    curl -fL "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VER}/hadoop-aws-${HADOOP_AWS_VER}.jar" -o "$SPARK_HOME/jars/hadoop-aws-${HADOOP_AWS_VER}.jar"; \
    curl -fL "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_BUNDLE_VER}/aws-java-sdk-bundle-${AWS_BUNDLE_VER}.jar" -o "$SPARK_HOME/jars/aws-java-sdk-bundle-${AWS_BUNDLE_VER}.jar"

# Python deps
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Конфиги и энтрипоинт
COPY spark-defaults.conf $SPARK_HOME/conf/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 7077 8080 8081
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["/entrypoint.sh","master"]
