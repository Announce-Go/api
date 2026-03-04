# Celery Beat 장애 분석 및 해결방안

**작성일:** 2026-03-04
**증상:** 배포(3/3 17시) 후 새벽 1시 배치가 실행되지 않음

---

## 1. 증상 요약

| 항목 | 상태 |
|------|------|
| 스케줄 등록 | 정상 (`01:00 KST` crontab으로 Redis에 등록됨) |
| Beat 프로세스 | **크래시** (17:07:58, 시작 후 정확히 5분) |
| Beat 재시작 | **안됨** (컨테이너는 살아있지만 beat만 죽은 상태) |
| Worker 프로세스 | 정상 (계속 살아있음) |
| API 프로세스 | 정상 (계속 살아있음) |
| 01:00 배치 실행 | **미실행** (beat가 죽어서 트리거할 주체가 없음) |

---

## 2. 원인 분석

### 원인 1 (직접 원인): Beat 프로세스 크래시 — `LockNotOwnedError`

Beat가 17:02:58에 시작해서 17:07:58에 크래시했다. 정확히 **300초(= `redbeat_lock_timeout`)** 후.

**메커니즘:**

```
[17:02:58] Beat 시작, Redis 락 획득 (TTL 300초)
[17:02:58] tick() 호출 → 다음 태스크 실행 시각 = 01:00 KST (약 8시간 후)
           → sleep 간격 = min(다음실행까지남은시간, maxinterval) = min(~28800, 300) = 300초
[17:02:58 ~ 17:07:58] Beat가 300초 동안 sleep
[17:07:58] sleep 종료 → tick() 재호출 → self.lock.extend(300) 시도
           → 그러나 락의 TTL이 이미 만료됨 → LockNotOwnedError → Beat 크래시
```

**핵심:** `redbeat_lock_timeout`(300초)과 Celery beat의 `maxinterval`(기본값 300초)이 **동일**하다.
Beat가 300초 sleep하는 동안 락도 300초 후 만료되므로, sleep이 끝나고 extend하려 할 때 이미 락이 없다.

```python
# celery_app.py 현재 설정
redbeat_lock_timeout=300,  # 5분 - 문제!
# maxinterval은 별도 설정 없음 → 기본값 300초
```

---

## 3. "17시에 배치가 돌았나?" — 아니요

`last_run_at: 2026-03-03T17:02:58`은 **태스크 실행 시각이 아님**.

RedBeat가 스케줄 엔트리를 최초 생성할 때 `last_run_at`을 현재 시각으로 초기화한다.
이것은 "다음 실행 시각 계산의 기준점"일 뿐, 실제 태스크 실행을 의미하지 않는다.

ECS 로그에서도 17시 전후로 **태스크 실행 로그가 전혀 없다** (worker received/succeeded 등).

Redis의 `score: 1772553599` ≈ 2026-03-04 01:00:00 KST로, 스케줄은 올바르게 등록되었다.

---

## 4. 해결방안

### Fix A: `redbeat_lock_timeout`과 `maxinterval` 명시적 설정 (즉시 적용 가능)

**현재 문제:**

```
lock_timeout = 300초,  maxinterval = 300초 (기본값)

     락 획득          sleep 300초           extend 시도
        |---------------------|------------------→ ❌ 락 만료됨
        |---- 락 TTL 300초 ---|
```

`lock_timeout`을 단순히 늘리면 "지연된 크래시"가 아니라 **정상 동작**한다.
Beat는 `maxinterval`(300초)마다 깨어나서 `lock.extend()`를 호출하기 때문:

```
lock_timeout = 900초,  maxinterval = 300초

     락 획득     sleep 300초     extend 성공     sleep 300초     extend 성공
        |------------|-------------|-------------|-------------|----→ ✅ 계속 갱신
        |------------ 락 TTL 900초 ------------|
                     ↑ 잔여 600초               ↑ 잔여 600초
```

**조건: `lock_timeout` > `maxinterval` + 여유분** 이면 안전하다.
매 300초마다 깨어나서 락을 갱신하므로, 10분 후에 다시 크래시하는 것이 아니라 **영구적으로 안전**하다.

```python
# celery_app.py 수정
celery_app.conf.update(
    ...
    redbeat_lock_timeout=900,           # 15분 (maxinterval의 3배, 네트워크 지연/GC 여유분 포함)
    beat_max_loop_interval=300,         # 5분 (기본값과 동일하지만 명시적으로 고정)
)
```

---

## 5. 적용 내용

| 수정 | 효과 | 난이도 |
|------|------|--------|
| lock_timeout 900 + maxinterval 300 명시 | Beat 크래시 방지 | 2줄 수정 |

---

## 6. 참고 자료

- [evidence/redis-keys.md](evidence/redis-keys.md) — Redis 키 상태 상세
- [evidence/ecs-logs.md](evidence/ecs-logs.md) — ECS 로그 타임라인 분석
