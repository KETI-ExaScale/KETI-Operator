# KETI-ExaScale HKubectl
## KETI-ExaScale HKubectl 설명
KETI-ExaScale Platform의 멀티 클러스터 Operator

Slurm과 Kubernetes 기반 명령어 처리 모듈

Developed by KETI
## 목차
[1. 필요 환경](#필요-환경)

[2. 설치 방법](#설치-방법)

[3. 설치 확인](#설치-확인)

## 필요 환경
> Kubernetes <= 1.24

> HKubectl

> KETI GPU Scheduler

## 설치 방법
    $ kubectl apply -f ketioperator.yaml
## 설치 확인
생성 확인

    $ kubectl get pods -A
    NAMESPACE     NAME                     READY   STATUS      RESTARTS      AGE
    gpu           operatortest-h6l2l       1/1     Running     0             21s

