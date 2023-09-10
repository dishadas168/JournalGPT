import dotenv
from pathlib import Path

config_dir = Path(__file__).parent.parent.resolve()/"config"

# load .env config
config_env = dotenv.dotenv_values(config_dir / "config.env")

openai_api_key=""
pinecone_api_key=""
pinecone_env=""
telegram_token=""
mongodb_uri = f"mongodb://mongo:{config_env['MONGODB_PORT']}"