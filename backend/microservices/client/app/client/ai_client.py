from app.client.base import BaseServiceClient


class AiServiceClient(BaseServiceClient):
    async def generate_code(self, prompt: str, code_gen_type: str) -> dict:
        data = await self._post_json(
            "/internal/ai/generate",
            payload={"prompt": prompt, "codeGenType": code_gen_type},
        )
        return dict(data or {})
