from pydantic import BaseModel

class Config(BaseModel):
    daily_bing_default_send_time: str = "13:00"
    daily_bing_hd_image: bool = False
