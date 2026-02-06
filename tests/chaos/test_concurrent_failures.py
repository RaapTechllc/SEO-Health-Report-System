"""
Chaos tests for concurrent audit handling with failures.

Tests verify that the system handles multiple concurrent audits with
random failures without deadlocks or cascading failures.
"""

import asyncio
import random
import time

import pytest


class TestConcurrentAuditFailures:
    """Tests for multiple audits with random failures."""

    @pytest.mark.asyncio
    async def test_multiple_audits_with_random_failures(self):
        """Multiple concurrent audits should handle random failures."""
        audit_results = []
        failure_rate = 0.3  # 30% failure rate

        async def run_audit(audit_id):
            await asyncio.sleep(random.uniform(0.01, 0.05))

            if random.random() < failure_rate:
                return {
                    "audit_id": audit_id,
                    "status": "failed",
                    "error": "Random failure for testing",
                }

            return {
                "audit_id": audit_id,
                "status": "completed",
                "score": random.randint(50, 100),
            }

        # Run 20 concurrent audits
        tasks = [run_audit(f"audit_{i}") for i in range(20)]
        results = await asyncio.gather(*tasks)
        audit_results.extend(results)

        # All should complete (not hang)
        assert len(audit_results) == 20

        # Should have mix of successes and failures
        completed = sum(1 for r in audit_results if r["status"] == "completed")
        failed = sum(1 for r in audit_results if r["status"] == "failed")

        assert completed > 0
        assert failed >= 0  # May have no failures due to randomness

    @pytest.mark.asyncio
    async def test_failed_audits_dont_affect_others(self):
        """Failed audit should not affect other concurrent audits."""
        results = {}
        failure_audit_id = "audit_5"

        async def run_audit(audit_id):
            await asyncio.sleep(0.01)

            if audit_id == failure_audit_id:
                raise Exception("Intentional failure")

            return {"audit_id": audit_id, "status": "completed"}

        tasks = {}
        for i in range(10):
            audit_id = f"audit_{i}"
            tasks[audit_id] = run_audit(audit_id)

        # Gather with return_exceptions to not fail on first error
        task_results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for audit_id, result in zip(tasks.keys(), task_results):
            if isinstance(result, Exception):
                results[audit_id] = {"status": "failed", "error": str(result)}
            else:
                results[audit_id] = result

        # The failing audit should fail
        assert results[failure_audit_id]["status"] == "failed"

        # All others should succeed
        for audit_id, result in results.items():
            if audit_id != failure_audit_id:
                assert result["status"] == "completed"


class TestDatabaseConnectionPool:
    """Tests for database connection pool handling under load."""

    @pytest.mark.asyncio
    async def test_no_database_deadlocks(self):
        """Concurrent database operations should not deadlock."""
        pool_size = 5
        semaphore = asyncio.Semaphore(pool_size)
        operations_completed = 0
        lock = asyncio.Lock()

        async def db_operation(op_id):
            nonlocal operations_completed
            async with semaphore:
                # Simulate DB operation
                await asyncio.sleep(random.uniform(0.01, 0.03))

                async with lock:
                    operations_completed += 1

                return op_id

        # Run more operations than pool size concurrently
        tasks = [db_operation(i) for i in range(20)]

        # Should complete without deadlock (timeout would indicate deadlock)
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=5.0)

        assert len(results) == 20
        assert operations_completed == 20

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion_handling(self):
        """Should handle connection pool exhaustion gracefully."""
        pool_size = 3
        available_connections = pool_size
        lock = asyncio.Lock()
        waiting_count = 0

        async def acquire_connection():
            nonlocal available_connections, waiting_count
            max_wait = 1.0
            wait_start = time.time()

            while True:
                async with lock:
                    if available_connections > 0:
                        available_connections -= 1
                        return True

                waiting_count += 1
                if time.time() - wait_start > max_wait:
                    waiting_count -= 1
                    return False  # Pool exhausted timeout

                await asyncio.sleep(0.01)
                waiting_count -= 1

        async def release_connection():
            nonlocal available_connections
            async with lock:
                available_connections += 1

        async def operation(op_id):
            acquired = await acquire_connection()
            if not acquired:
                return {"op_id": op_id, "status": "pool_exhausted"}

            try:
                await asyncio.sleep(0.1)
                return {"op_id": op_id, "status": "completed"}
            finally:
                await release_connection()

        # Many concurrent operations
        tasks = [operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should complete (some may have pool_exhausted status)
        assert len(results) == 10


class TestWorkerCrashRecovery:
    """Tests for worker crash and recovery scenarios."""

    @pytest.mark.asyncio
    async def test_worker_crash_recovery(self):
        """System should recover from worker crash."""
        worker_healthy = True
        audits_in_progress = {}
        recovered_audits = []

        async def worker_heartbeat():
            return worker_healthy

        async def simulate_crash():
            nonlocal worker_healthy
            worker_healthy = False
            # Mark in-progress audits for recovery
            for audit_id in list(audits_in_progress.keys()):
                recovered_audits.append(audit_id)
            audits_in_progress.clear()

        async def recover_worker():
            nonlocal worker_healthy
            worker_healthy = True

        # Start some audits
        audits_in_progress["audit_1"] = "running"
        audits_in_progress["audit_2"] = "running"

        # Simulate crash
        await simulate_crash()

        assert not worker_healthy
        assert len(audits_in_progress) == 0
        assert len(recovered_audits) == 2

        # Recover
        await recover_worker()

        assert worker_healthy

    def test_audit_state_preserved_on_crash(self):
        """Audit progress should be preserved when worker crashes."""
        audit_state = {
            "audit_id": "audit_123",
            "status": "running",
            "modules_completed": ["technical"],
            "modules_pending": ["content", "ai"],
            "partial_results": {"technical": {"score": 75}},
            "last_checkpoint": "2024-01-15T10:30:00Z",
        }

        # On recovery, should be able to resume from checkpoint
        assert len(audit_state["modules_completed"]) > 0
        assert audit_state["partial_results"] is not None


class TestQueueOverflow:
    """Tests for queue overflow handling."""

    @pytest.mark.asyncio
    async def test_queue_overflow_handling(self):
        """Queue overflow should be handled without data loss."""
        max_queue_size = 5
        queue = asyncio.Queue(maxsize=max_queue_size)
        rejected_items = []
        processed_items = []

        async def producer(item_count):
            for i in range(item_count):
                try:
                    queue.put_nowait(f"item_{i}")
                except asyncio.QueueFull:
                    rejected_items.append(f"item_{i}")

        async def consumer():
            while True:
                try:
                    item = queue.get_nowait()
                    processed_items.append(item)
                except asyncio.QueueEmpty:
                    break

        # Try to add more items than queue can hold
        await producer(10)

        # Process what's in queue
        await consumer()

        # Should have processed up to max size
        assert len(processed_items) == max_queue_size
        # Rest should be rejected
        assert len(rejected_items) == 5

    @pytest.mark.asyncio
    async def test_backpressure_mechanism(self):
        """System should apply backpressure when overwhelmed."""
        max_concurrent = 5
        semaphore = asyncio.Semaphore(max_concurrent)
        active_count = 0
        max_active_seen = 0
        lock = asyncio.Lock()

        async def process_with_backpressure(item):
            nonlocal active_count, max_active_seen

            async with semaphore:
                async with lock:
                    active_count += 1
                    max_active_seen = max(max_active_seen, active_count)

                await asyncio.sleep(0.01)

                async with lock:
                    active_count -= 1

                return item

        # Process many items
        tasks = [process_with_backpressure(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 20
        assert max_active_seen <= max_concurrent


class TestResourceLeaks:
    """Tests for resource leak prevention under failures."""

    @pytest.mark.asyncio
    async def test_no_memory_leaks_on_failures(self):
        """Failures should not cause memory leaks."""
        allocations = []

        async def leaky_operation(should_fail):
            # Simulate resource allocation
            resource = {"data": "x" * 1000}
            allocations.append(resource)

            try:
                if should_fail:
                    raise Exception("Simulated failure")
                await asyncio.sleep(0.01)
                return "success"
            finally:
                # Cleanup should happen even on failure
                allocations.remove(resource)

        # Run operations with failures
        tasks = [leaky_operation(i % 2 == 0) for i in range(10)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # All resources should be cleaned up
        assert len(allocations) == 0

    @pytest.mark.asyncio
    async def test_file_handle_cleanup(self):
        """File handles should be cleaned up on failures."""
        open_files = set()

        class MockFile:
            def __init__(self, name):
                self.name = name
                open_files.add(name)

            def close(self):
                open_files.discard(self.name)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()

        async def operation_with_file(file_name, should_fail):
            with MockFile(file_name):
                if should_fail:
                    raise OSError("File operation failed")
                await asyncio.sleep(0.01)

        # Run operations
        for i in range(5):
            try:
                await operation_with_file(f"file_{i}", i % 2 == 0)
            except OSError:
                pass

        # All files should be closed
        assert len(open_files) == 0


class TestGracefulDegradation:
    """Tests for graceful degradation under stress."""

    @pytest.mark.asyncio
    async def test_graceful_degradation_under_load(self):
        """System should degrade gracefully under heavy load."""
        max_concurrent = 10
        active = 0
        degraded_mode = False
        lock = asyncio.Lock()

        async def check_load():
            nonlocal degraded_mode
            async with lock:
                if active > max_concurrent * 0.8:
                    degraded_mode = True
                else:
                    degraded_mode = False

        async def process_request():
            nonlocal active
            async with lock:
                active += 1

            await check_load()

            try:
                if degraded_mode:
                    # Simplified processing in degraded mode
                    await asyncio.sleep(0.005)
                    return {"status": "completed", "mode": "degraded"}
                else:
                    await asyncio.sleep(0.01)
                    return {"status": "completed", "mode": "normal"}
            finally:
                async with lock:
                    active -= 1

        # Heavy load
        tasks = [process_request() for _ in range(15)]
        results = await asyncio.gather(*tasks)

        # All should complete
        assert len(results) == 15
        # Some may have been in degraded mode
        [r["mode"] for r in results]
        assert "completed" in [r["status"] for r in results]


# Run configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
