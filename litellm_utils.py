from litellm import completion
from datetime import datetime
import openai
import litellm
from .print_utils import make_printv
import time

print_v = make_printv(True)

# Within the OpenAI API, messages often adopt specific roles to guide the model’s responses.
# Commonly used roles include “system,” “user,” and “assistant.”
# The “system” provides high-level instructions.
# The “user” presents queries or prompts.
# The “assistant” is the model’s response.
# By differentiating these roles, we can set the context and direct the conversation efficiently.
# See https://arize.com/blog-course/mastering-openai-api-tips-and-tricks/


class CompletionFailedException(Exception):
    pass


def get_completion(
    llm_provider: str,
    llm_model: str,
    llm_max_token: int,
    llm_temperature: float,
    user_prompt: str,
    completion_identifier: str,
    max_attempts: int = 10,
    timeout: int = 60,
    system_prompt: str = None,
):
    if llm_provider is not None:
        litellm_model = f"{llm_provider}/{llm_model}"
    else:
        litellm_model = llm_model
    messages = [{"role": "user", "content": user_prompt}]
    if system_prompt is not None:
        messages.insert(0, {"role": "system", "content": system_prompt})
    for _ in range(max_attempts):
        try:
            response = completion(
                model=litellm_model,
                messages=messages,
                max_tokens=llm_max_token,
                timeout=timeout,  # raise timeout error if call takes > 60s
                temperature=llm_temperature,
            )
            return response
        except litellm.exceptions.RateLimitError as e:
            continue
        except openai.APITimeoutError as e:
            continue
        except Exception as e:
            raise e

    raise CompletionFailedException(
        f"Failed to get completion for {completion_identifier} after {max_attempts} attempts. Exiting"
    )


if __name__ == "__main__":
    import os

    llm_provider = os.getenv("LLMUTILS_LLM_PROVIDER")
    llm_model = os.getenv("LLMUTILS_LLM_MODEL")
    llm_max_token = int(os.getenv("LLMUTILS_LLM_MAX_TOKEN"))
    llm_temperature = float(os.getenv("LLMUTILS_LLM_TEMPERATURE"))
    user_prompt = "Write a short story about a cat."
    completion_identifier = "test"
    print(
        get_completion(
            llm_provider,
            llm_model,
            llm_max_token,
            llm_temperature,
            user_prompt,
            completion_identifier,
        )
    )
