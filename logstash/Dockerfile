FROM docker.elastic.co/logstash/logstash:7.17.0

# WE MUST USE PAHO MQTT, the other one is broken
RUN logstash-plugin install logstash-input-paho-mqtt