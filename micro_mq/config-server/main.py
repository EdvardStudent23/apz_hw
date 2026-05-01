import uvicorn
from fastapi import FastAPI, Body

app = FastAPI()


_registry: dict = {}


@app.post("/register")
async def register(data: dict = Body(...)):
    name: str = data["name"]
    url: str  = data["url"]
    _registry.setdefault(name, [])
    if url not in _registry[name]:
        _registry[name].append(url)
    print(f"[config-server] registered  {name!r}  ->  {url}", flush=True)
    return {"status": "ok", "registered": _registry[name]}


@app.get("/services/{name}")
async def get_service(name: str):
    urls = _registry.get(name, [])
    print(f"[config-server] lookup {name!r}  ->  {urls}", flush=True)
    return {"name": name, "urls": urls}


@app.get("/services")
async def list_all():
    return _registry


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
