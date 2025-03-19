# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Gabriel Gutierrez Anez

from typing import Type, Any, List
from functools import wraps

def inject(dependencies: List[Type[Any]]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            objects = [dep() for dep in dependencies]
            return func(*objects, *args, **kwargs)
        return wrapper
    return decorator