"""
Media Tools - Video and image analysis and processing tools.

These tools mirror BigfootLive's media processing capabilities.
Each tool includes input_examples for improved accuracy (Phase 1).
"""

MEDIA_TOOLS = [
    {
        "name": "analyze_media",
        "description": "Analyze video or image content for metadata, highlights, chapters, and insights. Supports various analysis types.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "UUID of the media asset to analyze"
                },
                "analysis_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["highlights", "thumbnails", "chapters", "transcript", "sentiment", "scene_detection", "face_detection", "object_detection", "audio_analysis"]
                    },
                    "description": "Types of analysis to perform"
                },
                "options": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "default": "en",
                            "description": "Language for transcript/text analysis"
                        },
                        "max_highlights": {
                            "type": "integer",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        },
                        "thumbnail_count": {
                            "type": "integer",
                            "default": 3,
                            "minimum": 1,
                            "maximum": 10
                        },
                        "min_chapter_duration": {
                            "type": "integer",
                            "default": 60,
                            "description": "Minimum chapter length in seconds"
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "default": 0.7,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Minimum confidence for detections"
                        }
                    }
                }
            },
            "required": ["media_id", "analysis_types"]
        },
        "input_examples": [
            {
                "media_id": "550e8400-e29b-41d4-a716-446655440000",
                "analysis_types": ["highlights", "chapters"],
                "options": {"max_highlights": 10}
            },
            {
                "media_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "analysis_types": ["transcript", "sentiment"],
                "options": {"language": "es"}
            },
            {
                "media_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "analysis_types": ["scene_detection", "face_detection", "object_detection"],
                "options": {"confidence_threshold": 0.85}
            }
        ]
    },
    {
        "name": "generate_thumbnail",
        "description": "Generate thumbnail images from video at specific timestamps or auto-detect best frames.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "UUID of the video asset"
                },
                "mode": {
                    "type": "string",
                    "enum": ["auto", "timestamp", "interval"],
                    "default": "auto",
                    "description": "Thumbnail generation mode"
                },
                "timestamps": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Specific timestamps in seconds (for timestamp mode)"
                },
                "interval": {
                    "type": "integer",
                    "description": "Generate thumbnail every N seconds (for interval mode)"
                },
                "count": {
                    "type": "integer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 20,
                    "description": "Number of thumbnails to generate (for auto mode)"
                },
                "size": {
                    "type": "object",
                    "properties": {
                        "width": {"type": "integer", "default": 1280},
                        "height": {"type": "integer", "default": 720}
                    }
                },
                "format": {
                    "type": "string",
                    "enum": ["jpg", "png", "webp"],
                    "default": "jpg"
                }
            },
            "required": ["media_id"]
        },
        "input_examples": [
            {
                "media_id": "550e8400-e29b-41d4-a716-446655440000",
                "mode": "auto",
                "count": 5
            },
            {
                "media_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "mode": "timestamp",
                "timestamps": [30.5, 120.0, 300.0],
                "format": "webp"
            },
            {
                "media_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "mode": "interval",
                "interval": 60,
                "size": {"width": 1920, "height": 1080}
            }
        ]
    },
    {
        "name": "extract_highlights",
        "description": "Extract highlight clips from video based on AI analysis of engaging moments.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "UUID of the source video"
                },
                "count": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                    "description": "Number of highlights to extract"
                },
                "min_duration": {
                    "type": "integer",
                    "default": 15,
                    "description": "Minimum highlight duration in seconds"
                },
                "max_duration": {
                    "type": "integer",
                    "default": 60,
                    "description": "Maximum highlight duration in seconds"
                },
                "focus": {
                    "type": "string",
                    "enum": ["engagement", "action", "audio_peaks", "chat_activity", "all"],
                    "default": "all",
                    "description": "What to optimize highlights for"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["mp4", "webm", "gif"],
                    "default": "mp4"
                },
                "include_audio": {
                    "type": "boolean",
                    "default": True
                }
            },
            "required": ["media_id"]
        },
        "input_examples": [
            {
                "media_id": "550e8400-e29b-41d4-a716-446655440000",
                "count": 10,
                "focus": "engagement"
            },
            {
                "media_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "count": 3,
                "min_duration": 5,
                "max_duration": 15,
                "output_format": "gif",
                "include_audio": False
            },
            {
                "media_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "focus": "chat_activity",
                "count": 5
            }
        ]
    },
    {
        "name": "generate_chapters",
        "description": "Auto-generate chapter markers for video based on content analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "UUID of the video"
                },
                "min_chapter_duration": {
                    "type": "integer",
                    "default": 60,
                    "description": "Minimum chapter length in seconds"
                },
                "max_chapters": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 2,
                    "maximum": 50,
                    "description": "Maximum number of chapters"
                },
                "naming_style": {
                    "type": "string",
                    "enum": ["descriptive", "topic", "numbered", "timestamp"],
                    "default": "descriptive",
                    "description": "How to name chapters"
                },
                "include_timestamps": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include timestamps in chapter titles"
                },
                "language": {
                    "type": "string",
                    "default": "en",
                    "description": "Language for chapter titles"
                }
            },
            "required": ["media_id"]
        },
        "input_examples": [
            {
                "media_id": "550e8400-e29b-41d4-a716-446655440000",
                "max_chapters": 8,
                "naming_style": "descriptive"
            },
            {
                "media_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "min_chapter_duration": 120,
                "naming_style": "topic",
                "language": "es"
            }
        ]
    },
    {
        "name": "transcribe_media",
        "description": "Generate transcript with timestamps from audio/video content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "UUID of the media asset"
                },
                "language": {
                    "type": "string",
                    "default": "auto",
                    "description": "Language code or 'auto' for detection"
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "srt", "vtt", "txt"],
                    "default": "json",
                    "description": "Output format"
                },
                "include_speaker_diarization": {
                    "type": "boolean",
                    "default": False,
                    "description": "Identify and label different speakers"
                },
                "include_word_timestamps": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include timestamps for each word"
                },
                "profanity_filter": {
                    "type": "boolean",
                    "default": False,
                    "description": "Filter profanity in transcript"
                }
            },
            "required": ["media_id"]
        },
        "input_examples": [
            {
                "media_id": "550e8400-e29b-41d4-a716-446655440000",
                "language": "en",
                "format": "srt"
            },
            {
                "media_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "language": "auto",
                "include_speaker_diarization": True,
                "format": "json"
            },
            {
                "media_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "include_word_timestamps": True,
                "format": "vtt"
            }
        ]
    },
    {
        "name": "create_clip",
        "description": "Create a clip from a specific portion of a video.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "UUID of the source video"
                },
                "start_time": {
                    "type": "number",
                    "description": "Start time in seconds"
                },
                "end_time": {
                    "type": "number",
                    "description": "End time in seconds"
                },
                "title": {
                    "type": "string",
                    "description": "Title for the clip"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["mp4", "webm", "mov"],
                    "default": "mp4"
                },
                "quality": {
                    "type": "string",
                    "enum": ["original", "1080p", "720p", "480p"],
                    "default": "original"
                },
                "add_watermark": {
                    "type": "boolean",
                    "default": False
                }
            },
            "required": ["media_id", "start_time", "end_time"]
        },
        "input_examples": [
            {
                "media_id": "550e8400-e29b-41d4-a716-446655440000",
                "start_time": 120.5,
                "end_time": 180.0,
                "title": "Epic Moment"
            },
            {
                "media_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "start_time": 0,
                "end_time": 30,
                "quality": "720p",
                "add_watermark": True
            }
        ]
    },
    {
        "name": "upload_media",
        "description": "Upload new media file and initiate processing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Media title"
                },
                "description": {
                    "type": "string",
                    "description": "Media description"
                },
                "source_url": {
                    "type": "string",
                    "description": "URL to fetch media from (alternative to direct upload)"
                },
                "content_type": {
                    "type": "string",
                    "enum": ["video", "audio", "image"],
                    "description": "Type of media being uploaded"
                },
                "visibility": {
                    "type": "string",
                    "enum": ["public", "unlisted", "private"],
                    "default": "private"
                },
                "auto_process": {
                    "type": "boolean",
                    "default": True,
                    "description": "Automatically process after upload"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["title", "content_type"]
        },
        "input_examples": [
            {
                "title": "Conference Keynote",
                "description": "Annual tech conference main presentation",
                "source_url": "https://example.com/videos/keynote.mp4",
                "content_type": "video",
                "visibility": "public",
                "tags": ["conference", "tech", "keynote"]
            },
            {
                "title": "Podcast Episode 42",
                "content_type": "audio",
                "visibility": "public",
                "auto_process": True
            }
        ]
    },
    {
        "name": "get_media_status",
        "description": "Get current processing status and metadata for a media asset.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "UUID of the media asset"
                },
                "include_processing_details": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include detailed processing job status"
                }
            },
            "required": ["media_id"]
        },
        "input_examples": [
            {
                "media_id": "550e8400-e29b-41d4-a716-446655440000"
            },
            {
                "media_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "include_processing_details": True
            }
        ]
    },
    {
        "name": "delete_media",
        "description": "Delete a media asset and all associated files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "UUID of the media asset to delete"
                },
                "delete_derivatives": {
                    "type": "boolean",
                    "default": True,
                    "description": "Also delete thumbnails, clips, and transcoded versions"
                },
                "confirm": {
                    "type": "boolean",
                    "description": "Explicit confirmation required for deletion"
                }
            },
            "required": ["media_id", "confirm"]
        },
        "input_examples": [
            {
                "media_id": "550e8400-e29b-41d4-a716-446655440000",
                "confirm": True
            },
            {
                "media_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "delete_derivatives": False,
                "confirm": True
            }
        ]
    },
    {
        "name": "list_media",
        "description": "List media assets with filtering and pagination.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content_type": {
                    "type": "string",
                    "enum": ["video", "audio", "image", "all"],
                    "default": "all"
                },
                "status": {
                    "type": "string",
                    "enum": ["processing", "ready", "failed", "all"],
                    "default": "all"
                },
                "visibility": {
                    "type": "string",
                    "enum": ["public", "unlisted", "private", "all"],
                    "default": "all"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20
                },
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["created_at", "title", "duration", "size"],
                    "default": "created_at"
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "desc"
                }
            },
            "required": []
        },
        "input_examples": [
            {
                "content_type": "video",
                "status": "ready",
                "limit": 10
            },
            {
                "visibility": "public",
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        ]
    }
]
