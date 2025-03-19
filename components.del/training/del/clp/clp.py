# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano


from uuid import uuid4
from typing import List
from py3dbp import Packer, Bin, Item
from detection.models import Prediction, GeneratedClpPlan, Clp


class ClpPlanGenerator:

    def generate(self, width:float, height:float, depth:float, predictions:List[Prediction]) -> GeneratedClpPlan:
        plan_id = uuid4()
        packer = Packer()
        container = Bin(
            plan_id,
            width,
            height,
            depth,
            1000
        )
        packer.add_bin(container)
        for pred in predictions:
            packer.add_item(Item(pred.id, pred.dimensions.width, pred.dimensions.height, pred.dimensions.depth, 0))

        packer.pack()

        remarks = "All boxes fitted in the container."
        if container.unfitted_items is not None and len(container.unfitted_items) > 0:
            remarks = f"{len(container.unfitted_items)} boxes did not fit in the container."

        return GeneratedClpPlan(
            plan=[
                Clp(
                    execution_id=plan_id,
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