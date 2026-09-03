from openai import OpenAI
import os

from coach_engine.openai_config import (
    require_openai_api_key,
)


try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


DEFAULT_MODEL = "gpt-4.1-mini"


def generate_text(
    prompt,
    model=DEFAULT_MODEL,
):
    api_key = require_openai_api_key(
        os.getenv("OPENAI_API_KEY")
    )

    client = OpenAI(
        api_key=api_key
    )

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    return response.output_text