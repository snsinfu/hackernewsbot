from datetime import timedelta
from urllib.parse import urlparse
import psycopg2

def connect_to_postgres(url):
    url = urlparse(url)
    connection = psycopg2.connect(
        database=uri.path[1:],
        user=uri.username,
        password=uri.password,
        host=uri.hostname,
        port=uri.port
    )
    return connection

class StoryRepository:
    def __init__(self, url):
        self._database = connect_to_postgres(url)

    def insert_story(self, story_id, submission_time):
        with self._database.cursor() as cursor:
            cursor.execute("""
                insert into story (id) values (%(id)s) returning index;
            """, {'id': story_id})
            index, = cursor.fetchone()
            cursor.execute("""
                insert into story_submission_time values (%(index)s, %(time)s);
                insert into story_processing_status values (%(index)s, false);
            """, {'index': index, 'time': submission_time})
        self._database.commit()

    def has_story(self, story_id):
        with self._database.cursor() as cursor:
            cursor.execute("""
                select * from story where id = %(id)s;
            """, {'id': story_id})
            return cursor.fetchone() is not None

    def mark_story(self, story_id, processed=True):
        with self._database.cursor() as cursor:
            cursor.execute("""
                update story_processing_status
                       set processed = %(processed)s
                       where id = %(id)s;
            """, {'id': story_id, 'processed': processed})
        self._database.commit()

    def delete_stale_stories(self, numkept):
        with self._database.cursor() as cursor:
            cursor.execute("""
                select max(index) from story;
            """)
            highest_index, = cursor.fetchone()
            if not highest_index:
                return
            threshold = highest_index - numkept
            cursor.execute("""
                delete from story where index <= %(threshold)s;
                delete from story_submission_time where index <= %(threshold)s;
                delete from story_processing_status where index <= %(threshold)s;
            """, {'threshold': threshold})
        self._database.commit()

    def get_pending_stories(self, age=timedelta(0)):
        with self._database.cursor() as cursor:
            cursor.execute("""
                select story.id
                       from story, story_processing_status
                       where story.index = story_processing_status.index and
                             story.time <= now() - interval %(age)s and
                             not story_processing_status.processed;
            """, {'age': age})
            return [story_id for story_id, in cursor]
