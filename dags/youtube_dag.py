import csv
import datetime
import pendulum
import os
from tqdm import tqdm
import glob

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.email import send_email

import api_functions as api


@dag(
    dag_id="youtube-playlist-backup-dag",
    schedule_interval=datetime.timedelta(weeks=1),
    start_date=pendulum.datetime(2023, 6, 19, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def YoutubeDAG():
    create_tracks_table = PostgresOperator(
        task_id="create_tracks_table",
        postgres_conn_id="main_pg_conn",
        sql="""
            CREATE TABLE IF NOT EXISTS tracks (
                "id" SERIAL PRIMARY KEY,
                "date" VARCHAR (15) NOT NULL,
                "playlist_name" TEXT NOT NULL,
                "track_pos" NUMERIC NOT NULL,
                "track_id" VARCHAR (15) NOT NULL,
                "track_name" TEXT
            );""",
    )
    run_date = datetime.datetime.now().strftime("%Y-%m-%d")
    data_path = "/opt/airflow/data/playlist_backup/" + run_date + "/"

    parallel_tasks = []
    for k, v in api.playlists.items():

        @task(task_id=f"fetch_{k}")
        def get_data(k, v):

            os.makedirs(os.path.dirname(data_path), exist_ok=True)

            HEADER = "track_pos\ttrack_id\ttrack_name"
            with open(data_path + k.strip() + ".csv", "w", encoding="utf-16") as file:
                playlist = api.get_playlist(k)
                playlist = api.clear_playlist_dic(playlist)
                file.write(HEADER + "\n")
                file.writelines(playlist)

        parallel_tasks.append(get_data(k, v))

    @task(task_id=f"save_to_db")
    def save_data():
        postgres_hook = PostgresHook(postgres_conn_id="main_pg_conn")
        conn = postgres_hook.get_conn()
        cur = conn.cursor()

        for fp in glob.glob(data_path + "PL*"):
            with open(fp, "r", encoding="utf-16") as file:
                playlist_name = api.playlists[fp.split("/")[-1].replace(".csv", "")]
                cur.copy_expert(
                    f"""ALTER TABLE tracks ALTER date SET DEFAULT '{run_date}';
                    ALTER TABLE tracks ALTER playlist_name SET DEFAULT '{playlist_name}';
                    COPY tracks(track_pos, track_id, track_name) FROM STDIN WITH CSV HEADER DELIMITER AS '\t' QUOTE E'\b';""",
                    file,
                )
            conn.commit()

    @task(task_id=f"find_deleted")
    def find_deleted_data():
        query = """
                COPY (
                    WITH 
                        new_entries as (
                            SELECT *
                            FROM tracks
                            WHERE track_name = 'DELETED_VIDEO'
                            AND Date in (SELECT DISTINCT Date FROM tracks ORDER BY Date DESC LIMIT 1 OFFSET 0)
                        ),
                        old_entries as (
                            SELECT DISTINCT date, track_pos, track_id, track_name
                            FROM tracks
                            WHERE Date in (SELECT DISTINCT Date FROM tracks ORDER BY Date DESC LIMIT 1 OFFSET 1)
                        )
                            SELECT new.date as new_date, new.playlist_name, new.track_pos as new_track_pos, new.track_id, old.date as old_date, old.track_pos as old_track_pos, old.track_name FROM new_entries AS new
                            LEFT JOIN old_entries AS old
                            ON new.track_id = old.track_id
                            WHERE old.track_name != 'DELETED_VIDEO'
                ) TO STDOUT WITH CSV HEADER DELIMITER AS '\t' QUOTE E'\b'
            ;
        """

        postgres_hook = PostgresHook(postgres_conn_id="main_pg_conn")
        conn = postgres_hook.get_conn()
        cur = conn.cursor()

        with open(data_path + "deleted.csv", "w", encoding="utf-16") as file:
            cur.copy_expert(
                query,
                file,
            )
        conn.commit()

    @task(task_id=f"send_raport")
    def send_raport():
        file_path = data_path + "deleted.csv"
        if not os.path.exists(file_path):
            print("no errors !")
            return 0

        html_content = """"""
        with open(file_path, "r", encoding="utf-16") as file:
            reader = csv.DictReader(
                file,
                delimiter="\t",
            )
            if next(reader, None) == None:
                print("no errors !")
                return 0

            for row in reader:
                subject = (
                    f"Deleted music raport for {row['old_date']} - {row['new_date']}"
                )
                html_content += "<h1>🎵" + subject + "🎵</h1>"
                break

            html_content += """<table>\n <tr> 
                            <td>playlist</td>
                            <td>title</td>
                            <td>new_track_pos</td>
                            <td>old_track_pos</td>
                    </tr>\n"""
            for row in reader:
                html_content += f"""<tr> 
                            <td>{row['playlist_name']}</td>
                            <td>{row['track_name']}</td>
                            <td>{row['new_track_pos']}</td>
                            <td>{row['old_track_pos']}</td>
                    </tr>\n"""
            html_content += "</table>\n"

        send_email(
            to=["lukaszkrupczak@gmail.com"],
            subject="⚠️ " + subject,
            html_content=html_content,
        )

    (
        create_tracks_table
        >> parallel_tasks
        >> save_data()
        >> find_deleted_data()
        >> send_raport()
    )


dag = YoutubeDAG()
