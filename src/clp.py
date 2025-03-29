# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

import os
import json
import random as rnd
import numpy as np
from dotenv import load_dotenv
from uuid import uuid4
from py3dbp import Packer, Bin, Item
from domain import Execution, GeneratedClpPlan, ClpItem, Box
import openai

load_dotenv()

class GenAIClpGenerator:

    def __init__(self):
        self.client = openai.AzureOpenAI(
            api_key = os.getenv('AZURE_OPENAI_KEY'),
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_version = os.getenv('AZURE_API_VERSION')
        )

    def generate(self, execution:Execution) -> GeneratedClpPlan:
        data = ["box_id,width,height,depth"]
        for box in execution.boxes:
            data.append(",".join([str(box.id), f"{box.width:.02f}", f"{box.height:.02f}", f"{box.depth:.02f}"]))
        data = "\n".join(data)
        response = self.client.chat.completions.create(
            model=os.getenv('AZURE_DEPLOYMENT_NAME'),
            stream=True,
            messages=[{
                "role": "system",
                "content": [{
                    "type": "text",
                    "text": """
                    You are a packaging logistic expert.
                    You must provide a container loading plan ordered from left to right, bottom to top, from back to front.
                    Start organzing the biggest boxes first.
                    You may rotate the boxes provided in order to fit as many as possible into the container.
                    You MUST ensure that if a box is on top of another box, the box below covers at least 60% of the box on top.
                    You MUST ensure that boxes cannot be placed in the "AIR" or without proper support.
                    You MUST provide the position of how the box should be placed by renferencing a sample box of 1x2x3.
                        - Select 1 if the 1x3 side is to be facing front. the side 1 is at the bottom and 3 would be the height
                        - Select 2 if the 2x3 side is to be facing front. the side 2 is at the bottom and 3 would be the height
                        - Select 3 if the 3x1 side is to be facing front. the side 3 is at the bottom and 1 would be the height
                        - Select 4 if the 3x2 side is to be facing front. the side 3 is at the bottom and 2 would be the hightt
                        - Select 5 if the 2x1 side is to be facing front. the side 2 is at the bottom and 1 would be the height
                    Think of at leat 3 CLPs and select the one that fits the most boxes.
                    Take your time, do not rush to provide an answer unless is the most efficient in order to maximize the amount of boxes organizzed.

                    You MUST always provide a properly formatted JSON string.
                    DO NOT RETURN ANYTHING ELSE THAN THE JSON.
                    The JSON must contain the following attributes:
                    plan: a List of items organized.
                    left_over_boxes: a List with the IDs of the boxes unable to fit.
                    remarks: a string saying if "All boxes fitted in the container" or "N boxes did not fit in the container."
                    Where N is the total count of boxes in the left_over_boxes

                    The items have the following attributes:
                        box_id: Id of the box
                        x: the location index of the box in the X plane
                        y: the location index of the box in the Y plane
                        z: the location index of the box in the Z plane
                        p: integer from 1 to 5 on how to place the box.

                    the X, Y and Z are not meant to track the distance, but instead the index 0, 1, 2 of the boxes placed.
                    """
                }]
            },
            {
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"Generatel CLP for the following container: W={execution.container_width}, H={execution.container_height}, D={execution.container_depth} and boxes:\n{data}"
                }]
            }]
        )
        raw_json = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content is not None:
                raw_json += chunk.choices[0].delta.content
        raw_json = raw_json.replace("```json", "").replace("```", "").replace("\n", "")
        return GeneratedClpPlan(**json.loads(raw_json))



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