# Stage 1: Build and install dependencies
FROM python:3.13-slim as builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Stage 2: Final image
FROM python:3.13-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a non-root user
RUN addgroup --system app && adduser --system --group app

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application source
COPY src/ .

# Change ownership of the app directory
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "dts_fb_activities.app:app", "--host", "0.0.0.0", "--port", "4001"]
