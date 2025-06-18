#!/usr/bin/env python3
"""
Analytics Service

Provides data analysis, visualization, and reporting for telemetry data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from .models import EventType, SessionStats
from .interfaces import TelemetryRepository

class DefaultAnalyticsService:
    """Default implementation of AnalyticsService."""
    
    def __init__(self, repository: TelemetryRepository, charts_dir: str = "database/charts"):
        self.repository = repository
        self.charts_dir = charts_dir
        self._ensure_charts_directory()
    
    def _ensure_charts_directory(self):
        """Ensure the charts directory exists."""
        if not os.path.exists(self.charts_dir):
            os.makedirs(self.charts_dir, exist_ok=True)
    
    def generate_daily_report(self, date: datetime) -> Dict[str, Any]:
        """Generate a comprehensive daily analytics report."""
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        # Get basic stats
        stats = self.repository.get_session_stats(start_time, end_time)
        
        # Get all events for the day
        events = self.repository.get_events(start_time, end_time)
        
        # Calculate hourly distribution
        hourly_counts = {}
        for hour in range(24):
            hourly_counts[hour] = 0
        
        for event in events:
            hour = event.timestamp.hour
            hourly_counts[hour] += 1
        
        # Calculate detection accuracy
        total_detections = stats.total_idle_detections + stats.total_active_detections
        total_attempts = total_detections + stats.total_detection_failures
        accuracy = (total_detections / total_attempts * 100) if total_attempts > 0 else 0
        
        # Find peak activity hours
        peak_hour = max(hourly_counts.items(), key=lambda x: x[1])
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "summary": {
                "total_idle_detections": stats.total_idle_detections,
                "total_active_detections": stats.total_active_detections,
                "total_detection_failures": stats.total_detection_failures,
                "average_confidence": round(stats.average_confidence, 2),
                "detection_accuracy_percent": round(accuracy, 2),
                "session_duration_minutes": stats.session_duration_seconds // 60
            },
            "hourly_activity": hourly_counts,
            "peak_activity": {
                "hour": peak_hour[0],
                "event_count": peak_hour[1]
            },
            "event_breakdown": self._get_event_type_breakdown(events)
        }
    
    def get_detection_accuracy_trends(self, days: int = 7) -> Dict[str, List[float]]:
        """Get detection accuracy trends over time."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        daily_accuracy = []
        dates = []
        
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            stats = self.repository.get_session_stats(day_start, day_end)
            total_detections = stats.total_idle_detections + stats.total_active_detections
            total_attempts = total_detections + stats.total_detection_failures
            
            accuracy = (total_detections / total_attempts * 100) if total_attempts > 0 else 0
            daily_accuracy.append(accuracy)
            dates.append(day_start.strftime("%Y-%m-%d"))
        
        return {
            "dates": dates,
            "accuracy_percentages": daily_accuracy,
            "average_accuracy": sum(daily_accuracy) / len(daily_accuracy) if daily_accuracy else 0
        }
    
    def get_activity_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Analyze activity patterns over the specified period."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        events = self.repository.get_events(start_date, end_date)
        
        # Analyze by hour of day
        hourly_pattern = [0] * 24
        daily_pattern = [0] * 7  # Monday = 0, Sunday = 6
        
        for event in events:
            hourly_pattern[event.timestamp.hour] += 1
            daily_pattern[event.timestamp.weekday()] += 1
        
        # Find most active periods
        peak_hour = hourly_pattern.index(max(hourly_pattern))
        peak_day = daily_pattern.index(max(daily_pattern))
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            "analysis_period_days": days,
            "total_events": len(events),
            "hourly_distribution": hourly_pattern,
            "daily_distribution": daily_pattern,
            "peak_activity": {
                "hour": peak_hour,
                "day": day_names[peak_day],
                "events_at_peak_hour": hourly_pattern[peak_hour],
                "events_on_peak_day": daily_pattern[peak_day]
            },
            "activity_score": sum(hourly_pattern) / days  # Average events per day
        }
    
    def export_data_csv(self, filepath: str, 
                       start_date: datetime, 
                       end_date: datetime) -> None:
        """Export telemetry data to CSV file."""
        events = self.repository.get_events(start_date, end_date)
        
        # Convert to pandas DataFrame
        data = []
        for event in events:
            row = {
                'timestamp': event.timestamp,
                'event_type': event.event_type.value,
                'message': event.message,
                'confidence': event.confidence,
                'state': event.state,
                'detection_method': event.detection_method,
                'match_rect_x': event.match_rect_x,
                'match_rect_y': event.match_rect_y,
                'match_rect_width': event.match_rect_width,
                'match_rect_height': event.match_rect_height
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
    
    def create_visualization(self, chart_type: str, 
                           data_range: tuple = None) -> str:
        """Create data visualization and return path to saved chart."""
        if data_range:
            start_date, end_date = data_range
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if chart_type == "accuracy_trend":
            return self._create_accuracy_trend_chart(start_date, end_date, timestamp)
        elif chart_type == "activity_heatmap":
            return self._create_activity_heatmap(start_date, end_date, timestamp)
        elif chart_type == "event_distribution":
            return self._create_event_distribution_chart(start_date, end_date, timestamp)
        elif chart_type == "confidence_scatter":
            return self._create_confidence_scatter_chart(start_date, end_date, timestamp)
        else:
            raise ValueError(f"Unknown chart type: {chart_type}")
    
    def _create_accuracy_trend_chart(self, start_date: datetime, end_date: datetime, timestamp: str) -> str:
        """Create accuracy trend line chart."""
        days = (end_date - start_date).days
        trend_data = self.get_detection_accuracy_trends(days)
        
        plt.figure(figsize=(12, 6))
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in trend_data["dates"]]
        
        plt.plot(dates, trend_data["accuracy_percentages"], marker='o', linewidth=2, markersize=6)
        plt.title("Detection Accuracy Trend", fontsize=16, fontweight='bold')
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Accuracy (%)", fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.tight_layout()
        
        filename = f"accuracy_trend_{timestamp}.png"
        filepath = os.path.join(self.charts_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def _create_activity_heatmap(self, start_date: datetime, end_date: datetime, timestamp: str) -> str:
        """Create activity heatmap showing patterns by hour and day."""
        events = self.repository.get_events(start_date, end_date)
        
        # Create hourly activity matrix (7 days x 24 hours)
        activity_matrix = [[0 for _ in range(24)] for _ in range(7)]
        
        for event in events:
            day_of_week = event.timestamp.weekday()
            hour = event.timestamp.hour
            activity_matrix[day_of_week][hour] += 1
        
        plt.figure(figsize=(15, 8))
        plt.imshow(activity_matrix, cmap='YlOrRd', aspect='auto')
        plt.title("Activity Heatmap (Day vs Hour)", fontsize=16, fontweight='bold')
        plt.xlabel("Hour of Day", fontsize=12)
        plt.ylabel("Day of Week", fontsize=12)
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        plt.yticks(range(7), days)
        plt.xticks(range(0, 24, 2))
        
        plt.colorbar(label='Event Count')
        plt.tight_layout()
        
        filename = f"activity_heatmap_{timestamp}.png"
        filepath = os.path.join(self.charts_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def _create_event_distribution_chart(self, start_date: datetime, end_date: datetime, timestamp: str) -> str:
        """Create pie chart showing event type distribution."""
        events = self.repository.get_events(start_date, end_date)
        event_counts = self._get_event_type_breakdown(events)
        
        plt.figure(figsize=(10, 8))
        
        labels = list(event_counts.keys())
        sizes = list(event_counts.values())
        colors = plt.cm.Set3(range(len(labels)))
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title("Event Type Distribution", fontsize=16, fontweight='bold')
        plt.axis('equal')
        
        filename = f"event_distribution_{timestamp}.png"
        filepath = os.path.join(self.charts_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def _create_confidence_scatter_chart(self, start_date: datetime, end_date: datetime, timestamp: str) -> str:
        """Create scatter plot of confidence scores over time."""
        events = self.repository.get_events(start_date, end_date)
        
        # Filter events with confidence scores
        detection_events = [e for e in events if e.confidence is not None and 
                          e.event_type in [EventType.IDLE_DETECTION, EventType.ACTIVE_DETECTION]]
        
        if not detection_events:
            # Create empty plot
            plt.figure(figsize=(12, 6))
            plt.text(0.5, 0.5, 'No confidence data available', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=plt.gca().transAxes, fontsize=14)
            plt.title("Detection Confidence Over Time", fontsize=16, fontweight='bold')
        else:
            timestamps = [e.timestamp for e in detection_events]
            confidences = [e.confidence for e in detection_events]
            colors = ['blue' if e.event_type == EventType.IDLE_DETECTION else 'red' 
                     for e in detection_events]
            
            plt.figure(figsize=(12, 6))
            plt.scatter(timestamps, confidences, c=colors, alpha=0.6, s=50)
            plt.title("Detection Confidence Over Time", fontsize=16, fontweight='bold')
            plt.xlabel("Time", fontsize=12)
            plt.ylabel("Confidence Score", fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            
            # Add legend
            plt.scatter([], [], c='blue', alpha=0.6, s=50, label='Idle Detection')
            plt.scatter([], [], c='red', alpha=0.6, s=50, label='Active Detection')
            plt.legend()
        
        plt.tight_layout()
        
        filename = f"confidence_scatter_{timestamp}.png"
        filepath = os.path.join(self.charts_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def _get_event_type_breakdown(self, events) -> Dict[str, int]:
        """Get count of each event type."""
        breakdown = {}
        for event in events:
            event_type = event.event_type.value
            breakdown[event_type] = breakdown.get(event_type, 0) + 1
        return breakdown 