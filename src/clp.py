# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

import os
import json
from dotenv import load_dotenv
from py3dbp import Packer, Bin, Item
from domain import Execution, GeneratedClpPlan, ClpItem
import openai
from openai.types.chat.chat_completion_system_message_param import ChatCompletionSystemMessageParam
from openai.types.chat.chat_completion_content_part_text_param import ChatCompletionContentPartTextParam
from openai.types.chat.chat_completion_user_message_param import ChatCompletionUserMessageParam

load_dotenv()

class GenAIClpGenerator:

    def __init__(self):
        self.client = openai.AzureOpenAI(
            api_key = os.getenv('AZURE_OPENAI_KEY'),
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_version = os.getenv('AZURE_API_VERSION')
        )
        self.model = os.getenv('AZURE_DEPLOYMENT_NAME')
        with open("instructions.txt", "r") as f:
            self.system_message = ChatCompletionSystemMessageParam(
                role="system",
                content=[ChatCompletionContentPartTextParam(
                    type="text",
                    text=f.read()
                )]
            )

    def generate(self, execution:Execution) -> GeneratedClpPlan:
        data = ["id,width,height,depth"]
        for box in execution.boxes:
            data.append(",".join([str(box.id), f"{box.width:.02f}", f"{box.height:.02f}", f"{box.depth:.02f}"]))
        data = "\n".join(data)
        user_message = f"Generate a CLP for the following container: width={execution.container_width}, height={execution.container_height}, depth={execution.container_depth} and boxes:\n{data}"
        response = self.client.chat.completions.create(
            model=self.model,
            stream=True,
            messages=[
                self.system_message,
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[ChatCompletionContentPartTextParam(
                        type="text",
                        content=user_message
                    )]
                )
            ]
        )
        texts = [
            chunk.choices[0].delta.content for chunk in response if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content is not None
        ]
        
        return GeneratedClpPlan(**json.loads("".join(texts)))



class ClpPlanGenerator:

    def generate(self, execution:Execution) -> GeneratedClpPlan:
        packer = Packer()
        container = Bin(
            execution.id,
            execution.container_width,
            execution.container_height,
            execution.container_depth,
            1000
        )
        packer.add_bin(container)
        for box in execution.boxes:
            packer.add_item(Item(box.id, box.width, box.height, box.depth, 0))

        packer.pack()

        remarks = "All boxes fitted in the container."
        if container.unfitted_items is not None and len(container.unfitted_items) > 0:
            remarks = f"{len(container.unfitted_items)} boxes did not fit in the container."

        return GeneratedClpPlan(
            plan=[
                ClpItem(
                    box_id=i.name,
                    x=i.position[0],
                    y=i.position[1],
                    z=i.position[2]
                )
                for i in container.items
            ],
            left_over_boxes=[
                i.name for i in container.unfitted_items
            ],
            remarks=remarks
        )