# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Gabriel Gutierrez Anez

from uuid import uuid4
import random as rnd
from datetime import datetime
from fastapi import APIRouter


class ApplicationController:
    
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self):
        @self.router.get("/executions", response_model=AgentsInfo)
        async def find_executions() -> AgentsInfo:
            return AgentsInfo(
                agents=[
                    AgentInfo(
                        id=uuid4(),
                        name=f"Agent Name {i}",
                        description=f"Agent Description {i}",
                        type=rnd.choice(["Consulting", "Custom"]),
                        created=datetime.now()
                    )
                    for i in range(10)
                ]
            )