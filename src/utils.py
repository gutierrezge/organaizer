# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano


from typing import Optional
import numpy as np


def sort_values(corners:Optional[np.ndarray]) -> Optional[np.ndarray]:
    """Sorts an array of 2D points clockwise and ensures output shape (6, 2)"""
    if corners is None or len(corners) < 6:
        return None

    corners = np.unique(corners.reshape(-1, 2), axis=0)
    if len(corners) < 6:
        return None

    center = np.mean(corners, axis=0)
    angles = np.arctan2(corners[:, 1] - center[1], corners[:, 0] - center[0])
    sorted_indices = np.argsort(angles)
    corners = corners[sorted_indices]

    distances = np.linalg.norm(corners, axis=1)
    top_left_idx = np.argmin(distances)
    corners = np.roll(corners, -top_left_idx, axis=0)

    return corners[:6] 