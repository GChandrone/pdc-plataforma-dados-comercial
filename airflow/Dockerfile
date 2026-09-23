# Imagem do Airflow do PDC: inclui o extrator, o ERP simulado e o provider do Databricks.
ARG AIRFLOW_VERSION=3.1.0
FROM apache/airflow:${AIRFLOW_VERSION}-python3.11

ARG AIRFLOW_VERSION
COPY --chown=airflow:root extrator /opt/pdc/src/extrator
COPY --chown=airflow:root erp_simulado /opt/pdc/src/erp_simulado

RUN pip install --no-cache-dir \
      "apache-airflow==${AIRFLOW_VERSION}" \
      "apache-airflow-providers-databricks>=7.0,<8" \
      /opt/pdc/src/extrator \
      /opt/pdc/src/erp_simulado
