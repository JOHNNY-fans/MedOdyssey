import json
import time
import random
import requests
import asyncio
import aiofiles
import random
from openai import AsyncOpenAI, OpenAI

MODEL_DIR_BASE = '/ailab/user/sunhongli/weights/'
HTTP_CONCURRENT_LIMIT = 32
API_CONCURRENT_LIMIT = 32
API_RETRY = 20
MAX_TOKENS = 500

# 请求openai接口时是否流式
STREAM = True

model2maxlen = {
    'gpt-4-turbo-2024-04-09': 128000,
    'gpt-4o': 128000,
    'gpt-4o-2024-05-13': 128000,
    'claude-3-haiku-20240307': 200000,
    'claude-3-sonnet-20240229': 200000,
    'claude-3-opus-20240229': 200000,
    'chatglm3-6b-128k': 128000,
    'Yarn-Mistral-7b-128k': 128000,
    'internlm2-chat-7b': 200000,
    'internlm2-chat-20b': 200000,
    'moonshot-v1-128k': 128000,
}

api_semaphore = asyncio.Semaphore(API_CONCURRENT_LIMIT)
async def openai_api(content, model_name, base_url, api_key, retry=30, stream=False):
    async with api_semaphore:
        try:
            openai_client = AsyncOpenAI(
                base_url=base_url,
                api_key=api_key,
            )
            completion = await openai_client.chat.completions.create(
                model=model_name,
                temperature=0,
                max_tokens=MAX_TOKENS,
                messages=[
                    {'role': 'user', 'content': content}
                ],
                stream=stream,
            )
            print(completion)
            if stream:
                res = []
                async for chunk in completion:
                    print(chunk)
                    if chunk.choices[0].delta.content is not None:
                        print(chunk.choices[0].delta.content)
                        res.append(chunk.choices[0].delta.content)
                res = ''.join(res)
                print(res)
            else:
                res = completion.choices[0].message.content
            
        except Exception as e:
            print(str(e))
            if retry == 0:
                print("max retry")
                raise e
            # traceback.print_exc()
            await asyncio.sleep(random.normalvariate(30, 5))
            return await openai_api(
                content=content,
                model_name=model_name,
                base_url=base_url,
                api_key=api_key,
                retry=retry-1,
                stream=stream,
            )
        
        return res

# 非异步版本
def openai_api_sync(content, model_name, base_url, api_key, retry=30, stream=False):
        try:
            openai_client = OpenAI(
                base_url=base_url,
                api_key=api_key,
            )
            completion = openai_client.chat.completions.create(
                model=model_name,
                temperature=0,
                max_tokens=MAX_TOKENS,
                messages=[
                    {'role': 'user', 'content': content}
                ],
                stream=stream,
            )
            # print(completion)
            if stream:
                res = []
                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        print(chunk.choices[0].delta.content)
                        res.append(chunk.choices[0].delta.content)
                res = ''.join(res)
                print(res)
            else:
                res = completion.choices[0].message.content
            
        except Exception as e:
            print(str(e))
            if retry == 0:
                print("max retry")
                raise e
            # traceback.print_exc()
            time.sleep(random.normalvariate(30, 5))
            return openai_api_sync(
                content=content,
                model_name=model_name,
                base_url=base_url,
                api_key=api_key,
                retry=retry-1,
                stream=stream,
            )
        
        return res

http_semaphore = asyncio.Semaphore(HTTP_CONCURRENT_LIMIT)
async def http_request(method, url, payload, headers, retry=30) -> str:
    async with http_semaphore:
        try:
            response = requests.request(method, url, headers=headers, data=payload)
            res = response.json()
        except Exception as e:
            print(str(e))
            await asyncio.sleep(30)
            if retry == 0:
                print("http request max retry")
                raise e
            return await http_request(
                url, payload, headers, retry=retry-1
            )
        return res


class TokenzierForLength:
    def __init__(self, model_name):
        self.model_name = model_name
        if 'gpt' in self.model_name:
            import tiktoken
            self.tokenizer = tiktoken.encoding_for_model(self.model_name)
        elif 'claude' in self.model_name:
            from anthropic import Anthropic
            self.tokenizer = Anthropic().get_tokenizer()
        elif 'chatglm' in self.model_name or 'Mistral' in self.model_name or 'internlm2' in self.model_name:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR_BASE + self.model_name, trust_remote_code=True)
        elif 'moonshot' in self.model_name:
            self.tokenizer = None
        else:
            raise ValueError('Unknown model name')
    
    async def get_token_len_by_api(self, text):
        if 'moonshot' in self.model_name:
            url = "https://api.moonshot.cn/v1/tokenizers/estimate-token-count"

            payload = json.dumps({
                "model": self.model_name,
                "messages": [{
                    "role": "user",
                    "content": text
                    }]
                })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer sk-J6Qp2qwhez7joRxhFva6tPHQioBVCBMv6H7HuTp5qmMxQAaU'
                }
            res = await http_request("POST", url, payload, headers, retry=API_RETRY)
            print(res)
            token_len = res['data']['total_tokens']
            return token_len
        else:
            raise ValueError('???')

    async def token_len(self, text):
        if 'moonshot' in self.model_name:
            return await self.get_token_len_by_api(text)
        else:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
    
    def encode(self, text):
        if 'gpt' in self.model_name:
            return self.tokenizer.encode(text)
        elif 'claude' in self.model_name:
            return self.tokenizer.encode(text).ids
        elif 'chatglm' in self.model_name or 'Mistral' in self.model_name or 'internlm2' in self.model_name:
            return self.tokenizer.encode(text, add_special_tokens=False).input_ids
    
    def decode(self, text):
        if 'gpt' in self.model_name:
            return self.tokenizer.decode(text)
        elif 'claude' in self.model_name:
            return self.tokenizer.decode(text)
        elif 'chatglm' in self.model_name or 'Mistral' in self.model_name or 'internlm2' in self.model_name:
            return self.tokenizer.decode(text, skip_special_tokens=True)


# save one json item to jsonl file.
lock = asyncio.Lock()
async def write2jsonl(json_data, file_name):
    async with lock:
        async with aiofiles.open(file_name, 'a', encoding='utf-8') as f:
            await f.write(json.dumps(json_data, ensure_ascii=False) + '\n')

# 非异步版本
def write2jsonl_sync(json_data, file_name):
    with open(file_name, 'a', encoding='utf-8') as f:
        f.write(json.dumps(json_data, ensure_ascii=False) + '\n')