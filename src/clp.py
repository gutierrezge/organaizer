# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano


from py3dbp import Packer, Bin, Item
from domain import Execution, GeneratedClpPlan, ClpItem


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