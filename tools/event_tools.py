"""
Event Tools - Live streaming event management tools.

These tools mirror BigfootLive's event management capabilities.
Each tool includes input_examples for improved accuracy (Phase 1).
"""

EVENT_TOOLS = [
    {
        "name": "create_event",
        "description": "Create a new live streaming event with title, description, scheduling, and visibility settings. Returns the created event with its unique ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Event title (max 100 characters)",
                    "maxLength": 100
                },
                "description": {
                    "type": "string",
                    "description": "Detailed event description (supports markdown)"
                },
                "scheduled_start": {
                    "type": "string",
                    "description": "Scheduled start time in ISO 8601 format (e.g., 2025-01-15T19:00:00Z)"
                },
                "scheduled_end": {
                    "type": "string",
                    "description": "Optional scheduled end time in ISO 8601 format"
                },
                "category": {
                    "type": "string",
                    "enum": ["entertainment", "education", "sports", "gaming", "music", "news", "talk_show", "other"],
                    "description": "Event category for discovery and recommendations"
                },
                "visibility": {
                    "type": "string",
                    "enum": ["public", "unlisted", "private"],
                    "default": "public",
                    "description": "Event visibility: public (discoverable), unlisted (link only), private (invite only)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for search and discovery (max 10)"
                },
                "thumbnail_url": {
                    "type": "string",
                    "description": "URL to custom thumbnail image"
                },
                "enable_chat": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable live chat during the event"
                },
                "enable_dvr": {
                    "type": "boolean",
                    "default": True,
                    "description": "Allow viewers to rewind during live stream"
                }
            },
            "required": ["title", "scheduled_start"]
        },
        "input_examples": [
            {
                "title": "Weekly Gaming Stream",
                "scheduled_start": "2025-01-15T19:00:00Z",
                "category": "gaming",
                "visibility": "public",
                "tags": ["gaming", "live", "weekly"],
                "enable_chat": True,
                "enable_dvr": True
            },
            {
                "title": "Private Team Meeting",
                "description": "Q1 planning session - internal only",
                "scheduled_start": "2025-01-20T14:00:00Z",
                "scheduled_end": "2025-01-20T15:30:00Z",
                "visibility": "private",
                "enable_chat": False
            },
            {
                "title": "Guitar Lessons Live",
                "description": "Learn blues guitar techniques with live Q&A",
                "scheduled_start": "2025-02-01T18:00:00Z",
                "category": "education",
                "visibility": "public",
                "tags": ["music", "guitar", "lessons", "blues"]
            }
        ]
    },
    {
        "name": "update_event",
        "description": "Update an existing event's details. Only provided fields will be updated.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event to update"
                },
                "title": {
                    "type": "string",
                    "description": "New event title"
                },
                "description": {
                    "type": "string",
                    "description": "New event description"
                },
                "scheduled_start": {
                    "type": "string",
                    "description": "New scheduled start time (ISO 8601)"
                },
                "scheduled_end": {
                    "type": "string",
                    "description": "New scheduled end time (ISO 8601)"
                },
                "category": {
                    "type": "string",
                    "enum": ["entertainment", "education", "sports", "gaming", "music", "news", "talk_show", "other"]
                },
                "visibility": {
                    "type": "string",
                    "enum": ["public", "unlisted", "private"]
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["event_id"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Updated Stream Title",
                "tags": ["updated", "gaming"]
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "scheduled_start": "2025-01-16T20:00:00Z",
                "visibility": "unlisted"
            }
        ]
    },
    {
        "name": "cancel_event",
        "description": "Cancel a scheduled event. Optionally notify registered viewers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event to cancel"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for cancellation (shared with viewers if notify is true)"
                },
                "notify_viewers": {
                    "type": "boolean",
                    "default": True,
                    "description": "Send cancellation notification to registered viewers"
                },
                "reschedule_to": {
                    "type": "string",
                    "description": "Optional: new datetime to suggest (ISO 8601)"
                }
            },
            "required": ["event_id"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "reason": "Technical difficulties",
                "notify_viewers": True
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "reason": "Rescheduling to next week",
                "notify_viewers": True,
                "reschedule_to": "2025-01-22T19:00:00Z"
            }
        ]
    },
    {
        "name": "list_events",
        "description": "List events with filtering and pagination options.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["scheduled", "live", "ended", "cancelled", "all"],
                    "default": "all",
                    "description": "Filter by event status"
                },
                "category": {
                    "type": "string",
                    "enum": ["entertainment", "education", "sports", "gaming", "music", "news", "talk_show", "other"],
                    "description": "Filter by category"
                },
                "visibility": {
                    "type": "string",
                    "enum": ["public", "unlisted", "private"],
                    "description": "Filter by visibility"
                },
                "start_after": {
                    "type": "string",
                    "description": "Show events starting after this datetime (ISO 8601)"
                },
                "start_before": {
                    "type": "string",
                    "description": "Show events starting before this datetime (ISO 8601)"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                    "description": "Maximum number of events to return"
                },
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0,
                    "description": "Number of events to skip for pagination"
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["scheduled_start", "created_at", "title"],
                    "default": "scheduled_start"
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "asc"
                }
            },
            "required": []
        },
        "input_examples": [
            {
                "status": "scheduled",
                "category": "gaming",
                "limit": 10
            },
            {
                "status": "live",
                "visibility": "public"
            },
            {
                "start_after": "2025-01-01T00:00:00Z",
                "start_before": "2025-01-31T23:59:59Z",
                "sort_by": "scheduled_start",
                "sort_order": "asc"
            }
        ]
    },
    {
        "name": "get_event",
        "description": "Get detailed information about a specific event including stream stats if live.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event"
                },
                "include_stats": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include viewer statistics (only available for live/ended events)"
                },
                "include_chat_summary": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include chat activity summary"
                }
            },
            "required": ["event_id"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000"
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "include_stats": True,
                "include_chat_summary": True
            }
        ]
    },
    {
        "name": "start_event",
        "description": "Start streaming for a scheduled event. Changes status to 'live' and enables viewer connections.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event to start"
                },
                "stream_key_override": {
                    "type": "string",
                    "description": "Optional: use a specific stream key instead of auto-generated"
                },
                "recording_enabled": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable VOD recording of the stream"
                },
                "low_latency_mode": {
                    "type": "boolean",
                    "default": False,
                    "description": "Enable low-latency streaming (may reduce quality)"
                }
            },
            "required": ["event_id"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "recording_enabled": True
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "low_latency_mode": True,
                "recording_enabled": False
            }
        ]
    },
    {
        "name": "stop_event",
        "description": "Stop a live stream and end the event. Finalizes VOD if recording was enabled.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event to stop"
                },
                "end_message": {
                    "type": "string",
                    "description": "Optional message to display to viewers when stream ends"
                },
                "process_vod": {
                    "type": "boolean",
                    "default": True,
                    "description": "Immediately process recording into VOD"
                },
                "generate_highlights": {
                    "type": "boolean",
                    "default": False,
                    "description": "Auto-generate highlight clips from the stream"
                }
            },
            "required": ["event_id"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "end_message": "Thanks for watching! VOD coming soon.",
                "process_vod": True
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "generate_highlights": True
            }
        ]
    },
    {
        "name": "get_stream_key",
        "description": "Get or regenerate the stream key for an event. Used by broadcasting software.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event"
                },
                "regenerate": {
                    "type": "boolean",
                    "default": False,
                    "description": "Generate a new stream key (invalidates existing)"
                }
            },
            "required": ["event_id"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000"
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "regenerate": True
            }
        ]
    },
    {
        "name": "send_event_notification",
        "description": "Send a notification to viewers registered for an event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "UUID of the event"
                },
                "message": {
                    "type": "string",
                    "description": "Notification message (max 280 characters)"
                },
                "notification_type": {
                    "type": "string",
                    "enum": ["reminder", "update", "starting_soon", "custom"],
                    "default": "custom"
                },
                "channels": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["email", "push", "sms"]
                    },
                    "default": ["push"],
                    "description": "Notification delivery channels"
                }
            },
            "required": ["event_id", "message"]
        },
        "input_examples": [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Starting in 10 minutes! Get ready!",
                "notification_type": "starting_soon",
                "channels": ["push", "email"]
            },
            {
                "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "message": "New giveaway during today's stream!",
                "notification_type": "custom",
                "channels": ["push"]
            }
        ]
    },
    {
        "name": "clone_event",
        "description": "Create a copy of an existing event with new scheduling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_event_id": {
                    "type": "string",
                    "description": "UUID of the event to clone"
                },
                "new_title": {
                    "type": "string",
                    "description": "Title for the new event (optional, defaults to 'Copy of [original]')"
                },
                "scheduled_start": {
                    "type": "string",
                    "description": "Scheduled start for the new event (ISO 8601)"
                },
                "copy_thumbnail": {
                    "type": "boolean",
                    "default": True,
                    "description": "Copy the thumbnail from source event"
                }
            },
            "required": ["source_event_id", "scheduled_start"]
        },
        "input_examples": [
            {
                "source_event_id": "550e8400-e29b-41d4-a716-446655440000",
                "scheduled_start": "2025-01-22T19:00:00Z"
            },
            {
                "source_event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "new_title": "Weekly Stream - Episode 2",
                "scheduled_start": "2025-01-29T19:00:00Z",
                "copy_thumbnail": True
            }
        ]
    }
]
