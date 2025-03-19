# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Gabriel Gutierrez Anez

from controllers.organaizer
from dotenv import load_dotenv
from config.config import Settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

load_dotenv()

def enable_cors(app:FastAPI) -> FastAPI:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    return app

def configure_controllers(app:FastAPI, api_prefix="/api/v1") -> FastAPI:
    settings = Settings()
    health_controller = controllers.health.HealthController()
    agent_controller = controllers.agent.AgentController()
    
    app.include_router(health_controller.router, prefix=api_prefix)
    app.include_router(agent_controller.router, prefix=api_prefix)

    return app


def create_app() -> FastAPI:
    return configure_controllers(enable_cors(FastAPI()))

def main():
    uvicorn.run("main:create_app", host="0.0.0.0", port=5000, reload=True)

if __name__ == "__main__":
    main()