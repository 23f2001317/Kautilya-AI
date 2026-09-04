import asyncio
import random
import structlog
from uuid import uuid4

import os
from apps.src.core.orchestrator import orchestrator

logger = structlog.get_logger(__name__)

# Predefined autonomous anomalies
ANOMALIES = [
    {
        "title": "Autonomous Discovery: High latency on auth-service",
        "service_name": "auth-service",
        "severity": "high",
        "description": "Background scanner detected p99 latency spike."
    },
    {
        "title": "Autonomous Discovery: Memory leak in payment-processor",
        "service_name": "payment-processor",
        "severity": "critical",
        "description": "Background scanner detected continuous memory growth."
    },
    {
        "title": "Autonomous Discovery: Error rate spike in vector-db",
        "service_name": "vector-db",
        "severity": "medium",
        "description": "Vector database returning 500 internal server errors."
    }
]

async def autonomous_scan_loop():
    """
    Infinite background loop that simulates autonomous repository and telemetry scanning.
    When an issue is 'found', it automatically triggers the remediation orchestrator.
    """
    logger.info("starting_autonomous_scheduler")
    
    while True:
        # Check every 60 seconds (or 30 for testing)
        await asyncio.sleep(60)
        
        # Only run if user has provided a repo URL config
        target_repo = os.environ.get("TARGET_REPO_URL")
        if not target_repo:
            logger.debug("autonomous_scan_skipped", reason="no_target_repo_configured")
            continue
            
        logger.info("autonomous_scan_running", target=target_repo)
        
        # 10% chance to find an anomaly per tick to prevent spamming
        if random.random() < 0.2:
            anomaly = random.choice(ANOMALIES)
            logger.info("autonomous_anomaly_detected", service=anomaly["service_name"])
            
            # Automatically invoke the orchestrator (no manual trigger)
            alert_data = {
                "id": f"auto-{uuid4().hex[:6]}",
                "service_name": anomaly["service_name"],
                "title": anomaly["title"],
                "severity": anomaly["severity"],
                "source": "autonomous_scanner"
            }
            
            # Fire and forget
            asyncio.create_task(orchestrator.process_alert(alert_data))
            
