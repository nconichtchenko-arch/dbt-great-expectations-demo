import great_expectations as gx
import pandas as pd
import urllib.parse
from sqlalchemy import create_engine, text

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ ---
DB_USER = "dwh_user"
DB_PASSWORD = "dwh_password"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "dwh_marketplace"

password = urllib.parse.quote_plus(DB_PASSWORD)
DB_URL = f"postgresql+psycopg2://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

TABLE_NAME = "dbt_gx_demo.sales_summary"

def run_checks():
    print("🚀 Запуск Great Expectations проверок...")

    # 1. Загружаем данные из dbt-модели
    query = f"SELECT * FROM {TABLE_NAME};"
    df = pd.read_sql(query, engine)
    print(f"  📥 Загружено строк: {len(df)}")

    # 2. Создаем контекст GX
    context = gx.get_context()
    data_source = context.data_sources.add_pandas("my_pandas_source")
    data_asset = data_source.add_dataframe_asset("sales_summary_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("sales_summary_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    # 3. Создаем Suite и проверки
    suite = context.suites.add(gx.ExpectationSuite(name="sales_summary_suite"))

    # Проверка 1: order_date не должен быть NULL
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="order_date"))

    # Проверка 2: total_orders не должен быть NULL и должен быть > 0
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="total_orders"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="total_orders", min_value=1))

    # Проверка 3: total_revenue не должен быть NULL и должен быть >= 0
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="total_revenue"))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="total_revenue", min_value=0))

    # 4. Запускаем проверки
    results = batch.validate(suite)

    # 5. Выводим результат
    if results.success:
        print("  ✅ Все проверки пройдены! Данные качественные.")
    else:
        print("  ❌ Некоторые проверки не пройдены:")
        for res in results.results:
            if not res.success:
                print(f"     - {res.expectation_config.type}: {res.result}")

    return results

if __name__ == "__main__":
    run_checks()