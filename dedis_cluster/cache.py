import functools
import logging

from django.conf import settings
from django.core.cache.backends.base import BaseCache

from .utils import load_class
from .exceptions import ConnectionInterrupted

DEDIS_CLUSTER_IGNORE_EXCEPTIONS = getattr(settings, 'DEDIS_CLUSTER_IGNORE_EXCEPTIONS', False)
DEDIS_CLUSTER_LOG_IGNORED_EXCEPTIONS = getattr(settings, 'DEDIS_CLUSTER_LOG_IGNORED_EXCEPTIONS', False)
DEDIS_CLUSTER_LOGGER = getattr(settings, 'DEDIS_CLUSTER_LOGGER', False)

if DEDIS_CLUSTER_IGNORE_EXCEPTIONS:
    logger = logging.getLogger((DEDIS_CLUSTER_LOGGER or __name__))


def omit_exception(method=None, return_value=None):
    """连接异常处理修饰器"""
    
    if method is None:
        return functools.partial(omit_exception, return_value=return_value)
    
    @functools.wraps(method)
    def _decorator(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except ConnectionInterrupted as e:
            if self._ignore_exceptions:
                if DEDIS_CLUSTER_LOG_IGNORED_EXCEPTIONS:
                    logger.error(str(e))
                    
                return return_value
            raise e
    return _decorator


class RedisClusterCache(BaseCache):
    def __init__(self, server, params):
        super(RedisClusterCache, self).__init__(params)
        self._server = server
        self._params = params
        options = params.get('OPTIONS', {})
        self._client_cls = options.get("CLIENT_CLASS", "dedis_cluster.client.DefaultClient")
        self._client_cls = load_class(self._client_cls)
        self._client = None
        self._ignore_exceptions = options.get('IGNORE_EXCEPTIONS', DEDIS_CLUSTER_IGNORE_EXCEPTIONS)

    @property
    def client(self):
        """Lazy client connection property"""
        if self._client is None:
            self._client = self._client_cls(self._server, self._params, self)
        return self._client

    @omit_exception
    def add(self, *args, **kwargs):
        return self.client.add(*args, **kwargs)

    @omit_exception
    def set(self, *args, **kwargs):
        return self.client.set(*args, **kwargs)

    @omit_exception
    def set_many(self, *args, **kwargs):
        return self.client.set_many(*args, **kwargs)
    
    @omit_exception
    def get(self, key, default=None, version=None):
        try:
            return self.client.get(key, default=default, version=version)
        except ConnectionInterrupted as e:
            if DEDIS_CLUSTER_LOG_IGNORED_EXCEPTIONS:
                logger.error(str(e))
            return default

    @omit_exception(return_value={})
    def get_many(self, *args, **kwargs):
        return self.client.get_many(*args, **kwargs)
    
    @omit_exception
    def delete(self, *args, **kwargs):
        return self.client.delete(*args, **kwargs)

    @omit_exception
    def delete_pattern(self, *args, **kwargs):
        return self.client.delete_pattern(*args, **kwargs)

    @omit_exception
    def delete_many(self, *args, **kwargs):
        return self.client.delete_many(*args, **kwargs)

    @omit_exception
    def clear(self):
        return self.client.clear()
    
    @omit_exception
    def keys(self, *args, **kwargs):
        return self.client.keys(*args, **kwargs)
    
    @omit_exception
    def has_key(self, *args, **kwargs):
        return self.client.has_key(*args, **kwargs)

    @omit_exception
    def lock(self, *args, **kwargs):
        return self.client.lock(*args, **kwargs)

    @omit_exception
    def incr_version(self, *args, **kwargs):
        return self.client.incr_version(*args, **kwargs)
    
    @omit_exception
    def incr(self, *args, **kwargs):
        return self.client.incr(*args, **kwargs)

    @omit_exception
    def decr(self, *args, **kwargs):
        return self.client.decr(*args, **kwargs)
    
    @omit_exception
    def iter_keys(self, *args, **kwargs):
        return self.client.iter_keys(*args, **kwargs)

    @omit_exception
    def ttl(self, *args, **kwargs):
        return self.client.ttl(*args, **kwargs)

    @omit_exception
    def persist(self, *args, **kwargs):
        return self.client.persist(*args, **kwargs)

    @omit_exception
    def expire(self, *args, **kwargs):
        return self.client.expire(*args, **kwargs)
