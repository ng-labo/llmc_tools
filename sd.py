import requests, json, base64

SD_URL = "http://192.168.1.202:7860"
DEFAULT_NEGATIVE_PROMPT = (
    "low quality, worst quality, lowres, "
    "bad anatomy, bad hands, extra fingers, "
    "missing fingers, blurry, watermark, text"
)

def generate_by_stablediffution(prompt: str, negative_prompt: str="") -> str:
    try:
        config = {
            "seed": -1,
            "sampler_name": "DPM++ 2M",
            "scheduler": "Automatic",
            "batch_size": 1,
            "n_iter": 1,
            "steps": 20,
            "cfg_scale": 4,
            "width": 512,
            "height": 768,
            "send_images": True,
            "save_images": False,
            "override_settings": {
                "sd_model_checkpoint": "meinamix_meinaV11.safetensors"
            }
        }
        payload = { **config, "prompt": prompt, "negative_prompt": negative_prompt or DEFAULT_NEGATIVE_PROMPT }
        response = requests.post(url=f'{SD_URL}/sdapi/v1/txt2img', json=payload)
        r = response.json()
        open('output.png', 'wb').write(base64.b64decode(r['images'][0]))
        return {"prompt": prompt, "config": config, "result": "success"}
    except Exception as e:
        return {"error": str(e)} 

FUNCTIONS = {
    "meinamix_meinaV11": generate_by_stablediffution,
}

TOOLS = [
    {
      "type": "function",
      "function": {
        "name": "meinamix_meinaV11",
        "description": "stable-diffution(automatic1111版) apiで画像生成する。"
                       "configは内部固定、画像サイズ512x768、結果は内部で保存されユーザーアプリケーションが引き継ぐ。"
                       "処理成否のみ変えるが失敗してもリトライの必要はない。",
        "parameters": {
          "type": "object",
          "properties": {
            "prompt": {
              "type": "string",
              "description": "stable-diffution prompt"
            },
            "negative_prompt": {
              "type": "string",
              "description": "stable-diffution negative_prompt"
            }
          },
          "required": ["prompt",],
          "additionalProperties": False
        }
      }
    },
]
