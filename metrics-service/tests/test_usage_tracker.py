"""
Unit tests for the Usage Tracker service.
Tests endpoint usage tracking, aggregation, and Redis storage.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.usage_tracker import UsageTracker, usage_tracker
from app.models import EndpointUsageRecord, UsageStatsResponse, ServiceUsageSummary


class TestUsageTracker:
    """Tests for UsageTracker class"""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh UsageTracker instance"""
        return UsageTracker()
    
    @pytest.fixture
    def sample_record(self):
        """Create a sample usage record"""
        return EndpointUsageRecord(
            endpoint="/api/health/status",
            method="GET",
            service="health-service",
            status_code=200,
            response_time_ms=45.5,
            timestamp=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_records(self):
        """Create multiple sample usage records"""
        now = datetime.now(timezone.utc)
        return [
            EndpointUsageRecord(
                endpoint="/api/health/status",
                method="GET",
                service="health-service",
                status_code=200,
                response_time_ms=30.0,
                timestamp=now
            ),
            EndpointUsageRecord(
                endpoint="/api/health/status",
                method="GET",
                service="health-service",
                status_code=200,
                response_time_ms=50.0,
                timestamp=now
            ),
            EndpointUsageRecord(
                endpoint="/api/health/ping/192.168.1.1",
                method="GET",
                service="health-service",
                status_code=500,
                response_time_ms=100.0,
                timestamp=now
            ),
            EndpointUsageRecord(
                endpoint="/api/metrics/snapshot",
                method="GET",
                service="metrics-service",
                status_code=200,
                response_time_ms=25.0,
                timestamp=now
            ),
        ]
    
    # ==================== Local Cache Tests ====================
    
    def test_update_local_cache(self, tracker, sample_record):
        """Should update local cache correctly"""
        tracker._update_local_cache(sample_record)
        
        assert "health-service" in tracker._local_cache
        summary = tracker._local_cache["health-service"]
        assert summary.total_requests == 1
        assert summary.total_successes == 1
        assert summary.total_errors == 0
        assert summary.last_updated is not None
    
    def test_update_local_cache_counts_errors(self, tracker):
        """Should count errors correctly"""
        error_record = EndpointUsageRecord(
            endpoint="/api/health/status",
            method="GET",
            service="health-service",
            status_code=500,
            response_time_ms=100.0,
            timestamp=datetime.now(timezone.utc)
        )
        
        tracker._update_local_cache(error_record)
        
        summary = tracker._local_cache["health-service"]
        assert summary.total_errors == 1
        assert summary.total_successes == 0
    
    def test_update_local_cache_multiple_services(self, tracker, sample_records):
        """Should track multiple services separately"""
        for record in sample_records:
            tracker._update_local_cache(record)
        
        assert "health-service" in tracker._local_cache
        assert "metrics-service" in tracker._local_cache
        
        health_summary = tracker._local_cache["health-service"]
        assert health_summary.total_requests == 3
        assert health_summary.total_successes == 2
        assert health_summary.total_errors == 1
        
        metrics_summary = tracker._local_cache["metrics-service"]
        assert metrics_summary.total_requests == 1
        assert metrics_summary.total_successes == 1
    
    def test_update_local_cache_tracks_timestamps(self, tracker, sample_record):
        """Should track collection_started and last_updated"""
        assert tracker._collection_started is None
        assert tracker._last_updated is None
        
        tracker._update_local_cache(sample_record)
        
        assert tracker._collection_started is not None
        assert tracker._last_updated is not None
    
    # ==================== Endpoint Key Generation ====================
    
    def test_get_endpoint_key(self, tracker):
        """Should generate correct Redis key"""
        key = tracker._get_endpoint_key("health-service", "GET", "/api/health/status")
        assert key == "usage:health-service:GET:api_health_status"
    
    def test_get_endpoint_key_normalizes_path(self, tracker):
        """Should normalize path in key generation"""
        key = tracker._get_endpoint_key("test", "POST", "/api/test/endpoint/")
        assert key == "usage:test:POST:api_test_endpoint"
    
    # ==================== Local Stats Retrieval ====================
    
    def test_get_local_stats_all(self, tracker, sample_records):
        """Should return all local stats"""
        for record in sample_records:
            tracker._update_local_cache(record)
        
        stats = tracker._get_local_stats()
        
        assert stats.total_services == 2
        assert stats.total_requests == 4
        assert "health-service" in stats.services
        assert "metrics-service" in stats.services
    
    def test_get_local_stats_filtered(self, tracker, sample_records):
        """Should filter by service"""
        for record in sample_records:
            tracker._update_local_cache(record)
        
        stats = tracker._get_local_stats(service="health-service")
        
        assert stats.total_services == 1
        assert stats.total_requests == 3
        assert "health-service" in stats.services
        assert "metrics-service" not in stats.services
    
    def test_get_local_stats_empty(self, tracker):
        """Should handle empty cache"""
        stats = tracker._get_local_stats()
        
        assert stats.total_services == 0
        assert stats.total_requests == 0
        assert len(stats.services) == 0


class TestUsageTrackerRedisIntegration:
    """Tests for UsageTracker Redis integration"""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh UsageTracker instance"""
        return UsageTracker()
    
    @pytest.fixture
    def sample_record(self):
        """Create a sample usage record"""
        return EndpointUsageRecord(
            endpoint="/api/health/status",
            method="GET",
            service="health-service",
            status_code=200,
            response_time_ms=45.5,
            timestamp=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        mock = AsyncMock()
        mock.pipeline = MagicMock(return_value=AsyncMock())
        mock.pipeline.return_value.execute = AsyncMock(return_value=[
            1, 1, 1.0, 1, True, True, True, True, None, None, None, None, 1, 1, 1, 1.0, True, True
        ])
        mock.sismember = AsyncMock(return_value=True)
        mock.smembers = AsyncMock(return_value={b"health-service"})
        mock.hgetall = AsyncMock(return_value={
            b"total_requests": b"10",
            b"total_successes": b"8",
            b"total_errors": b"2",
            b"total_response_time_ms": b"450.0",
            b"last_updated": datetime.now(timezone.utc).isoformat().encode()
        })
        return mock
    
    async def test_record_usage_with_redis(self, tracker, sample_record, mock_redis):
        """Should record usage to Redis"""
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = mock_redis
            
            result = await tracker.record_usage(sample_record)
            
            # Should call pipeline
            mock_redis.pipeline.assert_called()
    
    async def test_record_usage_without_redis(self, tracker, sample_record):
        """Should fall back to local cache when Redis unavailable"""
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = None
            
            result = await tracker.record_usage(sample_record)
            
            assert result is False
            assert "health-service" in tracker._local_cache
    
    async def test_record_batch(self, tracker):
        """Should record multiple records"""
        records = [
            EndpointUsageRecord(
                endpoint="/api/test",
                method="GET",
                service="test-service",
                status_code=200,
                response_time_ms=20.0,
                timestamp=datetime.now(timezone.utc)
            )
            for _ in range(5)
        ]
        
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = None  # Force local only
            
            count = await tracker.record_batch(records)
            
            # All should be recorded (locally)
            assert tracker._local_cache["test-service"].total_requests == 5
    
    async def test_get_usage_stats_from_redis(self, tracker, mock_redis):
        """Should get stats from Redis"""
        mock_redis.smembers.return_value = {b"health-service"}
        mock_redis.hgetall.side_effect = [
            # Metadata
            {
                b"collection_started": datetime.now(timezone.utc).isoformat().encode(),
                b"last_updated": datetime.now(timezone.utc).isoformat().encode()
            },
            # Service summary
            {
                b"total_requests": b"100",
                b"total_successes": b"95",
                b"total_errors": b"5",
                b"total_response_time_ms": b"4500.0",
                b"last_updated": datetime.now(timezone.utc).isoformat().encode()
            },
        ]
        
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = mock_redis
            
            stats = await tracker.get_usage_stats()
            
            assert stats.total_services == 1
    
    async def test_get_usage_stats_filtered_by_service(self, tracker, mock_redis):
        """Should filter by service name"""
        mock_redis.sismember.return_value = True
        mock_redis.hgetall.side_effect = [
            # Metadata
            {},
            # Service summary
            {
                b"total_requests": b"50",
                b"total_successes": b"48",
                b"total_errors": b"2",
                b"total_response_time_ms": b"1000.0",
            }
        ]
        mock_redis.smembers.return_value = set()
        
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = mock_redis
            
            stats = await tracker.get_usage_stats(service="health-service")
            
            mock_redis.sismember.assert_called()


class TestUsageTrackerReset:
    """Tests for usage stats reset functionality"""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh UsageTracker instance"""
        tracker = UsageTracker()
        # Pre-populate with some data
        tracker._local_cache = {
            "health-service": ServiceUsageSummary(
                service="health-service",
                total_requests=100,
                total_successes=95,
                total_errors=5
            ),
            "metrics-service": ServiceUsageSummary(
                service="metrics-service",
                total_requests=50,
                total_successes=50
            )
        }
        tracker._collection_started = datetime.now(timezone.utc)
        tracker._last_updated = datetime.now(timezone.utc)
        return tracker
    
    async def test_reset_stats_all(self, tracker):
        """Should reset all stats"""
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = None
            
            result = await tracker.reset_stats()
            
            assert result is True
            assert len(tracker._local_cache) == 0
            assert tracker._collection_started is None
            assert tracker._last_updated is None
    
    async def test_reset_stats_single_service(self, tracker):
        """Should reset only specified service"""
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = None
            
            result = await tracker.reset_stats(service="health-service")
            
            assert result is True
            assert "health-service" not in tracker._local_cache
            assert "metrics-service" in tracker._local_cache
    
    async def test_reset_stats_with_redis(self, tracker):
        """Should reset Redis data"""
        mock_redis = AsyncMock()
        mock_redis.smembers = AsyncMock(return_value={b"health-service", b"metrics-service"})
        mock_redis.pipeline = MagicMock(return_value=AsyncMock())
        mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[])
        
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = mock_redis
            
            result = await tracker.reset_stats()
            
            assert result is True
            mock_redis.pipeline.assert_called()


class TestUsageTrackerErrorHandling:
    """Tests for error handling in UsageTracker"""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh UsageTracker instance"""
        return UsageTracker()
    
    @pytest.fixture
    def sample_record(self):
        """Create a sample usage record"""
        return EndpointUsageRecord(
            endpoint="/api/test",
            method="GET",
            service="test-service",
            status_code=200,
            response_time_ms=10.0,
            timestamp=datetime.now(timezone.utc)
        )
    
    async def test_record_usage_handles_redis_error(self, tracker, sample_record):
        """Should fall back to local cache on Redis error"""
        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(side_effect=Exception("Redis error"))
        
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = mock_redis
            
            result = await tracker.record_usage(sample_record)
            
            assert result is False
            # Should still update local cache
            assert "test-service" in tracker._local_cache
    
    async def test_get_usage_stats_handles_redis_error(self, tracker, sample_record):
        """Should return local stats on Redis error"""
        # Add some local data
        tracker._update_local_cache(sample_record)
        
        with patch('app.services.usage_tracker.redis_publisher') as mock_publisher:
            mock_publisher._redis = AsyncMock()
            mock_publisher._redis.hgetall = AsyncMock(side_effect=Exception("Redis error"))
            
            stats = await tracker.get_usage_stats()
            
            # Should return local stats
            assert stats.total_services == 1
            assert "test-service" in stats.services


class TestStatusCodeClassification:
    """Tests for HTTP status code classification"""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh UsageTracker instance"""
        return UsageTracker()
    
    def test_2xx_is_success(self, tracker):
        """2xx codes should be counted as success"""
        for status in [200, 201, 204, 299]:
            record = EndpointUsageRecord(
                endpoint="/api/test",
                method="GET",
                service="test-service",
                status_code=status,
                response_time_ms=10.0,
                timestamp=datetime.now(timezone.utc)
            )
            tracker._update_local_cache(record)
        
        summary = tracker._local_cache["test-service"]
        assert summary.total_successes == 4
        assert summary.total_errors == 0
    
    def test_3xx_is_success(self, tracker):
        """3xx codes should be counted as success (redirects)"""
        for status in [301, 302, 304]:
            record = EndpointUsageRecord(
                endpoint="/api/test",
                method="GET",
                service="test-service",
                status_code=status,
                response_time_ms=10.0,
                timestamp=datetime.now(timezone.utc)
            )
            tracker._update_local_cache(record)
        
        summary = tracker._local_cache["test-service"]
        assert summary.total_successes == 3
        assert summary.total_errors == 0
    
    def test_4xx_is_error(self, tracker):
        """4xx codes should be counted as errors"""
        for status in [400, 401, 403, 404, 422]:
            record = EndpointUsageRecord(
                endpoint="/api/test",
                method="GET",
                service="test-service",
                status_code=status,
                response_time_ms=10.0,
                timestamp=datetime.now(timezone.utc)
            )
            tracker._update_local_cache(record)
        
        summary = tracker._local_cache["test-service"]
        assert summary.total_successes == 0
        assert summary.total_errors == 5
    
    def test_5xx_is_error(self, tracker):
        """5xx codes should be counted as errors"""
        for status in [500, 502, 503, 504]:
            record = EndpointUsageRecord(
                endpoint="/api/test",
                method="GET",
                service="test-service",
                status_code=status,
                response_time_ms=10.0,
                timestamp=datetime.now(timezone.utc)
            )
            tracker._update_local_cache(record)
        
        summary = tracker._local_cache["test-service"]
        assert summary.total_successes == 0
        assert summary.total_errors == 4

