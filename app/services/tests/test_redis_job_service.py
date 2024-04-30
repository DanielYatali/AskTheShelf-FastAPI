from time import sleep

import pytest
from unittest.mock import patch
from fakeredis.aioredis import FakeRedis
from app.services.redis_job_service import add_job, list_jobs, remove_job, MAX_JOBS_PER_USER, update_job_status
from app.app import redis


@pytest.fixture
async def fake_redis():
    fake = FakeRedis(decode_responses=True)
    await fake.flushall()
    return fake


@pytest.mark.asyncio
async def test_add_job(fake_redis):
    fake_redis = await fake_redis
    with patch('app.app.redis', fake_redis):
        user_id = 'test_user'
        job_data = {
            'job_id': 'test_job',
            'status': 'pending',
            'action': 'test_action',
        }
        # Now add_job uses the patched redis instance
        await add_job(user_id, job_data)
        job_list = await list_jobs(user_id)
        jobs = job_list['jobs']
        assert len(jobs) == 1
        assert jobs[0] == job_data  # Compare against the actual dictionary
        await remove_job(user_id, 'test_job')


@pytest.mark.asyncio
async def test_remove_job(fake_redis):
    fake_redis = await fake_redis
    with patch('app.app.redis', new=fake_redis):
        user_id = 'test'
        job_data = {
            'job_id': 'test_job',
            'status': 'pending',
            'action': 'test_action',
        }
        await add_job(user_id, job_data)
        await remove_job(user_id, 'test_job')
        job_list = await list_jobs(user_id)
        jobs = job_list['jobs']
        assert len(jobs) == 0

#integration test
@pytest.mark.asyncio
async def test_update_job_status_with_pubsub():
    user_id = 'test_user1'
    job_data = {
        'job_id': 'test_job',
        'status': 'pending',
        'action': 'test_action',
    }

    # Initialize Redis client by awaiting the fixture
    # await add_job(user_id, job_data)

    pubsub = redis.pubsub()
    # Subscribe to the user-specific updates channel
    await pubsub.subscribe(f'user_updates:{user_id}')

    # Update the job status
    job = await update_job_status(user_id, 'test_job', 'completed')
    sleep(3)
    message = await pubsub.get_message(ignore_subscribe_messages=False, timeout=1.0)
    assert message['data'].decode() == 'test_job'
    await pubsub.unsubscribe(f'user_updates:{user_id}')
    await pubsub.close()



