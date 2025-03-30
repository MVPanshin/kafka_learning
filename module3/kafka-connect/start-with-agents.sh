#!/bin/bash

# Запуск Kafka Connect с JMX Exporter и Jolokia
export KAFKA_OPTS="-javaagent:/opt/jmx_prometheus_javaagent-0.15.0.jar=9876:/opt/kafka-connect.yml -javaagent:/opt/jolokia-jvm-1.7.2.jar=config=/opt/jolokia.properties"

exec /etc/confluent/docker/run