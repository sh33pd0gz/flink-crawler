from datetime import datetime, timezone

from pyflink.common import Row, WatermarkStrategy
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.table import StreamTableEnvironment
from pyflink.common.watermark_strategy import TimestampAssigner

import cloudscraper
from bs4 import BeautifulSoup


class WebScraper:

    def __init__(self):
        self.url

    # def _get(self) -> requests.Response:
    #     # TODO spoof user-agent header
    #     data = requests.get(self.url)
    #     data.raise_for_status()
    #     return data.text
    #
    # def _parse(self, raw: str):
    #     return BeautifulSoup(raw, 'html.parser')

    def _structure(self):
        ...

    def scrape(self):
        '''
            1. Structure data
            2. Deal with dynamic pages
        '''
        # self._get()
        # self._parse()
        ...


class WebScrapeOnInterval(KeyedProcessFunction):

    def __init__(self):
        self.state = None

    def open(self, ctx: RuntimeContext):
        self.state = ctx.get_state(ValueStateDescriptor(
            "job_state", Types.PICKLED_BYTE_ARRAY()))

    def process_element(self, value, ctx: 'KeyedProcessFunction.Context'):
        # retrieve current count
        current = self.state.value()
        if current is None:
            current = Row(value.f1, 0, 0)

        # update count
        current[1] += 1

        # set state timestamp to record event time
        current[2] = ctx.timestamp()

        # state = (KEY, COUNT, EVENT_TS)

        # persist updated state
        self.state.update(current)

        # schedule the next timer 60 seconds from now
        ctx.timer_service().register_event_time_timer(
            current[2] + 1000)  # TODO parametrize this interval

    def on_timer(self, ts: int, ctx: 'KeyedProcessFunction.OnTimer'):
        # state for key that scheduled the timer
        result = self.state.value()

        # check state against record
        if ts == result[2] + 1000:  # TODO parametrize the interval
            scraper = cloudscraper.create_scraper()
            data = scraper.get("https://scores24.live/en/table-tennis/l-tt-elite-series-1").text
            soup = BeautifulSoup(data, 'html.parser')
            yield soup


class ProcessingTimestampAssigner(TimestampAssigner):

    def __init__(self):
        self.epoch = datetime.fromtimestamp(
            0, timezone.utc).replace(tzinfo=None)

    def extract_timestamp(self, value, record_timestamp) -> int:
        return int((value[0] - self.epoch).total_seconds() * 1000)


if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)

    # DataGen Table
    periodic_ddl = """
        create table periodic (
          ts TIMESTAMP(3),
          ct BIGINT
        ) with (
          'connector' = 'datagen',
          'fields.ct.kind' = 'sequence',
          'fields.ct.start' = '1',
          'fields.ct.end' = '10',
          'rows-per-second' = '1'
        )
    """
    periodic_types = Types.ROW([Types.SQL_TIMESTAMP(), Types.LONG()])
    t_env.execute_sql(periodic_ddl)

    # Stream
    stream = t_env.to_append_stream(
        t_env.from_path('periodic'), periodic_types)
    watermarked_stream = stream.assign_timestamps_and_watermarks(
        WatermarkStrategy.for_monotonous_timestamps()
        .with_timestamp_assigner(ProcessingTimestampAssigner())
    )
    watermarked_stream.key_by(lambda value: value[1]).process(
        WebScrapeOnInterval()).print()
    env.execute()
