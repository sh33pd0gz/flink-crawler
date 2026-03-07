import datetime

from pyflink.common import Row, WatermarkStrategy
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.table import StreamTableEnvironment
from pyflink.common.watermark_strategy import TimestampAssigner

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

        # persist updated state
        self.state.update(current)

        # schedule the next timer 60 seconds from now
        ctx.timer_service().register_event_time_timer(
            current[2] + 60000)  # TODO parametrize this interval

    def on_timer(self, ts: int, ctx: 'KeyedProcessFunction.OnTimer'):
        # state for key that scheduled the timer
        result = self.state.value()

        # check state against record
        if ts == result[2] + 60000:  # TODO parametrize the interval
            yield result[0], result[1]


class ProcessingTimestampAssigner(TimestampAssigner):

    def __init__(self, interval: int):
        self.epoch = datetime.datetime.utcfromtimestamp(0)

    def extract_timestamp(self, value, record_timestamp) -> int:
        return int((value[0] - self.epoch).total_seconds() * 1000)


if __name__ == "__main__":
    env = StreamExecutionEnvironment.get_execution_environment()
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)

    t_env.execute_sql("""
        CREATE TABLE my_source (
            t TIMESTAMP(3),
            i VARCHAR,
            n VARCHAR,
        ) WITH (
            'connector' = 'datagen',
            'rows-per-second' = '1'
        )
    """)

    # Stream
    stream = t_env.to_append_stream(t_env.from_path(
        'my_source'), Types.ROW([Types.SQL_TIMESTAMP(), Types.STRING(), Types.STRING()]))
    # Watermark
    watermarked_stream = stream.assign_timestamps_and_watermarks(
        WatermarkStrategy.for_monotonous_timestamps()
        .with_timestamp_assigner(ProcessingTimestampAssigner())
    )
    # Process keyed stream
    result = watermarked_stream.key_by(lambda value: value[1]) \
        .process(WebScrapeOnInterval()) \
        .print()  # TODO replace with Kafka sink
    # Execute stream
    env.execute()
