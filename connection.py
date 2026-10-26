import psycopg2
import pandas as pd
from sshtunnel import SSHTunnelForwarder


def connect_to_bd(data=None, ip='192.168.4.16', user='sshu', passwd='q1w2e3r4', request_type=0, connection_name=None):
    """
    Устанавливает соединение с базой данных через туннель
    data: DataFrame - данные для загрузки в БД (для request_type=0)
    request_type:
        0 - загрузка данных в БД
        1 - получение информации о чанках
        2 - получение всех схем подключения
        3 - обновление соединений
        4 - поиск схемы по точному имени
    connection_name: str - название схемы подключения (для поиска)
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

            if request_type == 0 and data is not None:
                # Прямая загрузка данных в БД без временных файлов

                # Сначала удаляем ВСЕ старые записи для этой схемы подключения
                if len(data) > 0:
                    connection_types = data['connection'].unique()
                    for conn_type in connection_types:
                        curs.execute("DELETE FROM public.update_connections WHERE connection = %s", (conn_type,))

                # Вставляем новые данные (только те, что остались в таблице)
                for _, row in data.iterrows():
                    curs.execute("""
                        INSERT INTO public.update_connections 
                        (connection, chunk, position, length, io, reg_num, method, chunk_offset, is_virtual, is_compressed)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row['connection'],
                        row['chunk'],
                        row['position'],
                        row['length'],
                        row['io'],
                        row['reg_num'],
                        row['method'],
                        row['chunk_offset'],
                        row['is_virtual'],
                        row['is_compressed']
                    ))

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

            elif request_type == 4 and connection_name:
                # ТОЧНЫЙ ПОИСК ПО ИМЕНИ СХЕМЫ
                curs.execute("SELECT * FROM _system.get_connection_chunk(%s)", (connection_name,))
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
    print(connect_to_bd(None, '192.168.4.61', 'sshu', 'q1w2e3r4', 2).columns)