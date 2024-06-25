import logging
import time
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Define the instrumentation scope attributes
instrumentation_scope = {
    "otel.scope.name": "io.opentelemetry.contrib.mongodb",
    "otel.scope.version": "1.0.0",
    "otel.library.name": "io.opentelemetry.contrib.mongodb",  # Deprecated
    "otel.library.version": "1.0.0"  # Deprecated
}

# Initialize tracer provider and logger provider
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

logger_provider = LoggerProvider(
    resource=Resource.create(
        {
            "service.name": "shoppingcart",
            "service.instance.id": "instance-12",
        }
    ),
)
set_logger_provider(logger_provider)

exporter = OTLPLogExporter(insecure=True)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

# Attach OTLP handler to root logger
root_logger = logging.getLogger()
root_logger.addHandler(handler)

# Function to add OpenTelemetry attributes to log records
class OTLPFormatter(logging.Formatter):
    def format(self, record):
        record.__dict__.update(instrumentation_scope)
        record.__dict__["otel.status_code"] = "OK"  # Example status code
        record.__dict__["otel.status_description"] = "Operation completed successfully"  # Example status description
        record.__dict__["otel.dropped_attributes_count"] = 0
        record.__dict__["otel.dropped_events_count"] = 0
        record.__dict__["otel.dropped_links_count"] = 0
        
        # Include the trace context if available
        span = trace.get_current_span()
        if span:
            span_context = span.get_span_context()
            record.__dict__["trace_id"] = format(span_context.trace_id, "032x")
            record.__dict__["span_id"] = format(span_context.span_id, "016x")
            record.__dict__["trace_state"] = str(span_context.trace_state)
        
        return super().format(record)

# Set formatter to include OpenTelemetry attributes
for handler in root_logger.handlers:
    handler.setFormatter(OTLPFormatter())

# Function to generate logs every 3 seconds
def generate_logs():
    logger1 = logging.getLogger("myapp.area1")
    logger2 = logging.getLogger("myapp.area2")
    
    while True:
        logging.info("Jackdaws love my big sphinx of quartz.")
        logger1.debug("Quick zephyrs blow, vexing daft Jim.")
        logger1.info("How quickly daft jumping zebras vex.")
        logger2.warning("Jail zesty vixen who grabbed pay from quack.")
        logger2.error("The five boxing wizards jump quickly.")
        
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("foo"):
            logger2.error("Hyderabad, we have a major problem.")
        
        time.sleep(3)

if __name__ == "__main__":
    generate_logs()
    logger_provider.shutdown()