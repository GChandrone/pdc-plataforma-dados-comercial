import pytest


@pytest.fixture(scope="session")
def spark():
    pyspark_sql = pytest.importorskip("pyspark.sql")
    sessao = (
        pyspark_sql.SparkSession.builder.master("local[1]")
        .appName("pdc-testes")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    yield sessao
    sessao.stop()
