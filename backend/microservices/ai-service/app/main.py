from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field


class CodeGenRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prompt: str
    code_gen_type: str = Field(default="html", alias="codeGenType")


def success(data=None) -> dict:
    return {"code": 0, "message": "ok", "data": data}


app = FastAPI(title="python-ai-mother-ai-service", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return success({"status": "UP", "service": "ai-service"})


@app.post("/internal/ai/generate")
async def generate_code(payload: CodeGenRequest) -> dict:
    prompt = payload.prompt.strip() or "Hello Python AI Mother"
    if payload.code_gen_type == "vue_project":
        code = (
            "```file:src/App.vue\n"
            "<template><main><h1>Python AI Mother</h1><p>"
            f"{prompt[:120]}</p></main></template>\n"
            "```"
        )
    else:
        code = (
            "```html\n"
            "<!doctype html><html><head><meta charset=\"utf-8\" />"
            "<title>Python AI Mother</title></head>"
            "<body><main><h1>Python AI Mother</h1>"
            f"<p>{prompt[:240]}</p></main></body></html>\n"
            "```"
        )
    return success({"code": code, "language": "html"})
