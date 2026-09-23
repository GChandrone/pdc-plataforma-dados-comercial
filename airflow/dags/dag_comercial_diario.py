"""DAG diária do domínio Comercial: sincroniza a configuração, extrai o ERP e aciona o job do Databricks."""

from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.sdk import dag, task


@dag(
    dag_id="dag_comercial_diario",
    description="Extração incremental do ERP simulado e carga Bronze/Silver/Gold no Databricks (Produção)",
    schedule="0 9 * * *",  # 06h no horário de Brasília (UTC-3)
    start_date=pendulum.datetime(2026, 9, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=10)},
    tags=["pdc", "comercial"],
)
def dag_comercial_diario():
    @task
    def sincronizar_configuracao() -> int:
        from pdc_extrator.cli import sincronizar_configuracao as sincronizar

        return sincronizar()

    @task
    def extrair() -> dict:
        from pdc_extrator.cli import executar_extracao

        resumo = executar_extracao()
        return {"lote": resumo["lote"], "registros": sum(i["registros"] for i in resumo["itens"])}

    executar_job = DatabricksRunNowOperator(
        task_id="executar_job_databricks",
        databricks_conn_id="databricks_default",
        job_name="job_comercial_diario",
        retries=0,
    )

    sincronizar_configuracao() >> extrair() >> executar_job


dag_comercial_diario()
