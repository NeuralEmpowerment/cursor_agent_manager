#!/usr/bin/env python3
"""
Dependency Injection Container

Configures and provides all telemetry-related dependencies.
"""

from dependency_injector import containers, providers
from telemetry import (
    SQLiteTelemetryRepository,
    DefaultTelemetryService,
    DefaultAnalyticsService
)

class TelemetryContainer(containers.DeclarativeContainer):
    """Container for telemetry-related dependencies."""
    
    # Configuration
    config = providers.Configuration()
    
    # Database configuration
    database_path = providers.Object("database/telemetry.db")
    charts_directory = providers.Object("database/charts")
    
    # Repository
    telemetry_repository = providers.Singleton(
        SQLiteTelemetryRepository,
        db_path=database_path
    )
    
    # Services
    telemetry_service = providers.Factory(
        DefaultTelemetryService,
        repository=telemetry_repository
    )
    
    analytics_service = providers.Factory(
        DefaultAnalyticsService,
        repository=telemetry_repository,
        charts_dir=charts_directory
    )

def initialize_telemetry_system():
    """Initialize the telemetry system and database."""
    container = TelemetryContainer()
    repo = container.telemetry_repository()
    repo.initialize()
    return container 