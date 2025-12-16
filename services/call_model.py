import json
from openai import OpenAI
from environs import Env
import re

env = Env()
env.read_env()

def call_model_for_translations(client, texts):

    system_prompt = (
        "пиши только то, что тебя просит, без дополнительных разъяснений, "
        "возвращай только сам json, без дополнительных слов и сообщений до и после самого json, "
        "мне твой ответ нужно буквально сразу в переменную вставить"
    )


    user_prompt = f'У тебя есть список с предложениями: {json.dumps(texts, ensure_ascii=False)}. ' \
                  'Сделай из него JSON, в котором ключи - сами предложения, ' \
                  'значения - перевод на русский язык с техническим соответствием с текстом. ' \
                  'Не обрывай слова, дописывай их до конца.'

    resp = client.chat.completions.create(
        model=env('MODEL_NAME'),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    )

    raw = resp.choices[0].message.content
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Ответ не является JSON-объектом.")
        return data
    except Exception:

        m = re.search(r'\{.*\}', raw, flags=re.DOTALL)
        if not m:
            raise RuntimeError("Не удалось извлечь JSON из ответа модели. Ответ:\n" + raw)
        json_str = m.group(0)

        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise ValueError
            return data
        except Exception:

            alt = json_str.replace("'", '"')
            try:
                data = json.loads(alt)
                if not isinstance(data, dict):
                    raise ValueError
                return data
            except Exception as e:
                raise RuntimeError("Не удалось распарсить JSON из ответа модели. "
                                   "Попробуй запрос повторно. raw response:\n" + raw) from e