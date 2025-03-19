# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Gabriel Gutierrez Anez

from datetime import datetime
from typing import Literal, Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

AgentType = Literal['Consulting', 'Custom']

class AgentInfo(BaseModel):
    model_config = ConfigDict(extra='ignore', from_attributes=True)
    id:UUID
    name:Optional[str] = Field(default=None)
    description:Optional[str] = Field(default=None)
    type:AgentType
    created:datetime

class AgentsInfo(BaseModel):
    agents:List[AgentInfo]