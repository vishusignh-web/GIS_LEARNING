"""Settings come from environment variables or a .env file (never hard-code secrets)."""
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Makes .env values (username, password, token URL) visible to gis_client via os.environ
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    arcgis_layer_url: str = "https://gispc06/arcgis/rest/services/Parcels/FeatureServer/0"
    arcgis_geometry_url: str = "https://gispc06/arcgis/rest/services/Utilities/Geometry/GeometryServer"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Field names are configurable so the same code works with your real layer
    id_field: str = "PARCEL_ID"
    block_field: str = "BLOCK_NO"
    zoning_field: str = "ZONING"
    out_fields: str = "PARCEL_ID,AREA,ZONING,BLOCK_NO"


settings = Settings()
