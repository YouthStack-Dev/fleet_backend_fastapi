import os
import base64
import logging
import time
import httpx
import json
from cachetools import TTLCache
from cachetools.keys import hashkey

# Constants
OAUTH2_V2_VALIDATION_URL_TEMPLATE = "{base_url}/as/introspect.oauth2?grant_type=urn:pingidentity.com:oauth2:grant_type:validate_bearer&response_type=code&token={token}"

# Environment Variables
OAUTH2_ENV = os.getenv("OAUTH2_ENV", "1").strip()
OAUTH2_BASE_URL = os.getenv("OAUTH2_BASE_URL", "").strip()
OAUTH2_VALIDATION_CLIENT_ID = os.getenv(
    "OAUTH2_VALIDATION_CLIENT_ID", ""
).strip()
OAUTH2_VALIDATION_CLIENT_SECRET = os.getenv(
    "OAUTH2_VALIDATION_CLIENT_SECRET", ""
).strip()
# Redis connection settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
USE_REDIS = os.getenv("USE_REDIS", "0").strip() == "1"


class OAuthApiAccessorError(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code


class RedisTokenManager:
    """Redis implementation for token storage"""
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(RedisTokenManager, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance
    
    def __init__(self):
        if self.__initialized:
            return
        
        try:
            import redis
            self.client = redis.Redis(
                host=REDIS_HOST, 
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD if REDIS_PASSWORD else None,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            self.available = True
            logging.info("Connected to Redis successfully")
        except ImportError:
            logging.error("Redis package not installed. Please install it with 'pip install redis'")
            self.available = False
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {str(e)}")
            self.available = False
        
        self.__initialized = True
    
    def is_available(self):
        """Check if Redis is available"""
        return self.available
    
    def store_token(self, token, data, ttl=None):
        """Store a token with its associated data in Redis"""
        if not self.available:
            return False
        
        try:
            prefix = "token:"
            key = f"{prefix}{token}"
            
            if isinstance(data, dict):
                data["active"] = True
            
            serialized_data = json.dumps(data)
            result = self.client.setex(key, int(ttl or 3600), serialized_data)
            
            logging.info(
                "Token stored in Redis: %s, TTL: %s seconds",
                token,
                ttl or 3600,
            )
            return result
        except Exception as e:
            logging.error(f"Error storing token in Redis: {str(e)}")
            return False
    
    def get_token_data(self, token):
        """Retrieve token data from Redis"""
        if not self.available:
            return None
        
        try:
            prefix = "token:"
            key = f"{prefix}{token}"
            data = self.client.get(key)
            
            if data:
                parsed_data = json.loads(data)
                if isinstance(parsed_data, dict):
                    parsed_data["source"] = "redis-cache"
                return parsed_data
            return None
        except Exception as e:
            logging.error(f"Error retrieving token from Redis: {str(e)}")
            return None
    
    def revoke_token(self, token):
        """Mark a token as revoked/inactive in Redis"""
        if not self.available:
            return False
        
        try:
            prefix = "token:"
            key = f"{prefix}{token}"
            data = self.client.get(key)
            
            if data:
                parsed_data = json.loads(data)
                if isinstance(parsed_data, dict):
                    parsed_data["active"] = False
                    ttl = self.client.ttl(key)
                    if ttl > 0:
                        self.client.setex(key, ttl, json.dumps(parsed_data))
                        return True
            return False
        except Exception as e:
            logging.error(f"Error revoking token in Redis: {str(e)}")
            return False
    
    def list_tokens(self, pattern="*", limit=100):
        """List tokens in Redis matching a pattern (caution: can be expensive with large DBs)"""
        if not self.available:
            return []
        
        try:
            results = []
            prefix = "token:"
            full_pattern = f"{prefix}{pattern}"
            
            cursor = '0'
            count = 0
            
            while cursor != 0 and count < limit:
                cursor, keys = self.client.scan(cursor=cursor, match=full_pattern, count=10)
                count += len(keys)
                
                for key in keys:
                    token = key.replace(prefix, "")
                    data = self.client.get(key)
                    ttl = self.client.ttl(key)
                    
                    if data:
                        results.append({
                            "token": token,
                            "expires_in": ttl,
                            "data": json.loads(data)
                        })
            
            return results
        except Exception as e:
            logging.error(f"Error listing tokens from Redis: {str(e)}")
            return []


class Oauth2AsAccessor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Oauth2AsAccessor, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        
        # Initialize memory cache for backward compatibility
        self.cache = TTLCache(maxsize=1000, ttl=3600)
        
        # Initialize Redis token manager
        self.redis_manager = RedisTokenManager()
        self.use_redis = USE_REDIS and self.redis_manager.is_available()
        
        if self.use_redis:
            logging.info("Using Redis for token storage")
        else:
            logging.info("Using in-memory cache for token storage")
            
        self.__initialized = True

    @classmethod
    def set_verbosity(cls, verbosity):
        logging.basicConfig(level=verbosity)
        logging.info("Logging verbosity set to: %s", verbosity)

    def validate_env_variables(self):
        if (
            not OAUTH2_ENV
            or not OAUTH2_BASE_URL
            or not OAUTH2_VALIDATION_CLIENT_ID
            or not OAUTH2_VALIDATION_CLIENT_SECRET
        ):
            raise OAuthApiAccessorError(
                "Required environment variables are not set.", 5003
            )

    @staticmethod
    def get_http_basic_auth_hash(user_name, password):
        auth_str = f"{user_name}:{password}"
        return f"Basic {base64.b64encode(auth_str.encode()).decode()}"

    @staticmethod
    def get_validation_url(oauth_token):
        base_url = OAUTH2_BASE_URL
        if not base_url:
            raise OAuthApiAccessorError(f"Base url is not set for {OAUTH2_ENV}", 5002)
        return OAUTH2_V2_VALIDATION_URL_TEMPLATE.format(
            base_url=base_url, token=oauth_token
        )

    @staticmethod
    def get_headers():
        auth_header = Oauth2AsAccessor.get_http_basic_auth_hash(
            OAUTH2_VALIDATION_CLIENT_ID, OAUTH2_VALIDATION_CLIENT_SECRET
        )
        return {
            "Authorization": auth_header,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    @staticmethod
    def handle_response(response):
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            return response.json()
        else:
            raise OAuthApiAccessorError(
                f"Validation API call failed with HTTP status code {response.status_code}",
                5001,
            )

    def store_opaque_token(self, opaque_token, data, ttl=None):
        """
        Store an opaque token mapping to its corresponding data
        
        Args:
            opaque_token: The opaque token string
            data: The data to associate with the token (typically JWT payload)
            ttl: Time to live in seconds, if None uses data["exp"] - current time
        """
        if ttl is None and isinstance(data, dict) and "exp" in data:
            ttl = data["exp"] - int(time.time())
        
        ttl = ttl or 3600  # Default 1 hour
        
        # First try Redis if available
        if self.use_redis:
            result = self.redis_manager.store_token(opaque_token, data, ttl)
            if result:
                return True
        
        # Fallback to in-memory cache or if Redis failed
        cache_key = hashkey(opaque_token)
        expiry_time = time.time() + ttl
        
        # Store token with active flag
        if isinstance(data, dict):
            data["active"] = True
        
        self.cache[cache_key] = (data, expiry_time)
        logging.info(
            "Opaque token cached in memory: %s, TTL: %s seconds",
            opaque_token,
            ttl,
        )
        return True

    def get_cached_oauth2_token(self, oauth_token):
        # First try Redis if available
        if self.use_redis:
            redis_data = self.redis_manager.get_token_data(oauth_token)
            if redis_data:
                logging.info("Token found in Redis: %s", oauth_token)
                return redis_data
        
        # Fallback to in-memory cache
        cache_key = hashkey(oauth_token)
        cached_item = self.cache.get(cache_key)
        if cached_item:
            response_data, expiry = cached_item
            if time.time() <= expiry:
                logging.info("Returning cached response for token: %s", oauth_token)
                response_data["source"] = "vsl-cache"
                return response_data
            else:
                del self.cache[cache_key]
        return None

    def validate_oauth2_token(self, oauth_token, use_cache=True):
        # Check if token is in the cache
        if use_cache:
            cached_response = self.get_cached_oauth2_token(oauth_token)
            if cached_response:
                logging.info("Cache hit")
                return cached_response

        logging.info("Cache miss")
        # Otherwise, perform a network call
        try:
            self.validate_env_variables()
            url = self.get_validation_url(oauth_token)
            headers = self.get_headers()
            response = httpx.post(url, headers=headers)
            response_data = self.handle_response(response)
            # Only cache if response is 200 and if it contains 'exp'
            if response.status_code == 200 and "exp" in response_data:
                # Calculate the expiry time based on the 'exp' field
                expiry_time = response_data["exp"]
                current_time = time.time()

                if expiry_time > current_time:
                    ttl = expiry_time - current_time
                    if use_cache:
                        # Store in Redis if available
                        if self.use_redis:
                            self.redis_manager.store_token(oauth_token, response_data, ttl)
                        
                        # Also store in memory cache for backward compatibility
                        self.cache[hashkey(oauth_token)] = (response_data, expiry_time)
                        logging.info(
                            "Response cached for token: %s, TTL: %s seconds",
                            oauth_token,
                            ttl,
                        )

            # Indicate the source is a network call
            response_data["source"] = "network-federate"
            return response_data
        except Exception as ex:
            logging.warning(
                "Error occurred in validate_oauth2_token API call: %s", str(ex)
            )
            raise

    def revoke_token(self, token):
        """Mark a token as inactive/revoked"""
        success = False
        
        # Try Redis first if available
        if self.use_redis:
            success = self.redis_manager.revoke_token(token) or success
        
        # Also try in-memory cache
        cache_key = hashkey(token)
        cached_item = self.cache.get(cache_key)
        if cached_item:
            data, expiry = cached_item
            if isinstance(data, dict):
                data["active"] = False
                self.cache[cache_key] = (data, expiry)
                success = True
        
        return success

    def list_cached_items(self):
        results = []
        
        # First get items from Redis if available
        if self.use_redis:
            redis_results = self.redis_manager.list_tokens()
            results.extend(redis_results)
        
        # Then get in-memory items
        logging.info("Listing cached items:")
        for key, (response_data, expiry_time) in self.cache.items():
            expiry_seconds = expiry_time - time.time()
            results.append({
                "token_hash": str(key),
                "expires_in": expiry_seconds,
                "data": response_data,
                "source": "memory-cache"
            })
        
        return results

