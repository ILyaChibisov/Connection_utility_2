import psycopg2
import pandas as pd
from sshtunnel import SSHTunnelForwarder


def connect_to_bd(file, ip='192.168.4.16', user='sshu', passwd='q1w2e3r4', request_type=0):
    """
    Принимает параметр file: str - путь к файлу.
    Устанавливает соединение с базой данных через туннель, записывает данные из файла csv в таблицу
    public.update_connections отображает данные в таблице update_connections после записи из этой таблицы
    return result
    """
    if user == '' or passwd == '':
        user, passwd = 'sshu', 'q1w2e3r4'
    try:
        with SSHTunnelForwarder(
                (ip, 22),
                ssh_username=user,
                ssh_password=passwd,
                remote_bind_address=('127.0.0.1', 5432)) as server:
            server.start()

            params = {
                'dbname': 'fizdb2',
                'user': 'postgres',
                'password': 'ine3ss62',
                'host': '127.0.0.1',
                'port': server.local_bind_port
            }

            conn = psycopg2.connect(**params)
            curs = conn.cursor()

            # ПРОВЕРКА СТРУКТУРЫ ТАБЛИЦЫ
            if file and request_type == 0:
                curs.execute("""
                    SELECT column_name, ordinal_position 
                    FROM information_schema.columns 
                    WHERE table_name = 'update_connections' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                table_structure = curs.fetchall()
                print("DEBUG: REAL table structure of public.update_connections:")
                for col in table_structure:
                    print(f"  {col[1]}: {col[0]}")

                # Также проверим структуру через описание таблицы
                curs.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'update_connections' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                full_structure = curs.fetchall()
                print("DEBUG: Full table structure:")
                for col in full_structure:
                    print(f"  {col[0]} ({col[1]})")

            if request_type == 0:
                # Для добавления новых данных сначала очищаем таблицу
                curs.execute("DELETE FROM public.update_connections")

                if file:  # Проверяем, что файл передан
                    # Также выведем содержимое CSV для отладки (убрали лишний импорт)
                    df_check = pd.read_csv(file)
                    print(f"DEBUG: CSV file columns: {df_check.columns.tolist()}")
                    print(f"DEBUG: First row of CSV: {df_check.iloc[0].tolist() if len(df_check) > 0 else 'Empty'}")

                    sql = "COPY public.update_connections FROM STDIN DELIMITER ',' CSV HEADER"
                    curs.copy_expert(sql, open(file, "r", encoding='utf-8'))

                # Вызываем функцию обновления соединений
                curs.execute("SELECT * FROM _system.update_connections()")
                column_names = [elt[0] for elt in curs.description]
                df = pd.DataFrame(curs.fetchall(), columns=column_names)

            elif request_type == 3:
                curs.execute("SELECT * FROM _system.update_connections()")
                column_names = [elt[0] for elt in curs.description]
                df = pd.DataFrame(curs.fetchall(), columns=column_names)

            elif request_type == 1:
                curs.execute("SELECT * FROM _system.get_chunk_info()")
                column_names = [elt[0] for elt in curs.description]
                df = pd.DataFrame(curs.fetchall(), columns=column_names)

            elif request_type == 2:
                curs.execute("SELECT * FROM _system.get_connection_chunk('.*')")
                column_names = [elt[0] for elt in curs.description]
                df = pd.DataFrame(curs.fetchall(), columns=column_names)

            elif type(request_type) == list:
                curs.callproc('_system.get_connection_chunk', request_type)
                column_names = [elt[0] for elt in curs.description]
                df = pd.DataFrame(curs.fetchall(), columns=column_names)

            conn.commit()
            curs.close()
            return df
    except Exception as e:
        error = f'Нет соединения c базой данных: {str(e)}'
        print(f"DEBUG: Error in connect_to_bd: {e}")
        df = pd.DataFrame([error], columns=['Ошибка'])
        return df


if __name__ == "__main__":
    print(connect_to_bd("connection_utility.csv", '192.168.4.61', 'sshu', 'q1w2e3r4', 2).columns)