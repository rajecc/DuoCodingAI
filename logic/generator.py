import os
import json
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from logic.evaluator import run_python_code

load_dotenv()

class TaskGenerationSchema(BaseModel):
    title: str
    description: str
    starter_code: str
    solution_code: str
    hints: List[str]
    test_cases: str

model = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview", 
    google_api_key=os.getenv("LLM_TOKEN"),
    temperature=0.2,
    max_retries=1
).bind(
    response_mime_type="application/json" ,
)

SYSTEM_PROMPT_TEMPLATE = """Ты — Senior разработчик и IT-наставник для школьников (12-17 лет). 
Твоя задача — создавать микро-упражнения для образовательной платформы.
КОНТЕКСТ ЗАДАЧИ:
- Уровень: {level}
- Трек: {track}
- Тема: {topic}

{track_rules}

ФОРМАТ ОТВЕТА:
Верни JSON-объект со следующими ключами: "title", "description", "starter_code", "solution_code", "hints" (массив из 3 строк), "test_cases".
"""

RULES_BACKEND = """ПРАВИЛА ДЛЯ BACKEND (PYTHON):
1. description: Бизнес-логика, без кода.
2. starter_code: Python, используй Type Hints. Внутри только `pass`.
3. solution_code: Оптимальный код функции на Python (PEP8).
4. test_cases: СТРОГО 4-5 Python `assert` выражений (например: `assert my_func(1) == 2`). Один edge-кейс обязательно. Никаких принтов.
5. hints: СТРОГО 3 штуки. 1 — наталкивает на мысль. 2 — советует инструмент. 3 — дает алгоритм."""

RULES_FRONTEND = """ПРАВИЛА ДЛЯ FRONTEND (JAVASCRIPT):
1. description: Задачи интерфейса (форматирование, парсинг, валидация). Без кода.
2. starter_code: JavaScript, ES6+. Используй стрелочные функции. Внутри оставь `// TODO`.
3. solution_code: Чистый JavaScript код.
4. test_cases: Напиши 4-5 проверок через `console.assert(func(1) === 2, 'error')`. 
5. hints: СТРОГО 3 штуки. 1 — наталкивает на мысль. 2 — советует инструмент. 3 — дает алгоритм."""


def clean_code_field(code: str, lang: str) -> str:
    """Удаляет markdown-кавычки из кода, если LLM их все же добавила."""
    return code.replace(f"```{lang}", "").replace("```", "").strip()

def generate_validated_task(track: str, topic: str, level: str, max_retries: int = 3) -> Optional[TaskGenerationSchema]:
    track_rules = RULES_BACKEND if track.lower() == "backend (python)" else RULES_FRONTEND
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_TEMPLATE),
        ("human", "Сгенерируй задачу в формате JSON")
    ])
    
    chain = prompt | model | StrOutputParser() 
    lang_tag = "python" if track.lower() == "backend (python)" else "javascript"
    
    for attempt in range(1, max_retries + 1):
        print(f"⏳ Попытка {attempt} из {max_retries}...")
        try:
            raw_json = chain.invoke({
                "track": track, 
                "topic": topic, 
                "level": level, 
                "track_rules": track_rules
            })
            
            parsed_dict = json.loads(raw_json)
            
            for key in ["starter_code", "solution_code", "test_cases"]:
                if key in parsed_dict and isinstance(parsed_dict[key], list):
                    parsed_dict[key] = "\n".join(parsed_dict[key])
            
            task = TaskGenerationSchema(**parsed_dict)
            
            task.solution_code = clean_code_field(task.solution_code, lang_tag)
            task.test_cases = clean_code_field(task.test_cases, lang_tag)
            task.starter_code = clean_code_field(task.starter_code, lang_tag)

            if track.lower() == "backend (python)":
                check_result = run_python_code(task.solution_code, task.test_cases)
                if check_result["status"] == "success" and check_result["passed"] == check_result["total"]:
                    print(f"✅ Успех на попытке {attempt}!")
                    return task
                else:
                    print(f"❌ Тесты не прошли: {check_result}")
            else:
                print(f"✅ Успех на попытке {attempt} (Frontend сгенерирован)!")
                return task
                
        except json.JSONDecodeError as e:
            print(f"⚠️ Ошибка парсинга JSON: {e}")
            continue
        except Exception as e:
            print(f"⚠️ Системная ошибка: {type(e).__name__} - {e}")
            continue
            
    return None