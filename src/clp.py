# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

import os
import requests
import json
from dotenv import load_dotenv, find_dotenv
from domain import (
    Execution,
    GeneratedClpPlan,
    ClpItem,
    BinPackingRequest,
    BinPackingItems,
    BinPackingBin,
    BinPackingResponse,
    PackingResponse
)

load_dotenv(find_dotenv())
    
class Clp3DBinPackingGenerator:

    def generate(self, execution:Execution) -> GeneratedClpPlan:
        bins = [BinPackingBin(
            id=str(execution.id),
            w=execution.container_width,
            h=execution.container_height,
            d=execution.container_depth
        )]
        items=[
            BinPackingItems(
                id=str(b.id),
                w=b.width,
                h=b.height,
                d=b.depth
            )
            for b in execution.boxes
        ]
        request = BinPackingRequest(
            items=items,
            bins=bins
        )

        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        params = {
            "query": request.model_dump_json()
        }

        response = requests.post(os.getenv('BIN3D_PACKING_ENDPOINT'), params, headers)
        if response.status_code == 200:
            response:PackingResponse = BinPackingResponse(**json.loads(response.content)).response

            return GeneratedClpPlan(
                plan=[
                    ClpItem(
                        box_id=i.id,
                        x=i.coordinates.x1,
                        y=i.coordinates.y1,
                        z=i.coordinates.z1,
                        image=i.image_sbs
                    )
                    for b in response.bins_packed for i in b.items
                ],
                left_over_boxes=[
                    i.id for i in response.not_packed_items
                ],
                used_space=response.bins_packed[0].bin_data.used_space if len(response.bins_packed) > 0 else 0
            )