# KETI-ExaScale HKubectl
## Introduction of KETI-ExaScale HKubectl
KETI-Operator for KETI-ExaScale Platform

Developed by KETI
## Contents
[1. Requirment](#requirement)

[2. How to Install](#how-to-install)

[3. Install Check](#install-check)

[4. How to Use](#how-to-use)

## Requirement
> Kubernetes <= 1.24

> HKubectl

> KETI GPU Scheduler

## How to Install
    $ kubectl apply -f ketioperator.yaml
## Install Check
Create Check

    $ kubectl get pods -A
    NAMESPACE     NAME                     READY   STATUS      RESTARTS      AGE
    gpu           operatortest-h6l2l       1/1     Running     0             21s

