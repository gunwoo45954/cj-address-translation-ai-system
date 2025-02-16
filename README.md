# CJ대한통운 미래기술챌린지 2023

## 프로젝트 개요
**프로젝트명** : 비정제 영문 주소 AI 번역 시스템 (23.07.03 ~ 23.08.15)

**프로젝트 내용** : 사용자가 비정제된 다양한 형식의 영문 주소를 요청 시, AI가 한국 주소 체계에 맞게 도로명주소 형태로 번역해 반환하는 시스템을 구현했습니다.

**프로젝트 결과** : 정확도 78%, 최종 3위

## 팀 역할
| 이름 | 역할 |
| :--- | :--- |
| 박준형 | Prompt 작성, Data preprocessing & postprocessing |
| 김건우 | Prompt 검수, API 설계 및 구현 |


## 배포 주소
프로젝트 기간이 지나 더 이상 주소를 운영하지 않습니다.


## Stacks

### Environment
![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-007ACC?style=for-the-badge&logo=Visual%20Studio%20Code&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=Git&logoColor=white)
![Github](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=GitHub&logoColor=white) 
![Postman](https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=Postman&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=GoogleCloud&logoColor=white)

### Development
![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-00897B?style=for-the-badge&logo=FastAPI&logoColor=white)

### Communication
![Notion](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=Notion&logoColor=white)
---


## Request & Response 형식

### Request
```
{
    "requestList": [
        {
            "seq": int,
            "requestAddress": char
        }
    ]
}
```

### Response
```
{
    "HEADER": {
        "RESULT_CODE": char,
        "RESULT_MSG": char
    },
    "BODY": [
        {
            "seq": char,
            "resultAddress": char
        }
    ]
}
```


## 주요 문제 해결 방법

### 문제 1 : 데이터 부족 문제
- **문제** : 제공받은 데이터 수가 모델에 학습시키기에는 부족했습니다.

- **해결 방법** : GPT3.5 모델을 사용한 Prompt Engineering에서 Few shot learning을 통해 적은 데이터에 대해서도 효과적으로 번역할 수 있도록 구현했습니다. 108개의 예선 데이터에 대해 정확도 100%를 보여줬습니다.

### 문제 2 : 응답 속도 문제
- **문제** : 본선 데이터 5,000개에 대해 응답 시간이 오래 걸려 제한 시간 내에 응답받을 수 없었습니다. 

- **해결 방법** : 입력 데이터를 일정 청크 단위로 나눈 뒤 Multi-processing을 사용해 응답 시간을 약 75% 단축시켰습니다. 


## Interface Definition
- **Interface Type** : HTTP RESTful
- **Method** : POST
- **Data Set** : JSON
- **Character-set** : UTF-8
- **ContentType** : application/json/x-www-form-urlencoded