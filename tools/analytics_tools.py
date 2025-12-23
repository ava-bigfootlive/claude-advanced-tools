"""
Analytics Tools - Viewer analytics, predictions, and insights tools.

These tools mirror BigfootLive's analytics and AI prediction capabilities.
Each tool includes input_examples for improved accuracy (Phase 1).
"""

ANALYTICS_TOOLS = [
    {
        "name": "get_viewer_stats",
        "description": "Get viewer statistics for an event or across all events. Includes real-time and historical data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of specific event (optional, omit for aggregate stats)"
                },
                "time_range": {
                    "type": "string",
                    "enum": ["live", "last_hour", "last_24h", "last_7d", "last_30d", "all_time"],
                    "default": "last_24h",
                    "description": "Time range for statistics"
                },
                "metrics": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["viewers", "peak_viewers", "avg_watch_time", "unique_viewers", "chat_messages", "reactions", "shares", "retention_curve", "geographic_distribution", "device_breakdown"]
                    },
                    "default": ["viewers", "peak_viewers", "avg_watch_time"],
                    "description": "Specific metrics to retrieve"
                },
                "granularity": {
                    "type": "string",
                    "enum": ["minute", "hour", "day", "week"],
                    "default": "hour",
                    "description": "Data point granularity for time series"
                },
                "include_comparison": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include comparison with previous period"
                }
            },
            "required": []
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "time_range": "live",
                "metrics": ["viewers", "chat_messages", "reactions"]
            },
            {
                "time_range": "last_7d",
                "metrics": ["unique_viewers", "avg_watch_time", "retention_curve"],
                "granularity": "day",
                "include_comparison": True
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "metrics": ["geographic_distribution", "device_breakdown"],
                "time_range": "all_time"
            }
        ]
    },
    {
        "name": "predict_engagement",
        "description": "Predict viewer engagement for a scheduled event based on historical data and event characteristics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of scheduled event to predict for"
                },
                "prediction_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["peak_viewers", "total_viewers", "avg_watch_time", "chat_activity", "optimal_start_time", "revenue_estimate"]
                    },
                    "default": ["peak_viewers", "total_viewers"],
                    "description": "Types of predictions to generate"
                },
                "confidence_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                    "description": "Desired confidence level (higher = narrower prediction range)"
                },
                "include_factors": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include contributing factors in response"
                }
            },
            "required": ["event_id"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "prediction_types": ["peak_viewers", "chat_activity"],
                "include_factors": True
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "prediction_types": ["optimal_start_time", "revenue_estimate"],
                "confidence_level": "high"
            }
        ]
    },
    {
        "name": "growth_forecast",
        "description": "Generate growth forecasts for channel/platform metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["subscribers", "monthly_viewers", "watch_hours", "revenue", "engagement_rate"],
                    "description": "Metric to forecast"
                },
                "forecast_period": {
                    "type": "string",
                    "enum": ["1_week", "1_month", "3_months", "6_months", "1_year"],
                    "default": "1_month",
                    "description": "How far ahead to forecast"
                },
                "scenario": {
                    "type": "string",
                    "enum": ["conservative", "moderate", "optimistic"],
                    "default": "moderate",
                    "description": "Growth scenario assumption"
                },
                "include_milestones": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include projected milestone dates"
                }
            },
            "required": ["metric"]
        },
        "input_examples": [
            {
                "metric": "subscribers",
                "forecast_period": "3_months",
                "scenario": "moderate"
            },
            {
                "metric": "revenue",
                "forecast_period": "1_year",
                "scenario": "optimistic",
                "include_milestones": True
            }
        ]
    },
    {
        "name": "recommend_content",
        "description": "Get AI-powered content recommendations based on performance data and trends.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recommendation_type": {
                    "type": "string",
                    "enum": ["topics", "formats", "timing", "collaborations", "improvements"],
                    "description": "Type of recommendation"
                },
                "based_on": {
                    "type": "string",
                    "enum": ["performance", "audience", "trends", "competitors", "all"],
                    "default": "all",
                    "description": "Data source for recommendations"
                },
                "count": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                    "description": "Number of recommendations"
                },
                "time_range": {
                    "type": "string",
                    "enum": ["last_7d", "last_30d", "last_90d"],
                    "default": "last_30d",
                    "description": "Historical data to analyze"
                }
            },
            "required": ["recommendation_type"]
        },
        "input_examples": [
            {
                "recommendation_type": "topics",
                "based_on": "trends",
                "count": 10
            },
            {
                "recommendation_type": "timing",
                "based_on": "performance",
                "time_range": "last_90d"
            },
            {
                "recommendation_type": "improvements",
                "based_on": "audience",
                "count": 5
            }
        ]
    },
    {
        "name": "analyze_audience",
        "description": "Get detailed audience demographics and behavior analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Analyze specific event audience (optional)"
                },
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["demographics", "geography", "behavior", "interests", "loyalty", "acquisition"]
                    },
                    "default": ["demographics", "behavior"],
                    "description": "Audience segments to analyze"
                },
                "time_range": {
                    "type": "string",
                    "enum": ["last_7d", "last_30d", "last_90d", "all_time"],
                    "default": "last_30d"
                },
                "compare_to_platform": {
                    "type": "boolean",
                    "default": False,
                    "description": "Compare to platform-wide averages"
                }
            },
            "required": ["segments"]
        },
        "input_examples": [
            {
                "segments": ["demographics", "geography", "interests"],
                "time_range": "last_30d"
            },
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "segments": ["behavior", "loyalty"],
                "compare_to_platform": True
            }
        ]
    },
    {
        "name": "get_revenue_report",
        "description": "Generate revenue reports with breakdown by source.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "enum": ["today", "this_week", "this_month", "last_month", "this_year", "custom"],
                    "default": "this_month"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for custom range (ISO 8601)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for custom range (ISO 8601)"
                },
                "breakdown_by": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["source", "event", "day", "week", "product"]
                    },
                    "default": ["source"],
                    "description": "How to break down revenue"
                },
                "include_projections": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include end-of-period projections"
                },
                "currency": {
                    "type": "string",
                    "default": "USD",
                    "description": "Currency for amounts"
                }
            },
            "required": []
        },
        "input_examples": [
            {
                "time_range": "this_month",
                "breakdown_by": ["source", "event"]
            },
            {
                "time_range": "custom",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "breakdown_by": ["day"],
                "include_projections": True
            }
        ]
    },
    {
        "name": "get_retention_analysis",
        "description": "Analyze viewer retention patterns and identify drop-off points.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event to analyze"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["curve", "segments", "comparison", "recommendations"],
                    "default": "curve",
                    "description": "Type of retention analysis"
                },
                "segment_count": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 5,
                    "maximum": 100,
                    "description": "Number of segments for curve analysis"
                },
                "compare_to": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Event IDs to compare against"
                }
            },
            "required": ["event_id"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "analysis_type": "curve",
                "segment_count": 20
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "analysis_type": "comparison",
                "compare_to": ["550e8400-e29b-41d4-a716-446655440000"]
            }
        ]
    },
    {
        "name": "get_chat_analytics",
        "description": "Analyze chat activity, sentiment, and engagement patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event"
                },
                "metrics": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["message_count", "unique_chatters", "sentiment", "top_emotes", "word_cloud", "peak_activity", "engagement_rate"]
                    },
                    "default": ["message_count", "sentiment"],
                    "description": "Chat metrics to analyze"
                },
                "time_window": {
                    "type": "string",
                    "enum": ["full_event", "first_hour", "peak_period", "custom"],
                    "default": "full_event"
                },
                "include_timeline": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include time-series data"
                }
            },
            "required": ["event_id"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "metrics": ["message_count", "sentiment", "top_emotes"],
                "include_timeline": True
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "metrics": ["word_cloud", "peak_activity", "unique_chatters"],
                "time_window": "peak_period"
            }
        ]
    },
    {
        "name": "generate_marketing_copy",
        "description": "Generate AI-powered marketing copy for events or content promotion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event to generate copy for (optional)"
                },
                "copy_type": {
                    "type": "string",
                    "enum": ["social_post", "email_subject", "email_body", "notification", "description", "ad_copy"],
                    "description": "Type of marketing copy"
                },
                "platform": {
                    "type": "string",
                    "enum": ["twitter", "facebook", "instagram", "linkedin", "email", "generic"],
                    "default": "generic",
                    "description": "Target platform for optimization"
                },
                "tone": {
                    "type": "string",
                    "enum": ["professional", "casual", "exciting", "informative", "urgent"],
                    "default": "casual"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum character count"
                },
                "include_hashtags": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include relevant hashtags"
                },
                "include_emoji": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include emoji"
                },
                "variations": {
                    "type": "integer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Number of variations to generate"
                }
            },
            "required": ["copy_type"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "copy_type": "social_post",
                "platform": "twitter",
                "tone": "exciting",
                "max_length": 280,
                "variations": 3
            },
            {
                "copy_type": "email_subject",
                "tone": "urgent",
                "max_length": 50,
                "include_emoji": True,
                "variations": 5
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "copy_type": "notification",
                "tone": "casual",
                "include_hashtags": False
            }
        ]
    },
    {
        "name": "suggest_schedule",
        "description": "Get AI-powered scheduling suggestions based on audience behavior.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content_type": {
                    "type": "string",
                    "enum": ["live_stream", "premiere", "post"],
                    "default": "live_stream"
                },
                "target_audience": {
                    "type": "string",
                    "enum": ["existing", "new", "all"],
                    "default": "all",
                    "description": "Which audience to optimize for"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Expected content duration"
                },
                "preferred_days": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                    },
                    "description": "Limit suggestions to these days"
                },
                "exclude_times": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string"},
                            "end": {"type": "string"}
                        }
                    },
                    "description": "Time ranges to exclude"
                },
                "timezone": {
                    "type": "string",
                    "default": "UTC",
                    "description": "Timezone for suggestions"
                },
                "suggestion_count": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["content_type"]
        },
        "input_examples": [
            {
                "content_type": "live_stream",
                "target_audience": "existing",
                "duration_minutes": 120,
                "timezone": "America/New_York"
            },
            {
                "content_type": "premiere",
                "preferred_days": ["friday", "saturday", "sunday"],
                "suggestion_count": 3
            }
        ]
    }
]
