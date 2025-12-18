# TODO List for Adding User Logs Schema to create_mart.py

- [x] Add the `create_user_logs_schema(conn)` function after the import statements in `src/etl_scripts/create_mart.py`.
- [x] Modify `main_create_mart()` to call `create_user_logs_schema(conn)` after `create_mart_db_schema(conn)` in the DDL creation block.
