"""
NekoCafé Member Service — 会员管理、认证授权、积分优惠券
"""

import json
import logging
import os
import time
from contextvars import ContextVar
from logging import Formatter, LogRecord

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
except ImportError:
    OTLPSpanExporter = None

from .database import init_db
from .routes import auth, member, points, coupon, cat, privacy

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status", "service"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint", "service"],
)


class JsonFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "service": "member-service",
            "message": record.getMessage(),
            "module": record.module,
            "traceId": trace_id_var.get(""),
        }
        if record.exc_info and record.exc_info[1]:
            log_obj["exception"] = str(record.exc_info[1])
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def setup_telemetry():
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    resource = Resource.create({SERVICE_NAME: "member-service"})
    provider = TracerProvider(resource=resource)
    if otlp_endpoint and OTLPSpanExporter:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


setup_logging()
setup_telemetry()

app = FastAPI(
    title="NekoCafé Member Service",
    description="会员管理、认证授权、积分优惠券服务",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)


@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        cur_trace_id = format(ctx.trace_id, "032x") if ctx.is_valid else ""
        trace_id_var.set(cur_trace_id)
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)
    REQUEST_COUNT.labels(
        method=method, endpoint=endpoint, status=status, service="member-service"
    ).inc()
    REQUEST_DURATION.labels(
        method=method, endpoint=endpoint, service="member-service"
    ).observe(duration)

    response.headers["X-Trace-Id"] = trace_id_var.get("")
    return response


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "healthy", "service": "member-service"}


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(REGISTRY), media_type="text/plain")


app.include_router(auth.router, prefix="/api/v1")
app.include_router(member.router, prefix="/api/v1")
app.include_router(points.router, prefix="/api/v1")
app.include_router(coupon.router, prefix="/api/v1")
app.include_router(cat.router, prefix="/api/v1")
app.include_router(privacy.router, prefix="/api/v1")
