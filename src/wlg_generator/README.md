# WLG Profile Test Generator

> Config 기반 자동 FIO 테스트 스크립트 생성 도구 (WLG Profile 1-6)

## 📦 패키지 내용

```
wlg_generator/
├── config/
│   └── profile_1.json    # Profile 1 설정 (예시)
├── generator.py          # FIO 스크립트 자동 생성
├── orchestrator.py       # 다중 job 실행 관리
├── run_profile.sh        # 실행 스크립트
└── README.md
```

## 🎯 주요 기능

- **자동 생성**: Config 파일만 작성하면 복잡한 FIO 스크립트 자동 생성
- **다중 스레드**: Read 3개 + Write 2개 = 5개 독립 job 동시 실행
- **Throughput 제어**: FIO `rate` 파라미터로 정확한 성능 제어
- **QoS 검증**: Latency percentile 요구사항 명시

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# Linux 환경 (fio 필요)
sudo apt-get install fio  # Ubuntu/Debian
# 또는
sudo yum install fio      # RHEL/CentOS

# Python 3.7+
python3 --version
```

### 2. 테스트 스크립트 생성
```bash
cd wlg_generator

# Profile 1, 64TB 환경용 생성
python3 generator.py config/profile_1.json 64TB
```

**생성 결과:**
```
output/
├── profile1_read_4k_64TB.fio    (406 MB/s, 58%)
├── profile1_read_8k_64TB.fio    (273 MB/s, 39%)
├── profile1_read_256k_64TB.fio  (21 MB/s, 3%)
├── profile1_write_4k_64TB.fio   (64 MB/s, 65%)
└── profile1_write_40k_64TB.fio  (320 MB/s, 35%)
```

### 3. 테스트 실행
```bash
# 간편 스크립트 사용
chmod +x run_profile.sh
./run_profile.sh 1 64TB

# 또는 직접 실행
python3 orchestrator.py profile_1_64TB_jobs.txt
```

## 📊 Profile 1 예시 (64TB)

### Workload 구성
| Type | Block Size | Throughput | Percentage |
|------|-----------|------------|------------|
| Read | 4k | 406 MB/s | 58% |
| Read | 8k | 273 MB/s | 39% |
| Read | 256k | 21 MB/s | 3% |
| Write | 4k | 64 MB/s | 65% |
| Write | 40k | 320 MB/s | 35% |

**Total**: Read 700 MB/s + Write 384 MB/s  
**Power Limit**: 11W  
**Runtime**: 168 hours

### QoS 요구사항
- Read 4k/8k: p50=0.3ms, p99=0.8ms, p99.99=5ms
- Read 256k: p50=1.7ms, p99=2.8ms, p99.99=5ms

## ⚙️ Config 작성 가이드

`config/profile_X.json` 예시:

```json
{
  "profile_id": 1,
  "power_limit_watts": 11,
  "runtime_hours": 168,
  
  "read_patterns": [
    {
      "block_size": "4k",
      "percentage": 58,
      "qos_requirements": {
        "p50_ms": 0.3,
        "p99_ms": 0.8,
        "p99.99_ms": 5.0
      }
    }
  ],
  
  "write_patterns": [
    {
      "block_size": "4k",
      "percentage": 65
    }
  ],
  
  "throughput_targets": {
    "64TB": {
      "read_total_mbps": 700,
      "write_4k_mbps": 64,
      "write_40k_mbps": 320
    }
  }
}
```

## 🔧 내부 환경 적용

### 1. Mount Point 설정
Config에서 변경:
```json
"test_environment": {
  "mount_point": "/your/mount/point",
  "test_file": "testfile.dat"
}
```

### 2. Device 지정
각 생성된 .fio 파일에서 `filename` 수정 가능

### 3. Precondition
- Profile 1-3: Sustain state 권장
- Profile 4-6: 90% fill 또는 prefill로 간소화

## 📈 결과 확인

테스트 완료 후 `results/` 디렉토리에 JSON 생성:
```json
{
  "profile_id": 1,
  "duration_hours": 168,
  "jobs": {
    "profile1_read_4k_64TB": {
      "status": "success",
      "throughput_mbps": 406,
      "latency_p99_ms": 0.75
    }
  }
}
```

## ⚠️ 주의사항

### FIO 제약사항
- Read/Write 간 정확한 I/O 비율(예: 80:20)은 FIO로 직접 제어 불가
- `rate` 파라미터로 throughput 제어 → 결과적으로 스펙 충족

### 동시 실행
- 5개 job이 동시에 실행되므로 I/O 경합 발생 가능
- 실제 환경에서 throughput 미달 시 `iodepth` 조정 필요

### Profile 2-6 추가
1. `config/profile_X.json` 생성
2. Read/Write 패턴 정의 (스펙 참조)
3. Generator 실행

## 📝 개발 정보

- **개발 방식**: AI 코딩 도구 활용 (7일 → 1-2일)
- **보안**: 내부 정보 완전 추상화 (config 기반)
- **재사용**: Profile 2-6도 config만 추가하면 완료

## 🤝 기여

내부 전용 도구입니다. 이슈 발견 시 개발팀에 문의하세요.

---

**Created with AI**: 수작업 7일 → AI 활용 1-2일 완성
