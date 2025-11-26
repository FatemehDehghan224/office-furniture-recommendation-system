import time
import functools
import traceback
import httpx
from openai import (
    APIConnectionError,
    RateLimitError,
    InternalServerError,
    APIStatusError,
)
from typing import Callable, Any, Type


def retry_on_failure(
    max_retries: int = 3,
    initial_delay: float = 2.0,
    backoff_factor: float = 1.5,
    handled_exceptions: tuple[Type[BaseException], ...] = (
        APIConnectionError,
        RateLimitError,
        InternalServerError,
        APIStatusError,
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.RemoteProtocolError,
        httpx.NetworkError,
        ConnectionError,
        TimeoutError,
    ),
):

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except handled_exceptions as e:
                    print(f"⚠️ خطا در اجرای تابع {func.__name__}: {type(e).__name__} - {e}")
                    print(f"🔁 تلاش مجدد {attempt}/{max_retries} پس از تأخیر {initial_delay:.1f} ثانیه ...")
                    if attempt == max_retries:
                        print("❌ حداکثر تعداد تلاش‌ها انجام شد. تابع شکست خورد.")
                        print(traceback.format_exc())
                        return None
                    time.sleep(initial_delay * (backoff_factor ** (attempt - 1)))
                except Exception as e:
                    print(f"❌ خطای غیرمنتظره در {func.__name__}: {type(e).__name__} - {e}")
                    print(traceback.format_exc())
                    return None
        return wrapper

    return decorator
