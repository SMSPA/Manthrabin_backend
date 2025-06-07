from manthrabin_backend import settings
import redis.asyncio as redis

redis_connection_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    max_connections=100
)
redis_client_from_pool = redis.Redis(connection_pool=redis_connection_pool)
def get_redis_client():
    return redis_client_from_pool