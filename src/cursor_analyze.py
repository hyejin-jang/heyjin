#!/usr/bin/env python3
"""
===============================================================================
 TP Log Analyzer - CSV 데이터 자동 분석 및 이상 감지
===============================================================================
 사용법:
   python3 cursor_analyze.py --input result.csv --threshold cursor_threshold.json

 출력:
   - 콘솔에 분석 결과 출력
   - cursor_analysis_report.txt 파일 생성
   - cursor_analysis_summary.json 파일 생성 (시각화 연동용)
===============================================================================
"""

import argparse
import csv
import json
import statistics
from typing import List, Dict, Any
from datetime import datetime


def load_csv(path: str) -> List[Dict[str, Any]]:
    """CSV 파일 로드"""
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 숫자 변환
            converted = {}
            for k, v in row.items():
                try:
                    if '.' in str(v):
                        converted[k] = float(v)
                    else:
                        converted[k] = int(v)
                except (ValueError, TypeError):
                    converted[k] = v
            data.append(converted)
    return data


def load_threshold(path: str) -> Dict:
    """임계값 설정 로드"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 기본 임계값 사용
        return get_default_thresholds()


def get_default_thresholds() -> Dict:
    """기본 임계값 (내부에서 수정 가능)"""
    return {
        "gc_tokens": {
            "critical_min": 3,
            "warning_min": 5,
            "description": "GC Token이 이 값 이하면 경고"
        },
        "int_write_buf": {
            "critical_max": 58,
            "warning_max": 50,
            "description": "Internal Write Buffer가 이 값 이상이면 경고"
        },
        "fcore_runtime_us": {
            "critical_max": 900,
            "warning_max": 700,
            "description": "FCore 런타임이 이 값 이상이면 경고"
        },
        "qcc_count": {
            "spike_threshold_sigma": 2.0,
            "description": "평균 대비 N 시그마 이상이면 스파이크로 판단"
        }
    }


def calculate_stats(data: List[Dict], field: str) -> Dict:
    """특정 필드의 통계 계산"""
    values = [row.get(field, 0) for row in data if row.get(field) is not None]
    
    if not values:
        return {"error": "No data"}
    
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "avg": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
        "p95": round(sorted(values)[int(len(values) * 0.95)], 2),
        "p99": round(sorted(values)[int(len(values) * 0.99)], 2),
    }


def detect_anomalies(data: List[Dict], thresholds: Dict) -> List[Dict]:
    """이상 패턴 감지"""
    anomalies = []
    
    # 필드별 통계 계산
    stats_cache = {}
    for field in thresholds.keys():
        if any(field in row for row in data):
            stats_cache[field] = calculate_stats(data, field)
    
    for i, row in enumerate(data):
        record_anomalies = []
        
        # GC Token 고갈 체크
        if 'gc_tokens' in row and 'gc_tokens' in thresholds:
            th = thresholds['gc_tokens']
            val = row['gc_tokens']
            if val <= th.get('critical_min', 3):
                record_anomalies.append({
                    "field": "gc_tokens",
                    "severity": "CRITICAL",
                    "value": val,
                    "threshold": th.get('critical_min'),
                    "message": f"GC Token 고갈 위험! ({val} <= {th.get('critical_min')})"
                })
            elif val <= th.get('warning_min', 5):
                record_anomalies.append({
                    "field": "gc_tokens",
                    "severity": "WARNING",
                    "value": val,
                    "threshold": th.get('warning_min'),
                    "message": f"GC Token 부족 ({val} <= {th.get('warning_min')})"
                })
        
        # Buffer 포화 체크
        if 'int_write_buf' in row and 'int_write_buf' in thresholds:
            th = thresholds['int_write_buf']
            val = row['int_write_buf']
            if val >= th.get('critical_max', 58):
                record_anomalies.append({
                    "field": "int_write_buf",
                    "severity": "CRITICAL",
                    "value": val,
                    "threshold": th.get('critical_max'),
                    "message": f"Write Buffer 포화! ({val} >= {th.get('critical_max')})"
                })
            elif val >= th.get('warning_max', 50):
                record_anomalies.append({
                    "field": "int_write_buf",
                    "severity": "WARNING",
                    "value": val,
                    "threshold": th.get('warning_max'),
                    "message": f"Write Buffer 높음 ({val} >= {th.get('warning_max')})"
                })
        
        # FCore 런타임 스파이크 체크
        if 'fcore_runtime_us' in row and 'fcore_runtime_us' in thresholds:
            th = thresholds['fcore_runtime_us']
            val = row['fcore_runtime_us']
            if val >= th.get('critical_max', 900):
                record_anomalies.append({
                    "field": "fcore_runtime_us",
                    "severity": "CRITICAL",
                    "value": val,
                    "threshold": th.get('critical_max'),
                    "message": f"FCore 런타임 급증! ({val}us >= {th.get('critical_max')}us)"
                })
        
        # QCC 스파이크 체크 (시그마 기반)
        if 'qcc_count' in row and 'qcc_count' in stats_cache:
            stats = stats_cache['qcc_count']
            th = thresholds.get('qcc_count', {})
            sigma = th.get('spike_threshold_sigma', 2.0)
            
            val = row['qcc_count']
            threshold_val = stats['avg'] + (sigma * stats['stdev'])
            
            if val > threshold_val:
                record_anomalies.append({
                    "field": "qcc_count",
                    "severity": "WARNING",
                    "value": val,
                    "threshold": round(threshold_val, 2),
                    "message": f"QCC 트래픽 스파이크 ({val} > {sigma}σ = {round(threshold_val, 2)})"
                })
        
        if record_anomalies:
            anomalies.append({
                "record_index": i,
                "timestamp": row.get('timestamp_ms', 'N/A'),
                "issues": record_anomalies
            })
    
    return anomalies


def generate_report(data: List[Dict], anomalies: List[Dict], thresholds: Dict) -> str:
    """분석 리포트 생성"""
    report = []
    report.append("=" * 70)
    report.append(" TP LOG ANALYSIS REPORT")
    report.append(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 70)
    report.append("")
    
    # 1. 기본 통계
    report.append("[ BASIC STATISTICS ]")
    report.append("-" * 50)
    
    numeric_fields = [k for k in data[0].keys() if isinstance(data[0].get(k), (int, float)) and not k.startswith('_')]
    
    for field in numeric_fields[:10]:  # 상위 10개만
        stats = calculate_stats(data, field)
        if 'error' not in stats:
            report.append(f"  {field}:")
            report.append(f"    Min: {stats['min']}, Max: {stats['max']}, Avg: {stats['avg']}")
            report.append(f"    P95: {stats['p95']}, P99: {stats['p99']}, StDev: {stats['stdev']}")
            report.append("")
    
    # 2. 이상 징후 요약
    report.append("")
    report.append("[ ANOMALY SUMMARY ]")
    report.append("-" * 50)
    
    critical_count = sum(1 for a in anomalies for i in a['issues'] if i['severity'] == 'CRITICAL')
    warning_count = sum(1 for a in anomalies for i in a['issues'] if i['severity'] == 'WARNING')
    
    report.append(f"  🔴 CRITICAL: {critical_count} events")
    report.append(f"  🟡 WARNING:  {warning_count} events")
    report.append(f"  Total anomalous records: {len(anomalies)} / {len(data)}")
    report.append("")
    
    # 3. 이상 상세
    if anomalies:
        report.append("")
        report.append("[ ANOMALY DETAILS (Top 20) ]")
        report.append("-" * 50)
        
        for anomaly in anomalies[:20]:
            report.append(f"  Record #{anomaly['record_index']} (ts: {anomaly['timestamp']})")
            for issue in anomaly['issues']:
                icon = "🔴" if issue['severity'] == 'CRITICAL' else "🟡"
                report.append(f"    {icon} {issue['message']}")
            report.append("")
    
    # 4. 권장 사항
    report.append("")
    report.append("[ RECOMMENDATIONS ]")
    report.append("-" * 50)
    
    if critical_count > 0:
        report.append("  ⚠️  Critical 이슈 발견됨. 즉시 조치 필요:")
        
        # 이슈 유형별 권장사항
        issue_types = set(i['field'] for a in anomalies for i in a['issues'])
        
        if 'gc_tokens' in issue_types:
            report.append("    - GC Token 고갈: GC threshold 조정 또는 OP 비율 증가 검토")
        if 'int_write_buf' in issue_types:
            report.append("    - Buffer 포화: Buffer pool 크기 확장 또는 Host 쓰로틀링 검토")
        if 'fcore_runtime_us' in issue_types:
            report.append("    - FCore 런타임 급증: Task 스케줄링 최적화 필요")
    else:
        report.append("  ✅ Critical 이슈 없음. 정상 범위 내 동작 중.")
    
    report.append("")
    report.append("=" * 70)
    
    return "\n".join(report)


def generate_summary_json(data: List[Dict], anomalies: List[Dict]) -> Dict:
    """시각화 연동용 JSON 요약"""
    numeric_fields = [k for k in data[0].keys() if isinstance(data[0].get(k), (int, float)) and not k.startswith('_')]
    
    stats_summary = {}
    for field in numeric_fields:
        stats_summary[field] = calculate_stats(data, field)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "total_records": len(data),
        "anomaly_count": len(anomalies),
        "critical_count": sum(1 for a in anomalies for i in a['issues'] if i['severity'] == 'CRITICAL'),
        "warning_count": sum(1 for a in anomalies for i in a['issues'] if i['severity'] == 'WARNING'),
        "statistics": stats_summary,
        "anomalies": anomalies[:100],  # 상위 100개만
    }


def main():
    parser = argparse.ArgumentParser(
        description='TP Log Analyzer - CSV 데이터 자동 분석',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--input', required=True, help='분석할 CSV 파일')
    parser.add_argument('--threshold', help='임계값 설정 JSON (없으면 기본값 사용)')
    parser.add_argument('--output-report', default='cursor_analysis_report.txt', help='리포트 출력 파일')
    parser.add_argument('--output-json', default='cursor_analysis_summary.json', help='JSON 요약 출력 파일')
    
    args = parser.parse_args()
    
    # 1. 데이터 로드
    print(f"[INFO] Loading CSV: {args.input}")
    data = load_csv(args.input)
    print(f"  - Loaded {len(data)} records")
    
    # 2. 임계값 로드
    if args.threshold:
        print(f"[INFO] Loading thresholds: {args.threshold}")
        thresholds = load_threshold(args.threshold)
    else:
        print("[INFO] Using default thresholds")
        thresholds = get_default_thresholds()
    
    # 3. 이상 감지
    print("[INFO] Detecting anomalies...")
    anomalies = detect_anomalies(data, thresholds)
    print(f"  - Found {len(anomalies)} anomalous records")
    
    # 4. 리포트 생성
    report = generate_report(data, anomalies, thresholds)
    print("\n" + report)
    
    # 5. 파일 저장
    with open(args.output_report, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[INFO] Report saved: {args.output_report}")
    
    summary = generate_summary_json(data, anomalies)
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[INFO] JSON summary saved: {args.output_json}")


if __name__ == '__main__':
    main()

