from typing import List, Optional
from models import RobotDog, DogStatus


class DogRouter:
    def assign_dog(self, dogs: List[RobotDog]) -> Optional[RobotDog]:
        """返回第一只空闲的狗，无空闲时返回 None"""
        for dog in dogs:
            if dog.status == DogStatus.IDLE:
                return dog
        return None
