"""DAG do ERP simulado: gera a movimentação diária do Protheus antes da extração."""

from __future__ import annotations

import pendulum
from airflow.sdk import dag, task


@dag(
    dag_id="dag_erp_simulador",
    description="Movimentação diária do ERP Protheus simulado (pedidos, alterações, exclusões e cadastros)",
    schedule="0 8 * * *",  # 05h no horário de Brasília, antes da dag_comercial_diario
    start_date=pendulum.datetime(2026, 9, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["pdc", "erp-simulado"],
)
def dag_erp_simulador():
    @task
    def simular_movimentacao() -> dict:
        from pdc_erp.cli import executar_simulacao

        return executar_simulacao()

    simular_movimentacao()


dag_erp_simulador()
