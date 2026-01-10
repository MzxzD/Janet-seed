"""
Plex Media Handler - Delegation handler for Plex Media Server integration
Provides capabilities for browsing library, querying metadata, and controlling playback
"""
from __future__ import annotations
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

from .base import (
    DelegationHandler,
    DelegationRequest,
    DelegationResult,
    HandlerCapability
)

logger = logging.getLogger(__name__)

try:
    from plexapi.server import PlexServer
    from plexapi.myplex import MyPlexAccount
    from plexapi.exceptions import NotFound, Unauthorized
    PLEXAPI_AVAILABLE = True
except ImportError:
    PLEXAPI_AVAILABLE = False
    PlexServer = None
    MyPlexAccount = None
    NotFound = None
    Unauthorized = None


class PlexDelegationHandler(DelegationHandler):
    """
    Handler for Plex Media Server integration.
    
    Capabilities:
    - search_media: Find movies/shows by title, genre, actor
    - get_recommendations: Suggest based on watch history (with consent)
    - control_playback: Play/pause/stop on Plex clients
    - fetch_library_stats: Count unwatched episodes, recent additions
    """
    
    def __init__(
        self,
        plex_server_url: Optional[str] = None,
        plex_token: Optional[str] = None,
        allow_history_tracking: bool = False
    ):
        """
        Initialize Plex handler.
        
        Args:
            plex_server_url: URL of local Plex server (e.g., "http://192.168.1.100:32400")
            plex_token: Plex authentication token
            allow_history_tracking: Whether to track watch history (requires explicit consent)
        """
        super().__init__(
            handler_id="plex_handler",
            name="Plex Media Server"
        )
        
        self.plex_server_url = plex_server_url
        self.plex_token = plex_token
        self.allow_history_tracking = allow_history_tracking
        self.plex_server = None
        self._last_error = None
        
        # Initialize Plex server connection if credentials provided
        if plex_server_url and plex_token and PLEXAPI_AVAILABLE:
            try:
                self.plex_server = PlexServer(plex_server_url, plex_token)
                logger.info(f"Plex server connected: {plex_server_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Plex server: {e}")
                self._last_error = str(e)
                self.plex_server = None
    
    def get_capabilities(self) -> List[HandlerCapability]:
        """Return list of capabilities this handler provides."""
        # Add MEDIA_CONTROL if not in enum yet
        try:
            return [HandlerCapability.MEDIA_CONTROL]
        except AttributeError:
            # Fallback to CUSTOM if MEDIA_CONTROL not defined
            return [HandlerCapability.CUSTOM]
    
    def can_handle(self, request: DelegationRequest) -> bool:
        """Check if this handler can handle the request."""
        if not self.is_available():
            return False
        
        # Check if request is for media control
        task_desc = request.task_description.lower()
        media_keywords = ["plex", "movie", "show", "tv", "episode", "play", "pause", "stop", "watch"]
        return any(keyword in task_desc for keyword in media_keywords)
    
    def handle(self, request: DelegationRequest) -> DelegationResult:
        """
        Handle the delegation request.
        
        Args:
            request: Delegation request
            
        Returns:
            Delegation result
        """
        if not self.is_available():
            return DelegationResult(
                success=False,
                output_data={},
                message="Plex server not available",
                error=self._last_error or "Plex server not configured"
            )
        
        try:
            task_desc = request.task_description.lower()
            input_data = request.input_data or {}
            
            # Route to appropriate handler method
            if "search" in task_desc or "find" in task_desc:
                return self._handle_search(request, input_data)
            elif "recommend" in task_desc or "suggest" in task_desc:
                return self._handle_recommendations(request, input_data)
            elif "play" in task_desc or "pause" in task_desc or "stop" in task_desc:
                return self._handle_playback_control(request, input_data)
            elif "stats" in task_desc or "count" in task_desc or "library" in task_desc:
                return self._handle_library_stats(request, input_data)
            else:
                return DelegationResult(
                    success=False,
                    output_data={},
                    message="Unknown Plex operation",
                    error=f"Unknown task: {task_desc}"
                )
        
        except Exception as e:
            logger.error(f"Error handling Plex request: {e}")
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Plex operation failed: {str(e)}",
                error=str(e)
            )
    
    def _handle_search(
        self,
        request: DelegationRequest,
        input_data: Dict[str, Any]
    ) -> DelegationResult:
        """Handle media search request."""
        query = input_data.get("query") or request.task_description
        media_type = input_data.get("type", "all")  # "movie", "show", "all"
        limit = input_data.get("limit", 10)
        
        try:
            results = []
            
            if media_type == "movie" or media_type == "all":
                movies = self.plex_server.library.search(title=query, libtype="movie", limit=limit)
                results.extend([{
                    "type": "movie",
                    "title": movie.title,
                    "year": movie.year,
                    "rating": movie.rating,
                    "summary": movie.summary[:200] if movie.summary else "",
                    "thumb": movie.thumb if hasattr(movie, "thumb") else None
                } for movie in movies[:limit]])
            
            if media_type == "show" or media_type == "all":
                shows = self.plex_server.library.search(title=query, libtype="show", limit=limit)
                results.extend([{
                    "type": "show",
                    "title": show.title,
                    "year": show.year,
                    "rating": show.rating,
                    "summary": show.summary[:200] if show.summary else "",
                    "thumb": show.thumb if hasattr(show, "thumb") else None
                } for show in shows[:limit]])
            
            return DelegationResult(
                success=True,
                output_data={
                    "results": results,
                    "query": query,
                    "count": len(results)
                },
                message=f"Found {len(results)} results for '{query}'",
                metadata={"operation": "search", "media_type": media_type}
            )
        
        except Exception as e:
            logger.error(f"Error searching Plex library: {e}")
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Search failed: {str(e)}",
                error=str(e)
            )
    
    def _handle_recommendations(
        self,
        request: DelegationRequest,
        input_data: Dict[str, Any]
    ) -> DelegationResult:
        """Handle recommendations request (requires consent for watch history)."""
        if not self.allow_history_tracking:
            return DelegationResult(
                success=False,
                output_data={},
                message="Recommendations require watch history tracking consent",
                error="History tracking not enabled"
            )
        
        limit = input_data.get("limit", 5)
        
        try:
            # Get recently watched items
            recently_watched = self.plex_server.library.recentlyViewed(maxresults=limit * 2)
            
            # Get recommendations based on watched content
            recommendations = []
            seen_titles = set()
            
            for item in recently_watched[:limit]:
                # Get similar items
                if hasattr(item, "related"):
                    for related in item.related():
                        if related.title not in seen_titles and len(recommendations) < limit:
                            recommendations.append({
                                "title": related.title,
                                "type": related.type,
                                "year": related.year if hasattr(related, "year") else None,
                                "summary": related.summary[:200] if related.summary else ""
                            })
                            seen_titles.add(related.title)
            
            return DelegationResult(
                success=True,
                output_data={
                    "recommendations": recommendations,
                    "count": len(recommendations),
                    "based_on": "watch_history"
                },
                message=f"Found {len(recommendations)} recommendations based on watch history",
                metadata={"operation": "recommendations", "requires_consent": True}
            )
        
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Recommendations failed: {str(e)}",
                error=str(e)
            )
    
    def _handle_playback_control(
        self,
        request: DelegationRequest,
        input_data: Dict[str, Any]
    ) -> DelegationResult:
        """Handle playback control (play/pause/stop) on Plex clients."""
        action = input_data.get("action", "play")  # "play", "pause", "stop"
        media_title = input_data.get("title")
        client_name = input_data.get("client")  # Optional client name
        
        try:
            # Find client
            clients = self.plex_server.clients()
            client = None
            
            if client_name:
                # Find specific client by name
                client = next((c for c in clients if client_name.lower() in c.name.lower()), None)
            else:
                # Use first available client
                client = clients[0] if clients else None
            
            if not client:
                return DelegationResult(
                    success=False,
                    output_data={},
                    message="No Plex clients available",
                    error="No clients found"
                )
            
            # Handle action
            if action == "play" and media_title:
                # Search for media
                media = self.plex_server.library.search(title=media_title, limit=1)
                if not media:
                    return DelegationResult(
                        success=False,
                        output_data={},
                        message=f"Media '{media_title}' not found",
                        error="Media not found"
                    )
                
                # Play on client
                client.playMedia(media[0])
                return DelegationResult(
                    success=True,
                    output_data={
                        "action": "play",
                        "media": media_title,
                        "client": client.name
                    },
                    message=f"Playing '{media_title}' on {client.name}",
                    metadata={"operation": "playback", "client": client.name}
                )
            
            elif action == "pause":
                # Pause client
                if hasattr(client, "pause"):
                    client.pause()
                return DelegationResult(
                    success=True,
                    output_data={"action": "pause", "client": client.name},
                    message=f"Paused playback on {client.name}",
                    metadata={"operation": "playback"}
                )
            
            elif action == "stop":
                # Stop client
                if hasattr(client, "stop"):
                    client.stop()
                return DelegationResult(
                    success=True,
                    output_data={"action": "stop", "client": client.name},
                    message=f"Stopped playback on {client.name}",
                    metadata={"operation": "playback"}
                )
            
            else:
                return DelegationResult(
                    success=False,
                    output_data={},
                    message=f"Unknown action: {action}",
                    error=f"Invalid action: {action}"
                )
        
        except Exception as e:
            logger.error(f"Error controlling playback: {e}")
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Playback control failed: {str(e)}",
                error=str(e)
            )
    
    def _handle_library_stats(
        self,
        request: DelegationRequest,
        input_data: Dict[str, Any]
    ) -> DelegationResult:
        """Handle library statistics request."""
        try:
            stats = {
                "movies": {"total": 0, "unwatched": 0},
                "shows": {"total": 0, "unwatched_episodes": 0},
                "recent_additions": []
            }
            
            # Count movies
            movies = self.plex_server.library.section("Movies").all()
            stats["movies"]["total"] = len(movies)
            stats["movies"]["unwatched"] = sum(1 for m in movies if m.viewCount == 0)
            
            # Count shows and episodes
            shows = self.plex_server.library.section("TV Shows").all()
            stats["shows"]["total"] = len(shows)
            unwatched_count = 0
            for show in shows:
                episodes = show.episodes()
                unwatched_count += sum(1 for e in episodes if e.viewCount == 0)
            stats["shows"]["unwatched_episodes"] = unwatched_count
            
            # Recent additions (last 10)
            recent = self.plex_server.library.recentlyAdded(maxresults=10)
            stats["recent_additions"] = [{
                "title": item.title,
                "type": item.type,
                "addedAt": str(item.addedAt) if hasattr(item, "addedAt") else None
            } for item in recent]
            
            return DelegationResult(
                success=True,
                output_data=stats,
                message=f"Library stats: {stats['movies']['total']} movies, {stats['shows']['total']} shows, {stats['shows']['unwatched_episodes']} unwatched episodes",
                metadata={"operation": "library_stats"}
            )
        
        except Exception as e:
            logger.error(f"Error fetching library stats: {e}")
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Library stats failed: {str(e)}",
                error=str(e)
            )
    
    def is_available(self) -> bool:
        """Check if handler is available and ready."""
        if not PLEXAPI_AVAILABLE:
            return False
        
        if not self.plex_server:
            return False
        
        # Test connection
        try:
            self.plex_server.library.sections()
            return True
        except Exception as e:
            self._last_error = str(e)
            return False
    
    def update_config(self, plex_server_url: Optional[str] = None, plex_token: Optional[str] = None):
        """Update Plex server configuration."""
        if plex_server_url:
            self.plex_server_url = plex_server_url
        if plex_token:
            self.plex_token = plex_token
        
        # Reconnect if both provided
        if self.plex_server_url and self.plex_token and PLEXAPI_AVAILABLE:
            try:
                self.plex_server = PlexServer(self.plex_server_url, self.plex_token)
                logger.info(f"Plex server reconnected: {self.plex_server_url}")
                self._last_error = None
            except Exception as e:
                logger.error(f"Failed to reconnect to Plex server: {e}")
                self._last_error = str(e)
                self.plex_server = None
