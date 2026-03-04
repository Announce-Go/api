# Redis Key 상태 (2026-03-04 기준)

배포 후 Redis에 생성된 키 목록 (DB 0, prefix: `batch:`)

## 키 목록

| 타입 | 키 | 설명 |
|------|-----|------|
| 세트 | `batch:_kombu.binding.celery` | Celery 기본 큐 바인딩 |
| 세트 | `batch:_kombu.binding.celery.pidbox` | Worker control 메시지 바인딩 |
| 세트 | `batch:_kombu.binding.celeryev` | Event 바인딩 |
| 세트 | `batch:redbeat:statics` | RedBeat 정적 스케줄 목록 |
| 정렬된 세트 | `batch:redbeat:schedule` | RedBeat 스케줄 (score = 다음 실행 시각 timestamp) |
| 해시 테이블 | `batch:redbeatcrawl-all-active-trackings` | 태스크 스케줄 정의 + 메타 |

## 주요 키 상세

### batch:redbeatcrawl-all-active-trackings (해시)

```json
{
  "definition": {
    "name": "crawl-all-active-trackings",
    "task": "app.tasks.rank_tasks.crawl_all_active_trackings",
    "schedule": {
      "__type__": "crontab",
      "minute": 0,
      "hour": 1,
      "day_of_week": "*",
      "day_of_month": "*",
      "month_of_year": "*"
    },
    "enabled": true
  },
  "meta": {
    "last_run_at": "2026-03-03T17:02:58.561183+09:00 (Asia/Seoul)"
  }
}
```

> `last_run_at`은 태스크가 실제 실행된 시각이 아니라, RedBeat가 스케줄 엔트리를 **최초 생성한 시각**(= beat 프로세스 시작 시각)이다.

### batch:redbeat:schedule (정렬된 세트)

```json
{
  "value": "batch:redbeatcrawl-all-active-trackings",
  "score": 1772553599
}
```

> `score` = 1772553599 ≈ **2026-03-04 01:00:00 KST** (= 2026-03-03 16:00:00 UTC)
> 이는 배포(17:02 KST) 이후 가장 가까운 새벽 1시를 정확히 가리키고 있다.
> **스케줄 자체는 올바르게 등록되어 있었다.**

### batch:redbeat:statics (세트)

```json
{ "value": "crawl-all-active-trackings" }
```

## 누락된 키

| 키 | 의미 |
|----|------|
| `batch:redbeat:lock` | **Beat 프로세스의 분산 락. 현재 존재하지 않음 = Beat가 죽어있음** |

## 결론

- 스케줄은 `01:00 KST`로 정확히 등록됨
- `last_run_at`은 초기화 시각(17:02)이며 태스크 실행 기록이 아님
- `redbeat:lock` 키가 없음 = Beat 프로세스가 죽어있는 상태
