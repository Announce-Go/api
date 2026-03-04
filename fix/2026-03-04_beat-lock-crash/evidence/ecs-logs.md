# ECS 로그 분석 (2026-03-03 17:02 ~ 03-04 09:06)

## 타임라인

### 17:02 - 새 컨테이너 시작 (`d4e40d0d`)

```
17:02:58 [beat]   beat: Starting...
17:02:58 [beat]   beat: Acquired lock            <-- 락 획득 성공
17:02:58 [worker] Connected to rediss://...
17:02:58 [worker] mingle: searching for neighbors
17:02:58 [worker] mingle: sync with 1 nodes      <-- 이전 컨테이너 worker와 sync
17:02:58 [worker] ready.
17:02:58 [api]    app_starting (postgresql, redis, s3)
17:02:58 [api]    Application startup complete.
```

**참고:** `LocalTime -> 2026-03-03 08:02:58` (UTC로 표시됨. KST 17:02:58)

### 17:07 - Beat 크래시

```
17:07:58 [beat] beat: Releasing lock
17:07:58 [beat] CRITICAL: beat raised exception
         <class 'redis.exceptions.LockNotOwnedError'>:
         LockNotOwnedError("Cannot extend a lock that's no longer owned")
```

**Beat 시작(17:02:58)으로부터 정확히 5분(300초) 후 = `redbeat_lock_timeout`과 동일**

스택 트레이스:
```
redbeat/schedulers.py:527 tick()
  -> self.lock.extend(int(self.lock_timeout))
redis/lock.py:302 extend()
  -> self.do_extend(additional_time, replace_ttl)
redis/lock.py:313 do_extend()
  -> raise LockNotOwnedError("Cannot extend a lock that's no longer owned")
```

### 17:10 - 이전 컨테이너 종료 (`f0ec136b`)

```
17:10:28 [api] Shutting down
17:10:28 [api] app_shutdown
17:10:28 [api] Application shutdown complete.
17:10:28 [api] Finished server process [1]
```

### 17:17 - Drift 경고

```
17:17:33 [worker] WARNING: Substantial drift from celery@SMART-TN-137s-MacBook-Pro.local
         Current drift is 32400 seconds.
         [orig: 2026-03-03 08:17:33 recv: 2026-03-03 17:17:33]
17:17:39 [worker] missed heartbeat from celery@SMART-TN-137s-MacBook-Pro.local
```

**32400초 = 9시간 = UTC와 KST 차이. 로컬 MacBook의 Celery가 프로덕션 Redis에 연결되어 있음.**

### 09:06 (다음날) - 로컬 MacBook sync

```
09:06:50 [worker] sync with celery@SMART-TN-137s-MacBook-Pro.local
```

## 핵심 발견

1. **Beat 크래시**: 시작 후 정확히 300초(lock timeout)에 크래시
2. **Beat 미복구**: 17:07 이후 beat 관련 로그 없음. Worker와 API만 살아있음
3. **1시 스케줄 미실행**: Beat가 죽어있으므로 01:00 KST 태스크가 트리거되지 않음
4. **로컬 워커 간섭**: MacBook 워커가 프로덕션 Redis에 접속 중 (9시간 drift)
