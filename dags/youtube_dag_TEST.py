import datetime
import pendulum
import os
from tqdm import tqdm

from airflow.decorators import dag, task

import alert_deleted_video as api


@dag(
    dag_id="youtube-dag-test",
    schedule_interval=datetime.timedelta(weeks=1),
    start_date=pendulum.datetime(2023, 6, 19, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def YoutubeDAG():
    fetch_data_tasks = []
    for k, v in api.playlists.items():

        @task(task_id=f"tast_fetch_{v}")
        def get_data(k, v):
            data_path = (
                "/opt/airflow/data/playlist_backup/"
                + datetime.datetime.now().strftime("%Y-%m-%d")
                + "/"
            )

            os.makedirs(os.path.dirname(data_path), exist_ok=True)

            with open(data_path + v.strip() + ".csv", "w", encoding="utf-16") as file:
                playlist = api.get_playlist(v)
                playlist = api.clear_playlist_dic(playlist)
                file.write(k + "\n")
                file.writelines(playlist)

        fetch_data_tasks.append(get_data(k, v))

    @task
    def process_data():
        print("done")

    fetch_data_tasks >> process_data()


dag = YoutubeDAG()
