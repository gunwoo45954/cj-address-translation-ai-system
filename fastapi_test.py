from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from omegaconf import OmegaConf
import argparse
from model import inference

import os

import openai
from itertools import chain
import pandas as pd

# Argument
parser = argparse.ArgumentParser()
parser.add_argument('--config','-c', type=str, default='')
args, _ = parser.parse_known_args()

conf = OmegaConf.load(f'./config/{args.config}.yaml')

# 도로명주소, Chat GPT api_key 값 할당
api_key = conf.api
chatapi_key = conf.chatgpt

os.environ["OPENAI_API_KEY"] = chatapi_key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Request JSON 형식
    # requestList : 전문 요청 List (List)
    # seq : 고유 sequence number (int)
    # requestAddress : 요청 영문주소 (CHAR)

class RequestItem(BaseModel):
    seq : int = Field(gt = 0, le = 99999999)
    requestAddress : str = Field(..., max_length=2000)

class RequestJSON(BaseModel):
    requestList: List[RequestItem] = Field(..., max_items=20000)

# Response JSON 형식
    # HEADER : 응답 성공/실패 여부(Array)
    # resultCode : S / F (CHAR)
    # resultMessage : Success, Fail Message (CHAR)
    # BODY : 번역 결과 반환 List (List)
    # resultList/seq : 고유 seq 번호(CHAR)
    # resultList/resultAddres : 번역 한글주소

class HeaderItem(BaseModel):
    RESULT_CODE : str = "S"
    RESULT_MSG : str = "Success"

class BodyItem(BaseModel):
    seq : str
    resultAddress : str

class ResponseJSON(BaseModel):
    HEADER : HeaderItem
    BODY : Optional[List[BodyItem]] = None      

class Response_fail(BaseModel):
    HEADER : HeaderItem

class CustomAPIRoute(APIRoute):
    def get_route_handler(self) -> callable:
        route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                fail_seq = None
                # 요청 데이터를 가져오거나 검증하는 로직 추가
                request_data = await request.json()
                # request_data 검증 및 처리
                if not request_data.get("requestList"):
                    return JSONResponse(content = "requestiList field is not exist.")
                
                for item in request_data.get("requestList", []):
                    if not isinstance(item.get("seq"), int) or not (1 <= item["seq"] <= 99999999) or not isinstance(item.get("requestAddress"), str) or not (1 <= len(item["requestAddress"]) <= 2000):
                        fail_seq = item.get("seq")
                        raise ValueError()
                    
                # 검증된 데이터를 기반으로 라우터 또는 미들웨어 호출
                response: Response = await route_handler(request)

            except ValueError as ex:
                response2 = Response_fail(HEADER=HeaderItem())
                response2.HEADER.RESULT_CODE = "F"
                response2.HEADER.RESULT_MSG = "seq " + str(fail_seq) + " is failed to transfer"
                return JSONResponse(content = response2.dict())

            return response
        
        return custom_route_handler

app = FastAPI()
custom_router = APIRouter(route_class = CustomAPIRoute)

@custom_router.post('/')
def create_response(item : RequestJSON):
    response = ResponseJSON(HEADER=HeaderItem())
    chunk_list = lambda lst,chunk_size : [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    # 청크로 나눠서 inference 한 후 chatgpt_result 반환
    chunk_size = 10
    input_data = [dict(i) for i in dict(item)['requestList']]
    data_chunk = chunk_list(input_data, chunk_size)
    chatgpt_result = list(chain(*[inference(api_key,{"requestList":i}) for i in data_chunk]))

    input_df = pd.DataFrame(input_data)
    result_df = pd.DataFrame(chatgpt_result)
    
    # 재시도할 횟수
    retry = 2
    for r in range(retry):
        no_answer_df =  input_df[result_df['resultAddress']=='답 없음'] # 답 없음으로 나온 결과들 다시 뽑아내기
        input_data = [{'seq':seq,'requestAddress':address} for seq,address in zip(no_answer_df['seq'],no_answer_df['requestAddress'])]
        
        data_chunk = chunk_list(input_data, chunk_size)
        chatgpt_result = list(chain(*[inference(api_key,{"requestList":i}) for i in data_chunk]))
        
        for i in chatgpt_result:
            result_df.loc[result_df['seq'] == i['seq'],'resultAddress'] = i['resultAddress']

    body_items = [BodyItem(**{'seq':str(seq),'resultAddress':address}) for seq,address in zip(result_df['seq'],result_df['resultAddress'])]
    response.BODY = body_items
    
    return response

app.include_router(custom_router)

if __name__ == "__main__":
    uvicorn.run("fastapi_test:app")