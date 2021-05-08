import psutil

# 현재 램 사용량을 콘솔에 프린트
def memory_usage(message: str = 'debug'):
    p = psutil.Process()
    rss = p.memory_info().rss / 2 ** 20 # Byte to MB
    print(f"[{message}] memory usage: {rss: 10.5f} MB")