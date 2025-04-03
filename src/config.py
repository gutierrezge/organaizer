# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano


from pydantic import BaseModel, Field


class DistanceConfig(BaseModel):
    distance_factor:float = Field(default=0.75)
    to_centimeter:float = Field(default=1/10)


class DetectionConfig(BaseModel):
    confidence:float=Field(default=0.1)
    iou:float=Field(default=0.1)
    box_model:str = Field(default="../training/best.pt")
    sam_model:str = Field(default="../training/sam2_t.pt")
    mask_optimization_sigma:float = Field(default=3.5)


class CameraConfig(BaseModel):
    camera_id:int = Field(default=0)
    resolution: tuple[int, int] = Field(default=(640, 480))
    fps:int = Field(default=30)
    
    
class Config(BaseModel):
    camera:CameraConfig = Field(default=CameraConfig())
    detection:DetectionConfig = Field(default=DetectionConfig())
    distance:DistanceConfig = Field(default=DistanceConfig())