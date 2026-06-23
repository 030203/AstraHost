import unittest

from app import chat_service

message = "深圳天气如何"
answer = chat_service.chat(message)


print(answer)