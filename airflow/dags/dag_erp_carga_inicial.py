"""DAG manual (sem agendamento): carga inicial do ERP simulado. Executar uma única vez."""

from __future__ import annotations

import pendulum
from airflow.sdk import dag, task


@dag(
    dag_id="dag_erp_carga_inicial",
    description="Cria cadastros e 12 meses de histórico de pedidos no ERP simulado (execução única)",
    schedule=None,
    start_date=pendulum.datetime(2026, 9, 1, tz="UTC"),
    catchup=False,
    tags=["pdc", "erp-simulado"],
)
def dag_erp_carga_inicial():
    @task
    def carga_inicial() -> dict:
        from pdc_erp.cli import executar_carga_inicial

        return executar_carga_inicial()

    carga_inicial()


dag_erp_carga_inicial()
