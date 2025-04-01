FROM python:3.11-slim AS base

WORKDIR /app

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

COPY pyproject.toml README.md LICENSE ./
COPY nim_compliance_agents/ nim_compliance_agents/

RUN pip install --no-cache-dir .

USER appuser

ENTRYPOINT ["nim-compliance"]
CMD ["--help"]
